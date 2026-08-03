"""웹 백엔드 (배포 단위: web/backend).

프론트엔드가 호출하는 유일한 서버. 저장 데이터는 DB에서 조회하고, 실시간 데이터는
api 게이트웨이를 중계한다. KIS를 직접 호출하지 않는다.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web.backend.routers import market_data, live, dashboard, logs, ml, finance, master, account

app = FastAPI(
    title="Quant Miner Web Backend",
    description="프론트 서빙 — DB 조회 + api 게이트웨이 중계",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(master.router)       # 종목 검색 (DB 전용) — /stock/{iscd}/* 보다 먼저
app.include_router(market_data.router)  # DB 우선
app.include_router(live.router)         # 실시간 → api 중계
app.include_router(dashboard.router)
app.include_router(logs.router)
app.include_router(ml.router)          # 설정 주도 가격예측(비동기 잡)
app.include_router(finance.router)     # 재무/기업정보 → api 중계
app.include_router(account.router)     # 잔고/주문체결 → api 중계


@app.on_event("startup")
def startup():
    from shared.db.ml_model import create_table
    from shared.db.stock_master import create_table as create_master_table
    create_table()          # 모델 레지스트리 테이블 보장
    create_master_table()   # 종목 마스터 테이블 보장


@app.get("/health")
def health():
    return {"status": "ok"}
