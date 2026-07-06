from fastapi import APIRouter, HTTPException, Query
from typing import List

from shared.models.stock import (
    MinuteChartRow, OhlcvRow, CurrentPrice, OrderBookRow, InvestorRow,
)
from shared.services.chart.minute import get_minute_chart, get_minute_chart_range
from shared.services.quote.ohlcv import get_period_ohlcv, get_ohlcv_all
from shared.services.quote.current import get_current_price
from shared.services.quote.orderbook import get_orderbook
from shared.services.quote.investor import get_investor_trend
from shared.services.market.short_sell import get_short_sell
from shared.services.market.credit import get_credit

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/{iscd}/minute-chart", response_model=List[MinuteChartRow])
def minute_chart(
    iscd: str,
    date: str = Query(..., examples=["20260102"],
                      description="조회 일자 'YYYYMMDD'"),
):
    """분봉 조회 (당일 09:00:00 ~ 15:30:00 전체 데이터)"""
    try:
        rows = get_minute_chart(iscd=iscd, date=date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return rows


@router.get("/{iscd}/minute-chart/range", response_model=List[MinuteChartRow])
def minute_chart_range(
    iscd: str,
    start: str = Query(..., examples=["20260102"], description="시작일 YYYYMMDD"),
    end: str = Query(..., examples=["20260131"], description="종료일 YYYYMMDD"),
):
    """기간 분봉 전체 조회 (DB 캐시 우선, 없으면 FHKST03010230 수집·적재)."""
    if start > end:
        raise HTTPException(status_code=400, detail="start는 end보다 앞서야 합니다")
    try:
        return get_minute_chart_range(iscd=iscd, start_date=start, end_date=end)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{iscd}/ohlcv", response_model=List[OhlcvRow])
def period_ohlcv(
    iscd: str,
    start: str = Query(..., examples=["20260101"], description="시작일 YYYYMMDD"),
    end:   str = Query(..., examples=["20260113"], description="종료일 YYYYMMDD"),
    period: str = Query("D", description="D:일 W:주 M:월 Y:년"),
    save: bool = Query(True, description="DB 저장 여부"),
):
    """기간별 OHLCV 조회 (save=true 시 DB 적재)"""
    items = get_period_ohlcv(iscd=iscd, start_date=start,
                             end_date=end, period=period, save=save)
    if not items:
        raise HTTPException(status_code=404, detail="데이터 없음")
    return [
        OhlcvRow(
            date=i.stck_bsop_date,
            open=int(i.stck_oprc), high=int(i.stck_hgpr),
            low=int(i.stck_lwpr), close=int(i.stck_clpr),
            volume=int(i.acml_vol), amount=int(i.acml_tr_pbmn),
            change_sign=i.prdy_vrss_sign, change_val=int(i.prdy_vrss),
        )
        for i in items
    ]


@router.get("/{iscd}/ohlcv/all", response_model=List[OhlcvRow])
def ohlcv_all(
    iscd: str,
    start: str = Query("19900101", description="수집 시작일 YYYYMMDD"),
    period: str = Query("D", description="D:일 W:주 M:월 Y:년"),
    save: bool = Query(True, description="DB 저장 여부"),
):
    """전 기간 OHLCV 수집 (페이지네이션 자동 처리, 시간 소요 있음)"""
    items = get_ohlcv_all(iscd=iscd, start_date=start, period=period, save=save)
    if not items:
        raise HTTPException(status_code=404, detail="데이터 없음")
    return [
        OhlcvRow(
            date=i.stck_bsop_date,
            open=int(i.stck_oprc), high=int(i.stck_hgpr),
            low=int(i.stck_lwpr), close=int(i.stck_clpr),
            volume=int(i.acml_vol), amount=int(i.acml_tr_pbmn),
            change_sign=i.prdy_vrss_sign, change_val=int(i.prdy_vrss),
        )
        for i in items
    ]


@router.get("/{iscd}/current", response_model=CurrentPrice)
def current_price(iscd: str):
    """현재가 스냅샷"""
    try:
        p = get_current_price(iscd)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return CurrentPrice(
        current=int(p.stck_prpr),
        open=int(p.stck_oprc), high=int(p.stck_hgpr), low=int(p.stck_lwpr),
        change_val=int(p.prdy_vrss),
        change_rate=float(p.prdy_ctrt),
        volume=int(p.acml_vol),
        market_cap=int(p.hts_avls),
        per=float(p.per or 0),
        pbr=float(p.pbr or 0),
        foreign_ratio=float(p.hts_frgn_ehrt or 0),
    )


@router.get("/{iscd}/orderbook", response_model=OrderBookRow)
def orderbook(iscd: str):
    """호가/예상체결"""
    ob = get_orderbook(iscd)
    return OrderBookRow(
        ask_prices=ob.ask_prices, bid_prices=ob.bid_prices,
        ask_quantities=ob.ask_quantities, bid_quantities=ob.bid_quantities,
        total_ask_qty=ob.total_ask_qty, total_bid_qty=ob.total_bid_qty,
        expected_price=ob.expected_price,
    )


@router.get("/{iscd}/investor", response_model=List[InvestorRow])
def investor_trend(
    iscd: str,
    save: bool = Query(True, description="DB 저장 여부"),
):
    """투자자별 매매동향 (모의환경에서는 빈 배열)"""
    items = get_investor_trend(iscd, save=save)
    return [
        InvestorRow(
            date=i.stck_bsop_date,
            individual_net=int(i.prsn_ntby_qty),
            foreign_net=int(i.frgn_ntby_qty),
            institution_net=int(i.orgn_ntby_qty),
        )
        for i in items
    ]


@router.get("/{iscd}/short-sell")
def short_sell(
    iscd: str,
    start: str = Query(..., examples=["20260102"]),
    end:   str = Query(..., examples=["20260113"]),
    save: bool = Query(True),
):
    """공매도 현황 (실전투자 환경 필요)"""
    items = get_short_sell(iscd, start, end, save=save)
    return {"count": len(items), "data": [i.model_dump() for i in items]}


@router.get("/{iscd}/credit")
def credit(
    iscd: str,
    start: str = Query(..., examples=["20260102"]),
    end:   str = Query(..., examples=["20260113"]),
    save: bool = Query(True),
):
    """신용잔고 (실전투자 환경 필요)"""
    items = get_credit(iscd, start, end, save=save)
    return {"count": len(items), "data": [i.model_dump() for i in items]}
