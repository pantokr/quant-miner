"""계좌 도메인 라우터 응답 스키마"""
from pydantic import BaseModel
from typing import List


class BalanceSummary(BaseModel):
    deposit: int        # 예수금총액
    total_eval: int     # 총평가금액
    total_profit: int   # 평가손익합계


class BalanceItem(BaseModel):
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: float
    current_price: int
    profit_rate: float


class BalanceResult(BaseModel):
    summary: BalanceSummary
    stocks: List[BalanceItem]


class CcldItem(BaseModel):
    order_no: str
    stock_code: str
    stock_name: str
    side: str           # 매수 / 매도
    order_qty: int
    filled_qty: int
    avg_price: float
    total_amount: int
