"""저장 데이터 라우터 (DB 우선).

과거/저장 데이터(분봉·OHLCV·투자자추이)는 DB에서 조회한다.
DB에 없으면 api 게이트웨이를 중계 호출(게이트웨이가 KIS에서 받아 적재)한다.
프론트가 쓰는 경로를 그대로 노출한다.
"""
from datetime import datetime
from fastapi import APIRouter, Query
from typing import List

from shared.models.stock.schema import MinuteChartRow, OhlcvRow, InvestorRow
from shared.db.stock_minute import query_minute_range
from shared.db.stock_ohlcv import query_ohlcv
from shared.db.stock_investor import query_investor_trend
from web.backend.gateway import proxy_get

router = APIRouter(tags=["market-data (DB)"])

MARKET_OPEN = "090000"
MARKET_CLOSE = "153000"


@router.get("/stock/{iscd}/minute-chart", response_model=List[MinuteChartRow])
def minute_chart(iscd: str, date: str = Query(..., examples=["20260102"])):
    rows = query_minute_range(iscd, date, MARKET_OPEN, date, MARKET_CLOSE)
    if rows:
        return rows
    return proxy_get(f"/stock/{iscd}/minute-chart", {"date": date})


@router.get("/stock/{iscd}/minute-chart/range", response_model=List[MinuteChartRow])
def minute_chart_range(
    iscd: str,
    start: str = Query(..., examples=["20260102"]),
    end: str = Query(..., examples=["20260131"]),
):
    """기간 분봉: DB 우선, 없으면 게이트웨이(수집·적재) 중계."""
    rows = query_minute_range(iscd, start, MARKET_OPEN, end, MARKET_CLOSE)
    if rows:
        return rows
    return proxy_get(f"/stock/{iscd}/minute-chart/range", {"start": start, "end": end})


@router.get("/stock/{iscd}/ohlcv", response_model=List[OhlcvRow])
def ohlcv(
    iscd: str,
    start: str = Query(...),
    end: str = Query(...),
    period: str = Query("D"),
    save: bool = Query(True),
):
    rows = query_ohlcv(iscd, period, start, end)
    if rows:
        return rows
    return proxy_get(
        f"/stock/{iscd}/ohlcv",
        {"start": start, "end": end, "period": period, "save": save},
    )


@router.get("/stock/{iscd}/ohlcv/all", response_model=List[OhlcvRow])
def ohlcv_all(
    iscd: str,
    start: str = Query("19900101"),
    period: str = Query("D"),
    save: bool = Query(True),
):
    today = datetime.today().strftime("%Y%m%d")
    rows = query_ohlcv(iscd, period, start, today)
    if rows:
        return rows
    return proxy_get(
        f"/stock/{iscd}/ohlcv/all",
        {"start": start, "period": period, "save": save},
    )


@router.get("/stock/{iscd}/investor", response_model=List[InvestorRow])
def investor(iscd: str, save: bool = Query(True)):
    rows = query_investor_trend(iscd)
    if rows:
        return rows
    return proxy_get(f"/stock/{iscd}/investor", {"save": save})
