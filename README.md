# quant-miner

한국투자증권(KIS) OpenAPI 기반 **주식 데이터 수집 · 트레이딩 · 웹 대시보드** 모노레포.

시세/재무 데이터를 수집해 PostgreSQL에 적재하고, 웹에서 조회하며, 트레이딩까지 확장하는
퀀트 데이터 파이프라인입니다. 4개의 독립 배포 단위로 구성됩니다.

---

## 목적

- **수집**: KIS OpenAPI로 분봉·일봉(OHLCV)·투자자·재무 등 데이터를 자동 수집 → DB 적재
- **서빙**: 웹 프론트에 저장 데이터(DB) + 실시간 데이터(현재가/랭킹/잔고)를 제공
- **트레이딩**: 전략 기반 자동매매 (스캐폴드 단계)
- **연구**: 설정 주도 가격예측 ML (predict — web/backend ml 라우터가 재사용)

---

## 아키텍처

```
                    ┌────────────────────────────┐
  브라우저  ─────▶  │  web/frontend (Next.js)     │  Vercel · :3000
                    └──────────────┬─────────────┘
                                   │ /api/proxy
                    ┌──────────────▼─────────────┐
                    │  web/backend (FastAPI)      │  :8000  ← 프론트는 여기만 호출
                    │  · 저장 데이터 → DB 직접 조회 │
                    │  · 실시간 → api 게이트웨이 중계│
                    └───────┬───────────────┬─────┘
              DB 조회       │               │  실시간 중계
                    ┌───────▼──────┐  ┌─────▼──────────────┐
                    │  PostgreSQL  │  │  api (FastAPI)      │  :9000 (내부 전용)
                    │              │  │  KIS 호출 전담 게이트웨이 │
                    └───────▲──────┘  └─────┬──────────────┘
                            │  적재          │  KIS OpenAPI
              ┌─────────────┴───┐     ┌──────▼───────┐
              │  collector       │     │  KIS 서버     │
              │  KIS→DB 수집     │     └──────────────┘
              └──────────────────┘
              ┌──────────────────┐
              │  trader (스캐폴드) │  전략/리스크/주문
              └──────────────────┘
```

- **api** — KIS OpenAPI 호출 전담 게이트웨이. backend·collector·trader가 KIS 데이터를 얻는 통로.
- **web/backend** — 프론트가 호출하는 유일한 서버. KIS를 **직접 호출하지 않고** 저장 데이터는 DB, 실시간은 api 중계.
- **web/frontend** — Next.js 대시보드 (Vercel 배포).
- **collector** — 대상 종목의 분봉/OHLCV를 주기 수집해 DB 적재.
- **trader** — 전략→리스크검사→주문 루프 (현재 뼈대).
- **shared** — 인증·설정·DB모델·DTO·KIS 호출 로직 공통 모듈.

### 데이터 흐름
```
저장 데이터  : frontend → web/backend → PostgreSQL
실시간 데이터: frontend → web/backend → api 게이트웨이 → KIS
수집         : collector → api 로직(shared.services) → KIS → PostgreSQL
```

---

## 기술 스택

| 영역 | 스택 |
|---|---|
| 백엔드 | Python 3.12, FastAPI, uvicorn, pydantic 2, requests |
| DB | PostgreSQL 17, psycopg2(데이터 접근), SQLAlchemy(스키마 정의 소스) |
| 프론트 | Next.js 16, React 19, Chakra UI, recharts |
| 인프라 | Docker / docker compose, GitHub Actions(CD), Vercel(프론트) |

---

## 디렉터리 구조

```
quant-miner/
├── api/                 KIS 게이트웨이 (FastAPI) · uvicorn api.main:app
│   ├── main.py · routers/{stock,account,ranking,finance}
│   ├── Dockerfile · requirements.txt
├── web/
│   ├── frontend/        Next.js (Vercel)
│   └── backend/         웹서버 · uvicorn web.backend.main:app
│       ├── main.py · gateway.py
│       ├── routers/{market_data(DB), live(중계), dashboard, logs}
│       ├── auth.py(JWT 스텁) · Dockerfile · requirements.txt
├── collector/           수집기 · python -m collector.main
│   └── main.py · gap_filler.py · kis_client_collector.py
├── trader/              트레이더(스캐폴드) · python -m trader.main
│   └── main.py · strategy.py · risk_manager.py · kis_client_trader.py
├── shared/              공통 코드 (모든 유닛이 import)
│   ├── config.py        환경변수 중앙화
│   ├── kis_auth.py      KIS 토큰 발급/캐시
│   ├── db_models.py     SQLAlchemy 스키마 단일 소스
│   ├── models/          KIS 요청/응답 DTO
│   ├── db/              psycopg2 연결 + upsert/query
│   └── services/        KIS 호출 로직 (quote/chart/market/finance/account)
├── research/            가격예측 ML (predict — web/backend ml 라우터가 재사용)
├── db/                  schema.sql · migrations/
├── scripts/             수집/점검 CLI
├── docker-compose.yml       로컬/서버 빌드용 (db·api·backend·collector·trader)
├── docker-compose.prod.yml  서버 image-only 기동용
├── local-test.ps1           로컬 서버 일괄 실행
├── docker-upload.ps1        빌드→전송→원격 기동 (수동 배포)
└── DEPLOY.md                배포 가이드
```

