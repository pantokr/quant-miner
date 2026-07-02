<#
도커 이미지 빌드 → tar 저장 → 원격 Ubuntu 서버로 업로드 → load & 기동.

로컬(Windows/Docker Desktop)에서 실행. OpenSSH(ssh/scp)가 필요합니다.

사용:
  .\docker-upload.ps1
  .\docker-upload.ps1 -Server 158.180.79.14 -User ubuntu
  .\docker-upload.ps1 -SshKey C:\keys\oracle.pem
  .\docker-upload.ps1 -SkipBuild        # 이미 빌드된 이미지 재사용
  .\docker-upload.ps1 -NoUp             # 업로드/load만, 기동은 수동

전제:
  - docker-compose.yml 에 image: quant-miner-<svc>:latest 태그가 있어야 함(빌드시 그 이름으로 태깅).
  - 서버에 docker / docker compose 설치돼 있어야 함.
  - 로컬에 .env 존재(서버로 함께 전송).
#>
param(
    [string]$Server = "158.180.79.14",
    [string]$User = "ubuntu",
    [string]$RemoteDir = "quant-miner",       # 서버 홈 기준 상대경로
    [string]$SshKey = "",                       # 예: C:\keys\oracle.pem (없으면 기본 키/에이전트)
    [switch]$SkipBuild,
    [switch]$NoUp
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

$images = @(
    "quant-miner-api:latest",
    "quant-miner-backend:latest",
    "quant-miner-collector:latest",
    "quant-miner-trader:latest"
)
$tar = Join-Path $root "quant-images.tar"
$target = "$User@$Server"

# ssh/scp 공통 옵션
$sshOpts = @()
if ($SshKey) {
    if (-not (Test-Path $SshKey)) { Write-Error "SSH 키를 찾을 수 없습니다: $SshKey"; exit 1 }
    $sshOpts += @("-i", $SshKey)
}

if (-not (Test-Path (Join-Path $root ".env"))) {
    Write-Error ".env 가 없습니다. 서버로 전송할 환경설정이 필요합니다."; exit 1
}

# 1) 빌드 -------------------------------------------------------------
if (-not $SkipBuild) {
    Write-Host "[1/5] docker compose build..." -ForegroundColor Cyan
    & docker compose build
    if ($LASTEXITCODE -ne 0) { Write-Error "빌드 실패"; exit 1 }
} else {
    Write-Host "[1/5] 빌드 건너뜀(-SkipBuild)" -ForegroundColor DarkGray
}

# 2) 이미지 저장 ------------------------------------------------------
Write-Host "[2/5] docker save -> $tar ..." -ForegroundColor Cyan
& docker save -o $tar @images
if ($LASTEXITCODE -ne 0) { Write-Error "docker save 실패(이미지 이름 확인: $($images -join ', '))"; exit 1 }
$sizeMB = [math]::Round((Get-Item $tar).Length / 1MB, 1)
Write-Host "     저장 완료: $sizeMB MB" -ForegroundColor DarkGray

# 3) 원격 디렉터리 준비 -----------------------------------------------
Write-Host "[3/5] 원격 디렉터리 준비: $target : ~/$RemoteDir" -ForegroundColor Cyan
& ssh @sshOpts $target "mkdir -p ~/$RemoteDir"
if ($LASTEXITCODE -ne 0) { Write-Error "SSH 연결/디렉터리 생성 실패"; exit 1 }

# 4) 전송 (이미지 tar + prod compose + .env) --------------------------
Write-Host "[4/5] 전송(scp)..." -ForegroundColor Cyan
& scp @sshOpts $tar "${target}:~/$RemoteDir/quant-images.tar"
if ($LASTEXITCODE -ne 0) { Write-Error "이미지 전송 실패"; exit 1 }
& scp @sshOpts (Join-Path $root "docker-compose.prod.yml") "${target}:~/$RemoteDir/docker-compose.prod.yml"
& scp @sshOpts (Join-Path $root ".env") "${target}:~/$RemoteDir/.env"
Write-Host "     전송 완료" -ForegroundColor DarkGray

# 5) 원격 load & 기동 -------------------------------------------------
Write-Host "[5/5] 원격 load & 기동..." -ForegroundColor Cyan
$remote = "cd ~/$RemoteDir && docker load -i quant-images.tar"
if (-not $NoUp) {
    $remote += " && docker compose -f docker-compose.prod.yml up -d && docker compose -f docker-compose.prod.yml ps"
}
& ssh @sshOpts $target $remote
if ($LASTEXITCODE -ne 0) { Write-Error "원격 load/기동 실패"; exit 1 }

Write-Host ""
Write-Host "완료." -ForegroundColor Green
Write-Host "  서버 백엔드 : http://${Server}:8000/health"
Write-Host "  로그 확인   : ssh $target 'cd ~/$RemoteDir && docker compose -f docker-compose.prod.yml logs -f backend'"
if ($NoUp) {
    Write-Host "  (기동 생략됨) 서버에서: docker compose -f docker-compose.prod.yml up -d" -ForegroundColor DarkGray
}
