import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List

from shared.models.stock import (
    MinuteChartRow, OhlcvRow, CurrentPrice, OrderBookRow, InvestorRow,
)
from shared.services.chart.minute import get_minute_chart, get_minute_chart_range
from shared.services.chart.gapfill import fill_minute_gaps
from shared.services.quote.ohlcv import ensure_ohlcv_coverage, get_ohlcv_all
from shared.services.quote.current import get_current_price
from shared.services.quote.orderbook import get_orderbook
from shared.services.quote.investor import get_investor_trend
from shared.services.market.short_sell import get_short_sell
from shared.services.market.credit import get_credit
from shared.services.market.loan import get_loan_trans
# DB 조회는 모듈 상단에서 가져온다. 함수 안에서 지연 임포트하면 없는 이름을 써도
# 기동할 때는 멀쩡하고 요청이 들어와야 500이 나서, 화면에서는 "데이터가 없다"로 보인다.
from shared.db.stock_ohlcv import query_ohlcv
from shared.db.stock_investor import query_investor_trend
from shared.db.stock_short import query_short_sell, query_credit
from shared.db.stock_loan import query_loan_trans

router = APIRouter(prefix="/stock", tags=["stock"])


def _int(value, default: int = 0) -> int:
    """KIS 숫자 필드 → int.

    KIS는 값이 없는 칸을 빈 문자열로 준다 (특히 오래된 일자의 거래대금·전일대비).
    그대로 int()에 넣으면 행 하나 때문에 응답 전체가 500이 되고, 화면에는 원인 없는
    "HTTP 500"만 남는다. DB 적재 쪽(upsert_ohlcv)은 예전부터 이렇게 방어하고 있었다.
    """
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return default


