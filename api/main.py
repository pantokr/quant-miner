from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.db.stock_minute import create_table as create_minute_table
from shared.db.stock_ohlcv import create_table as create_ohlcv_table
from shared.db.stock_investor import create_table as create_investor_table
from shared.db.stock_short import create_tables as create_short_tables
from shared.db.token_store import create_table as create_token_table
from shared.db.stock_finance import create_table as create_finance_table
from shared.db.stock_info import create_tables as create_info_tables
from shared.db.stock_holiday import create_table as create_holiday_table
from api.routers import stock, account, ranking
from api.routers import finance, dashboard, logs

app = FastAPI(
    title="Quant Miner API",
    description="KIS OpenAPI 기반 주식 데이터 수집/조회 서버",
    version="0.2.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실운영시에는 특정 도메인으로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/test")
def test():
    return {"message": "top level test"}


app.include_router(stock.router)
app.include_router(account.router)
app.include_router(ranking.router)
app.include_router(finance.router)
app.include_router(dashboard.router)
app.include_router(logs.router)


@app.on_event("startup")
def startup():
    create_token_table()
    create_minute_table()
    create_ohlcv_table()
    create_investor_table()
    create_short_tables()
    create_finance_table()
    create_info_tables()
    create_holiday_table()


@app.get("/health")
def health():
    return {"status": "ok"}
