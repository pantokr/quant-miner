# 배포 가이드

## 개요
- **백엔드 4개(api·backend·collector·trader) + db** → Oracle Ubuntu 서버, GitHub Actions로 자동 배포
- **프론트(web/frontend)** → Vercel Git 연동으로 자동 배포
- 흐름: `git push origin main` → Actions가 SSH로 서버 접속 → `git pull` + `docker compose up -d --build`

`.env`(KIS 키·DB 비번)는 **git에 올리지 않고** 서버 로컬에만 둔다. 코드는 git, 비밀은 서버.

---

## 1. 서버 최초 세팅 (1회)

```bash
# Docker + compose 플러그인 (미설치 시)
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER      # sudo 없이 docker 실행 (재로그인 필요)

# 저장소 클론
git clone <GitHub 저장소 URL> ~/quant-miner
cd ~/quant-miner

# 환경설정 작성 (KIS/POSTGRES)
cp .env.example .env   # 없으면 직접 작성
nano .env

# 최초 기동
docker compose up -d --build
docker compose ps
```

방화벽/보안목록: **8000(backend)** 과 **22(SSH)** 만 외부 개방. 9000(게이트웨이)·5432(db)는 공개 불필요.

---

## 2. GitHub Secrets 등록

배포용 SSH 키를 만들고 공개키를 서버에 등록한다.

```bash
# 로컬에서 배포 전용 키 생성
ssh-keygen -t ed25519 -f deploy_key -N ""
# 공개키를 서버 authorized_keys에 추가
ssh-copy-id -i deploy_key.pub <user>@<server>   # 또는 수동 append
```

저장소 → Settings → Secrets and variables → Actions 에 등록:

| Secret | 값 | 필수 |
|---|---|---|
| `SSH_HOST` | 서버 IP (예: 168.107.24.190) | ✅ |
| `SSH_USER` | 접속 계정 (예: ubuntu) | ✅ |
| `SSH_KEY` | **deploy_key 개인키 전체 내용** | ✅ |
| `SSH_PORT` | SSH 포트 (기본 22면 생략) | ⬜ |
| `REMOTE_DIR` | 저장소 경로 (기본 `~/quant-miner`면 생략) | ⬜ |

---

## 3. 사용

```bash
git push origin main
```
→ [.github/workflows/deploy.yml](.github/workflows/deploy.yml) 가 실행되어 서버가 자동 갱신.
관련 경로(api/web/backend/collector/trader/shared/compose/Dockerfile)가 바뀔 때만 트리거된다.
GitHub → Actions 탭에서 "수동 실행(workflow_dispatch)"도 가능.

로그 확인:
```bash
ssh <user>@<server> "cd ~/quant-miner && docker compose logs -f backend"
```

---

## 4. 프론트(Vercel)
- Vercel 프로젝트 Settings → **Root Directory = `web/frontend`**
- Git 연동 시 push마다 자동 배포. 백엔드 주소는 [web/frontend/vercel.json](web/frontend/vercel.json) 리라이트로 지정.

---

## 대안: 수동 배포
CI 없이 즉시 반영하려면 [docker-upload.ps1](docker-upload.ps1) (로컬 빌드 → 이미지 전송 → 서버 load & 기동). 자동/수동 병행 가능.