def _float(value, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


@router.get("/{iscd}/minute-chart", response_model=List[MinuteChartRow])
def minute_chart(
    iscd: str,
    date: str = Query(..., examples=["20260102"],
                      description="조회 일자 'YYYYMMDD'"),
    fill: bool = Query(True, description="체결 없는 분을 직전 값으로 메워 391분을 채움"),
):
    """분봉 조회 (당일 09:00:00 ~ 15:30:00 전체 데이터)"""
    try:
        rows = get_minute_chart(iscd=iscd, date=date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return fill_minute_gaps(rows, trade_date=date) if fill else rows


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
    """기간별 OHLCV 조회 (DB 우선, 모자란 구간만 KIS 수집)"""
    # 예전에는 캐시가 "하나라도" 있으면 그대로 돌려줬다. 그래서 최근 3개월만 적재된
    # 종목을 1년으로 조회하면 3개월치만 나오고, 나머지는 영영 채워지지 않았다.
    # 이제는 요청 구간과 DB 커버리지를 비교해 빠진 구간만 받아 온다.
    try:
        ensure_ohlcv_coverage(iscd=iscd, start_date=start,
                              end_date=end, period=period, save=save)
    except RuntimeError as e:
        # 수집에 실패해도 DB에 있는 만큼은 보여 준다 — 빈 화면보다 낫다
        logging.warning(f"[{iscd}] OHLCV 결손 수집 실패: {e}")

    cached = query_ohlcv(iscd, period, start, end)

    if not cached:
        raise HTTPException(status_code=404, detail="데이터 없음")

    try:
        return [
            OhlcvRow(
                date=str(r["date"]),
                open=int(r["open"] or 0), high=int(r["high"] or 0),
                low=int(r["low"] or 0), close=int(r["close"] or 0),
                volume=int(r["volume"] or 0), amount=int(r["amount"] or 0),
                change_sign=str(r["change_sign"] or ""), change_val=int(r["change_val"] or 0),
            )
            for r in cached
        ]
    except Exception as e:
        import logging
        logging.error(f"OhlcvRow 변환 오류: {e}, data: {cached[:1]}")
        raise HTTPException(status_code=500, detail=f"데이터 변환 오류: {e}")


@router.get("/{iscd}/ohlcv/all", response_model=List[OhlcvRow])
def ohlcv_all(
    iscd: str,
    start: str = Query("19900101", description="수집 시작일 YYYYMMDD"),
    period: str = Query("D", description="D:일 W:주 M:월 Y:년"),
    save: bool = Query(True, description="DB 저장 여부"),
):
    """전 기간 OHLCV 수집 (페이지네이션 자동 처리, 시간 소요 있음)"""
    try:
        items = get_ohlcv_all(iscd=iscd, start_date=start,
                              period=period, save=save)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    if not items:
        raise HTTPException(status_code=404, detail="데이터 없음")
    return [
        OhlcvRow(
            date=i.stck_bsop_date,
            open=_int(i.stck_oprc), high=_int(i.stck_hgpr),
            low=_int(i.stck_lwpr), close=_int(i.stck_clpr),
            volume=_int(i.acml_vol), amount=_int(i.acml_tr_pbmn),
            change_sign=i.prdy_vrss_sign, change_val=_int(i.prdy_vrss),
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
        current=_int(p.stck_prpr),
        open=_int(p.stck_oprc), high=_int(p.stck_hgpr), low=_int(p.stck_lwpr),
        change_val=_int(p.prdy_vrss),
        change_rate=_float(p.prdy_ctrt),
        volume=_int(p.acml_vol),
        market_cap=_int(p.hts_avls),
        per=_float(p.per),
        pbr=_float(p.pbr),
        foreign_ratio=_float(p.hts_frgn_ehrt),
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
    use_cache: bool = Query(True, description="DB 캐시 사용 여부"),
):
    """투자자별 매매동향 (모의환경에서는 빈 배열)"""
    if use_cache:
        cached = query_investor_trend(iscd)
        if cached:
            return cached

    items = get_investor_trend(iscd, save=save)

    def n(value) -> int:
        # 장중 미집계 행은 빈 문자열로 온다
        try:
            return int(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            return 0

    res = [
        InvestorRow(
            date=i.stck_bsop_date,
            individual_net=n(i.prsn_ntby_qty),
            foreign_net=n(i.frgn_ntby_qty),
            institution_net=n(i.orgn_ntby_qty),
        )
        for i in items
    ]
    # API 결과가 있고 캐시를 안 썼다면 (혹은 강제 갱신이면) 결과 반환
    return res


@router.get("/{iscd}/short-sell")
def short_sell(
    iscd: str,
    start: str = Query(..., examples=["20260102"]),
    end:   str = Query(..., examples=["20260113"]),
    save: bool = Query(True),
):
    """공매도 현황 (DB 우선, 없으면 KIS 수집)"""
    cached = query_short_sell(iscd, start, end)
    if not cached:
        get_short_sell(iscd, start, end, save=save)
        cached = query_short_sell(iscd, start, end)
    return {"count": len(cached), "data": cached}


@router.get("/{iscd}/credit")
def credit(
    iscd: str,
    start: str = Query(..., examples=["20260102"]),
    end:   str = Query(..., examples=["20260113"]),
    save: bool = Query(True),
):
    """신용잔고 (DB 우선, 없으면 KIS 수집)"""
    cached = query_credit(iscd, start, end)
    if not cached:
        get_credit(iscd, start, end, save=save)
        cached = query_credit(iscd, start, end)
    return {"count": len(cached), "data": cached}


@router.get("/{iscd}/loan-trans")
def loan_trans(
    iscd: str,
    start: str = Query(..., examples=["20260102"]),
    end:   str = Query(..., examples=["20260803"]),
    save: bool = Query(True),
):
    """대차거래추이 — 대차잔고는 공매도 선행지표 (DB 우선, 없으면 KIS 수집)"""
    cached = query_loan_trans(iscd, start, end)
    if not cached:
        get_loan_trans(iscd, start, end, save=save)
        cached = query_loan_trans(iscd, start, end)
    return {"count": len(cached), "data": cached}
