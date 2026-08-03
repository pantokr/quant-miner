from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List, Optional

from shared.models.stock import (
    FinancePeriodRow, StockInfoRow, HolidayRow, DividendRow, EstimateRow,
)
from shared.services.finance.fundamental import get_finance, get_finance_from_db
from shared.services.finance.info import (
    get_stock_info_api, get_stock_info_db,
    fetch_holidays, get_trade_days_db,
    get_dividend, get_dividend_db,
    get_estimate_perform, get_estimate_db,
)

router = APIRouter(prefix="/finance", tags=["finance"])

_FINANCE_TYPES = [
    "balance_sheet",
    "income_statement",
    "financial_ratio",
    "profit_ratio",
    "stability_ratio",
    "growth_ratio",
]


# ── 종목기본정보 ───────────────────────────────────────────

@router.get("/{iscd}/info/basic", response_model=Dict[str, Any])
def stock_basic_info(
    iscd: str,
    prdt_type_cd: str = Query(
        "300", description="300:주식/ETF/ETN/ELW  302:채권  306:ELS"),
    save: bool = Query(True),
    from_db: bool = Query(False),
):
    """주식기본정보 조회 (종목명, 상장일, 시가총액규모, ISIN 등)"""
    if from_db:
        data = get_stock_info_db(iscd)
        if not data:
            raise HTTPException(status_code=404, detail="DB에 데이터 없음")
        return data

    # 주식기본조회(CTPF1002R)는 모의투자 도메인에서 500을 반환한다.
    # 예외가 그대로 새어 나가면 클라이언트가 원인을 알 수 없으므로 502로 감싼다.
    try:
        data = get_stock_info_api(iscd, prdt_type_cd=prdt_type_cd, save=save)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"KIS 주식기본조회 실패: {e}")
    if not data:
        raise HTTPException(status_code=502, detail="KIS API 응답 없음")
    return data


# ── 영업일 ────────────────────────────────────────────────

@router.get("/market/holidays", response_model=List[HolidayRow])
def market_holidays(
    bass_dt: str = Query(..., description="기준일자 YYYYMMDD"),
    save: bool = Query(True),
):
    """영업일/휴장일 조회 및 DB 적재"""
    try:
        rows = fetch_holidays(bass_dt, save=save)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if not rows:
        raise HTTPException(status_code=404, detail="데이터 없음")
    return [
        HolidayRow(
            date=r.get("bass_dt", ""),
            is_open=r.get("opnd_yn", "N") == "Y",
            is_trade_day=r.get("tr_day_yn", "N") == "Y",
            weekday=r.get("wday_dvsn_cd", ""),
        )
        for r in rows
    ]


@router.get("/market/trade-days", response_model=List[str])
def trade_days(
    start: str = Query(..., description="시작일 YYYYMMDD"),
    end: str = Query(..., description="종료일 YYYYMMDD"),
):
    """DB에서 거래일 목록 조회"""
    return get_trade_days_db(start, end)


# ── 배당금 ────────────────────────────────────────────────

@router.get("/{iscd}/dividend", response_model=List[DividendRow])
def dividend(
    iscd: str,
    start: str = Query(..., description="시작일 YYYYMMDD"),
    end: str = Query(..., description="종료일 YYYYMMDD"),
    save: bool = Query(True),
    from_db: bool = Query(False),
):
    """배당금 조회 (DB 우선, 없으면 KIS 수집)"""
    # 1. DB 먼저 조회 (전체 이력 캐시 구조라 기간 필터 없이 가져와서 메모리 필터)
    rows = get_dividend_db(iscd)

    def within(d: str) -> bool:
        return start <= d.replace("-", "") <= end

    cached = [r for r in rows if within(r["record_date"])]

    # 2. 데이터 부족 시 KIS 수집
    if not cached and not from_db:
        get_dividend(iscd, start, end, save=save)
        rows = get_dividend_db(iscd)
        cached = [r for r in rows if within(r["record_date"])]

    if not cached:
        raise HTTPException(status_code=404, detail="배당 데이터 없음")

    return [
        DividendRow(
            stock_code=r["stock_code"],
            record_date=str(r["record_date"]),
            amount_per_share=str(r.get("amount_per_share", "")),
            dividend_type=str(r.get("dividend_type", "")),
            pay_date=str(r.get("pay_date") or ""),
        )
        for r in cached
    ]


# ── 추정실적 ───────────────────────────────────────────────

_ESTIMATE_FIELDS = (
    "revenue", "revenue_growth", "operating_profit", "op_growth",
    "net_income", "net_growth", "ebitda", "eps", "eps_growth",
    "per", "pbr", "roe", "debt_ratio",
)


def _estimate_row(iscd: str, r: Dict[str, Any]) -> "EstimateRow":
    return EstimateRow(
        stock_code=iscd,
        period=r.get("stac_yymm", ""),
        period_label=r.get("period_label", ""),
        is_estimate=bool(r.get("is_estimate")),
        analyst=r.get("analyst"),
        opinion=r.get("opinion"),
        **{k: r.get(k) for k in _ESTIMATE_FIELDS},
    )


@router.get("/{iscd}/estimate", response_model=List[EstimateRow])
def estimate_perform(
    iscd: str,
    save: bool = Query(True),
    from_db: bool = Query(False),
):
    """추정실적 조회 (컨센서스 — 확정 실적 + 추정치)"""
    if from_db:
        return [_estimate_row(iscd, r.get("data", {})) for r in get_estimate_db(iscd)]

    rows = get_estimate_perform(iscd, save=save)
    if not rows:
        raise HTTPException(status_code=404, detail="추정실적 데이터 없음")
    return [_estimate_row(iscd, r) for r in rows]


# ── 재무 데이터 ────────────────────────────────────────────
# ⚠ 경로가 `/{iscd}/{finance_type}` 로 넓어 위의 구체적 경로(dividend·estimate·
#   market/*)를 모두 먹어버린다. FastAPI는 선언 순서대로 매칭하므로 반드시 맨 끝에 둘 것.

@router.get("/{iscd}/{finance_type}", response_model=List[FinancePeriodRow])
def get_finance_data(
    iscd: str,
    finance_type: str,
    period_type: str = Query("A", description="A:연간 Q:분기"),
    save: bool = Query(True, description="DB 저장 여부"),
    from_db: bool = Query(False, description="True 시 API 호출 없이 DB에서만 반환"),
):
    """
    재무 데이터 조회 및 DB 적재

    finance_type: balance_sheet | income_statement | financial_ratio |
                  profit_ratio | stability_ratio | growth_ratio
    """
    if finance_type not in _FINANCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"유효하지 않은 finance_type. 가능한 값: {_FINANCE_TYPES}",
        )

    if from_db:
        rows = get_finance_from_db(iscd, finance_type, period_type)
        return [
            FinancePeriodRow(
                stock_code=r["stock_code"],
                period_type=r["period_type"],
                period=r["period"],
                data=r["data"],
            )
            for r in rows
        ]

    try:
        rows = get_finance(iscd, finance_type, period_type, save=save)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not rows:
        raise HTTPException(status_code=404, detail="데이터 없음")

    return [
        FinancePeriodRow(
            stock_code=iscd,
            period_type=period_type,
            period=r.get("stac_yymm", ""),
            data=r,
        )
        for r in rows
    ]
