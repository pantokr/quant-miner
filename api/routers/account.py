from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from shared.models.account import BalanceSummary, BalanceItem, BalanceResult, CcldItem
from shared.kis_auth import get_valid_token
from shared.services.account.account import get_balance, get_daily_ccld

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/balance", response_model=BalanceResult)
def balance():
    """주식 잔고 조회"""
    res = get_balance()
    if not res.is_success:
        raise HTTPException(status_code=502, detail=res.msg1)

    o2 = res.output2[0] if res.output2 else None
    summary = BalanceSummary(
        deposit=int(o2.dnca_tot_amt) if o2 else 0,
        total_eval=int(o2.tot_evlu_amt) if o2 else 0,
        total_profit=int(o2.evlu_pfls_smtl_amt) if o2 else 0,
    )
    stocks = [
        BalanceItem(
            stock_code=item.pdno,
            stock_name=item.prdt_name,
            quantity=int(item.hldg_qty),
            avg_price=float(item.pchs_avg_pric),
            current_price=int(item.prpr),
            profit_rate=float(item.evlu_pfls_rt),
        )
        for item in res.output1
        if int(item.hldg_qty) > 0
    ]
    return BalanceResult(summary=summary, stocks=stocks)


@router.get("/daily-ccld", response_model=List[CcldItem])
def daily_ccld(
    start_dt: Optional[str] = Query(
        None, examples=["20260102"], description="시작일 YYYYMMDD (기본: 오늘)"),
    end_dt:   Optional[str] = Query(
        None, examples=["20260102"], description="종료일 YYYYMMDD (기본: 오늘)"),
):
    """주식 일별 주문체결 조회"""
    token = get_valid_token()
    if not token:
        raise HTTPException(status_code=502, detail="KIS 토큰 발급 실패")

    res = get_daily_ccld(start_dt=start_dt, end_dt=end_dt, access_token=token)
    if not res.is_success:
        raise HTTPException(status_code=502, detail=res.msg1)

    return [
        CcldItem(
            order_no=item.odno,
            stock_code=item.pdno,
            stock_name=item.prdt_name,
            side=item.sll_buy_dvsn_cd_name,
            order_qty=int(item.ord_qty),
            filled_qty=int(item.tot_ccld_qty),
            avg_price=float(item.avg_prvs or 0),
            total_amount=int(item.tot_ccld_amt),
        )
        for item in res.output1
    ]