---

## 로컬 실행

`.env` 작성 후 (아래 참고), PowerShell에서:

```powershell
.\local-test.ps1            # 게이트웨이(9000)+백엔드(8000)+프론트(3000) 새 창 3개
.\local-test.ps1 -NoFrontend
```

수동 실행:
```powershell
# ① 게이트웨이
venv\Scripts\uvicorn api.main:app --port 9000 --reload
# ② 백엔드 (게이트웨이 지정)
$env:KIS_GATEWAY_URL="http://localhost:9000"; venv\Scripts\uvicorn web.backend.main:app --port 8000 --reload
# ③ 프론트
cd web\frontend; npm install; npm run dev
```

수집기 단발 실행:
```powershell
venv\Scripts\python -m collector.main --iscd 005930 --start 20260101
```

또는 docker compose:
```powershell
docker compose up -d db api backend
```

### 포트
| 서비스 | 포트 |
|---|---|
| web/frontend | 3000 |
| web/backend | 8000 |
| api 게이트웨이 | 9000 (내부 전용) |
| PostgreSQL | 5432 |

---

## 환경변수 (`.env`, git 미포함)

```
# KIS OpenAPI
KIS_APP_KEY=...
KIS_APP_SECRET=...
KIS_ENV=demo            # demo(모의) | real(실전)
KIS_CANO=...            # 계좌번호 앞 8자리
KIS_ACNT_PRDT_CD=01

# PostgreSQL
POSTGRES_HOST=db        # docker compose db 사용 시 'db', 외부 DB면 해당 주소
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=panto
POSTGRES_PASSWORD=...
```
KIS 토큰은 `kis_token` 테이블에 캐시되어 컨테이너 재시작에도 유지됩니다.

---

## DB 스키마

스키마 정본은 [shared/db_models.py](shared/db_models.py)(SQLAlchemy)이며, [db/schema.sql](db/schema.sql)은
거기서 생성된 DDL 스냅샷입니다. 주요 테이블: `stock_minute_chart`, `stock_ohlcv`,
`stock_investor_trend`, `stock_short_sell`, `stock_credit`, `stock_finance`,
`stock_info`, `stock_dividend`, `stock_estimate`, `stock_holiday`, `kis_token`.

> 데이터 접근(upsert/query)은 현재 psycopg2(`shared/db/*.py`) 유지, SQLAlchemy는 스키마 소스 용도.

---

## 배포

- **백엔드(api·backend·collector·trader·db)** → Oracle Ubuntu 서버, **GitHub Actions**로 자동 배포
  (main push → SSH → `git pull && docker compose up -d --build`). [.github/workflows/deploy.yml](.github/workflows/deploy.yml)
- **프론트** → Vercel Git 연동 자동 배포 (Root Directory = `web/frontend`)
- **수동 배포** → [docker-upload.ps1](docker-upload.ps1) (로컬 빌드 → 이미지 전송 → 서버 load & 기동)

상세 절차는 [DEPLOY.md](DEPLOY.md) 참고.

---

## 주요 엔드포인트 (web/backend, 프론트 호출용)

| 경로 | 소스 |
|---|---|
| `GET /stock/{iscd}/minute-chart?date=` | DB (없으면 게이트웨이) |
| `GET /stock/{iscd}/ohlcv?start=&end=&period=` | DB |
| `GET /stock/{iscd}/investor` | DB |
| `GET /stock/{iscd}/current` · `/orderbook` | api 중계(실시간) |
| `GET /account/balance` · `/daily-ccld` | api 중계(실시간) |
| `GET /ranking/{fluctuation,volume,foreign,institution}` | api 중계(실시간) |
| `GET /dashboard/summary` · `/logs` | 대시보드/로그 |
