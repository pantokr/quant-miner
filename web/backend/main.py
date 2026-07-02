"""웹 백엔드 (배포 단위: web/backend).

프론트엔드가 호출하는 유일한 서버. 저장 데이터는 DB에서 조회하고, 실시간 데이터는
api 게이트웨이를 중계한다. KIS를 직접 호출하지 않는다.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web.backend.routers import market_data, live, dashboard, logs

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

app.include_router(market_data.router)  # DB 우선
app.include_router(live.router)         # 실시간 → api 중계
app.include_router(dashboard.router)
app.include_router(logs.router)


@app.get("/health")
def health():
    return {"status": "ok"}
