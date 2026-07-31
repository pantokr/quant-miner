"""KIS 게이트웨이 (배포 단위: api).

KIS OpenAPI 호출을 전담하는 HTTP 서비스. web/backend 및 (필요 시) collector/trader가
이 서비스를 통해 KIS 데이터를 얻는다. 웹 전용 관심사(dashboard/logs/auth)는 web/backend 소관.
"""
import logging

import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from shared.db.stock_minute import create_table as create_minute_table
from shared.db.stock_ohlcv import create_table as create_ohlcv_table
from shared.db.stock_investor import create_table as create_investor_table
from shared.db.stock_short import create_tables as create_short_tables
from shared.db.token_store import create_table as create_token_table
from shared.db.stock_finance import create_table as create_finance_table
from shared.db.stock_info import create_tables as create_info_tables
from shared.db.stock_holiday import create_table as create_holiday_table
from api.routers import stock, account, ranking, finance

app = FastAPI(
    title="Quant Miner KIS Gateway",
    description="KIS OpenAPI 호출 전담 게이트웨이",
    version="0.3.0",
)

# CORS — 내부 서비스(backend/collector/trader)에서 호출. 필요 시 제한.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stock.router)
app.include_router(account.router)
app.include_router(ranking.router)
app.include_router(finance.router)


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


@app.exception_handler(requests.RequestException)
def kis_upstream_error(request: Request, exc: requests.RequestException):
    """
    KIS 쪽 오류를 502로 바꿔 내보낸다.

    이전에는 서비스가 res.raise_for_status()로 던진 예외가 그대로 새어 나가
    "500 Internal Server Error"만 남았다. 우리 코드가 터진 것처럼 보여서
    원인(예: 토큰 만료 EGW00123)을 로그에서 파헤쳐야 했다.
    """
    body = ""
    if exc.response is not None:
        body = exc.response.text[:300]
    logging.error("KIS 호출 실패 %s — %s", request.url.path, body or exc)
    return JSONResponse(
        status_code=502,
        content={"detail": f"KIS 응답 오류: {body or exc}"},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
