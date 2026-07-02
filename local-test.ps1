<#
로컬 개발 서버 실행 스크립트

기본: 게이트웨이(api,9000) + 백엔드(web/backend,8000) + 프론트(web/frontend,3000)를 각각 새 창에서 실행.
  -NoFrontend : 프론트 제외 (백엔드 스택만)
  -NoReload   : uvicorn --reload 끄기

사용:
  .\local-test.ps1
  .\local-test.ps1 -NoFrontend
  .\local-test.ps1 -NoReload

데이터 흐름: frontend(3000) -> web/backend(8000) -> api 게이트웨이(9000) -> KIS
#>
param(
    [switch]$NoFrontend,
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$root = $PSScriptRoot
$uvicorn = Join-Path $root "venv\Scripts\uvicorn.exe"
$reload = if ($NoReload) { "" } else { "--reload" }

if (-not (Test-Path $uvicorn)) {
    Write-Error "uvicorn을 찾을 수 없습니다: $uvicorn`nvenv 설치 확인 (pip install -r api\requirements.txt)."
    exit 1
}
if (-not (Test-Path (Join-Path $root ".env"))) {
    Write-Warning ".env 파일이 없습니다. KIS 키/POSTGRES 설정이 필요합니다."
}

function Start-Server([string]$title, [string]$command) {
    $prefix = "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; `$host.UI.RawUI.WindowTitle='$title';"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "$prefix $command" | Out-Null
    Write-Host "  > $title" -ForegroundColor Green
}

Write-Host "로컬 서버 기동..." -ForegroundColor Cyan

# 1) KIS 게이트웨이 (9000)
Start-Server "api-gateway:9000" `
    "cd '$root'; & '$uvicorn' api.main:app --port 9000 $reload"

# 2) 웹 백엔드 (8000) — 게이트웨이(9000)를 가리킴
Start-Server "web-backend:8000" `
    "cd '$root'; `$env:KIS_GATEWAY_URL='http://localhost:9000'; & '$uvicorn' web.backend.main:app --port 8000 $reload"

# 3) 프론트 (3000) — 기본 포함, -NoFrontend로 제외
if (-not $NoFrontend) {
    Start-Server "frontend:3000" `
        "cd '$root\web\frontend'; npm run dev"
}

Write-Host ""
Write-Host "기동 완료. 각 창에서 로그 확인, Ctrl+C로 종료." -ForegroundColor Cyan
Write-Host "  게이트웨이 : http://localhost:9000/health"
Write-Host "  백엔드     : http://localhost:8000/health"
if (-not $NoFrontend) { Write-Host "  프론트     : http://localhost:3000  (기동에 수 초 소요)" }
Write-Host ""
Write-Host "점검 예시:" -ForegroundColor DarkGray
Write-Host '  curl "http://localhost:8000/stock/005930/current"' -ForegroundColor DarkGray
