"""저장 데이터 라우터 (DB 우선).

과거/저장 데이터(분봉·OHLCV·투자자추이)는 DB에서 조회한다.
DB에 없으면 api 게이트웨이를 중계 호출(게이트웨이가 KIS에서 받아 적재)한다.
프론트가 쓰는 경로를 그대로 노출한다.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import List

from shared.models.stock.schema import MinuteChartRow, OhlcvRow, InvestorRow
from shared.db.stock_minute import query_minute_range
from shared.db.stock_ohlcv import get_ohlcv_coverage, query_ohlcv
from shared.db.stock_investor import query_investor_trend
from shared.services.chart.gapfill import expected_last_minute, fill_minute_gaps
from shared.services.quote.coverage import missing_ranges
from web.backend.gateway import proxy_get

router = APIRouter(tags=["market-data (DB)"])

MARKET_OPEN = "090000"
MARKET_CLOSE = "153000"


@router.get("/stock/{iscd}/minute-chart", response_model=List[MinuteChartRow])
def minute_chart(
    iscd: str,
    date: str = Query(..., examples=["20260102"]),
    fill: bool = Query(True, description="체결 없는 분을 직전 값으로 메워 빈 시간대를 채움"),
):
    """
    일일 분봉 (대시보드 차트용).

    DB를 먼저 보되 "지금 있어야 할 시각까지" 들어와 있는지 확인한다. 예전에는
    DB에 몇 봉이라도 있으면 그대로 돌려줘서, 11시까지만 적재된 종목은 15시에
    조회해도 11시 이후가 비어 그래프가 중간에 끊겼다.
    """
    rows = query_minute_range(iscd, date, MARKET_OPEN, date, MARKET_CLOSE)
    want_last = expected_last_minute(date)

    have_last = str(rows[-1]["trade_time"]) if rows else ""
    stale = bool(want_last) and have_last < want_last

    if stale:
        # 게이트웨이가 KIS에서 최신까지 수집·적재한 뒤 돌려준다
        fresh = proxy_get(f"/stock/{iscd}/minute-chart", {"date": date, "fill": fill})
        if fresh:
            return fresh
        # 게이트웨이도 못 가져오면(휴장 등) DB에 있는 만큼이라도 보여 준다
        if not rows:
            return []

    return fill_minute_gaps(rows, trade_date=date) if fill else rows


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
    """
    기간별 OHLCV.

    DB에 뭐라도 있으면 그대로 돌려주던 예전 방식은, 최근 몇 달만 적재된 종목을
    1년으로 조회했을 때 짧은 표를 주고 끝냈다. 요청 구간을 DB가 실제로 덮고 있는지
    보고, 모자라면 게이트웨이가 결손분을 수집·적재한 결과를 받아 온다.
    """
    rows = query_ohlcv(iscd, period, start, end)
    min_date, max_date, count = get_ohlcv_coverage(iscd, period, start, end)

    if missing_ranges(start, end, min_date, max_date, count):
        try:
            fresh = proxy_get(
                f"/stock/{iscd}/ohlcv",
                {"start": start, "end": end, "period": period, "save": save},
            )
        except HTTPException:
            # 게이트웨이가 죽었거나 KIS에도 없는 구간 — DB에 있는 만큼은 보여 준다
            if rows:
                return rows
            raise
        if fresh:
            return fresh

    return rows


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
