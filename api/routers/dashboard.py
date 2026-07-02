"""대시보드 라우터 — 잔고/포지션/수익률.

기존 shared.services.account 를 재사용해 프론트 대시보드용 통합 뷰를 제공한다.
(시세/랭킹 등 상세 엔드포인트는 기존 stock/ranking 라우터 유지)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from shared.services.account.account import get_balance

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class Position(BaseModel):
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: float
    current_price: int
    eval_amount: int
    profit_amount: int
    profit_rate: float


class DashboardSummary(BaseModel):
    deposit: int          # 예수금
    total_eval: int       # 총평가금액
    total_profit: int     # 평가손익합계
    positions: List[Position]


@router.get("/summary", response_model=DashboardSummary)
def summary():
    """잔고 요약 + 보유 포지션 + 수익률."""
    res = get_balance()
    if not res.is_success:
        raise HTTPException(status_code=502, detail=res.msg1)

    o2 = res.output2[0] if res.output2 else None
    positions = [
        Position(
            stock_code=i.pdno,
            stock_name=i.prdt_name,
            quantity=int(i.hldg_qty or 0),
            avg_price=float(i.pchs_avg_pric or 0),
            current_price=int(i.prpr or 0),
            eval_amount=int(i.evlu_amt or 0),
            profit_amount=int(i.evlu_pfls_amt or 0),
            profit_rate=float(i.evlu_pfls_rt or 0),
        )
        for i in res.output1
        if int(i.hldg_qty or 0) > 0
    ]
    return DashboardSummary(
        deposit=int(o2.dnca_tot_amt) if o2 else 0,
        total_eval=int(o2.tot_evlu_amt) if o2 else 0,
        total_profit=int(o2.evlu_pfls_smtl_amt) if o2 else 0,
        positions=positions,
    )
