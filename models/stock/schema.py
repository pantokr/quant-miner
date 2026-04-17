"""라우터 응답 스키마 (클라이언트에게 반환하는 API 응답 형태)"""
from pydantic import BaseModel
from typing import Any, Dict, List, Optional


# ── 분봉 ──────────────────────────────────────────────────

class MinuteChartRow(BaseModel):
    stock_code: str
    trade_date: str
    trade_time: str
    open_price: int
    high_price: int
    low_price: int
    close_price: int
    volume: int
    cumul_amount: int


# ── 시세 ──────────────────────────────────────────────────

class OhlcvRow(BaseModel):
    date: str
    open: int
    high: int
    low: int
    close: int
    volume: int
    amount: int
    change_sign: str
    change_val: int


class CurrentPrice(BaseModel):
    current: int
    open: int
    high: int
    low: int
    change_val: int
    change_rate: float
    volume: int
    market_cap: int
    per: float
    pbr: float
    foreign_ratio: float


class OrderBookRow(BaseModel):
    ask_prices: List[int]
    bid_prices: List[int]
    ask_quantities: List[int]
    bid_quantities: List[int]
    total_ask_qty: int
    total_bid_qty: int
    expected_price: str


class InvestorRow(BaseModel):
    date: str
    individual_net: int
    foreign_net: int
    institution_net: int


# ── 순위 ──────────────────────────────────────────────────

class RankRow(BaseModel):
    rank: int
    stock_code: str
    stock_name: str
    price: int
    change_rate: float


class FluctuationRankRow(RankRow):
    volume: int
    trade_value: int


class VolumeRankRow(RankRow):
    volume: int
    trade_value: int


class NetBuyRankRow(RankRow):
    net_buy_qty: int
    net_buy_amount: int


# ── 재무/기업정보 ──────────────────────────────────────────

class FinancePeriodRow(BaseModel):
    """재무 기간별 데이터 행 (재무상태표/손익계산서/비율 공통)"""
    stock_code: str
    period_type: str            # "A" 연간 / "Q" 분기
    period: str                 # 결산년월 YYYYMM
    data: Dict[str, Any]        # 원본 KIS 응답 필드 전체


class StockInfoRow(BaseModel):
    stock_code: str
    name: str
    market: str
    sector: str
    listed_shares: Optional[int] = None
    listed_date: Optional[str] = None
    isin: Optional[str] = None
    settlement_month: Optional[str] = None


class HolidayRow(BaseModel):
    date: str                   # YYYYMMDD
    is_open: bool               # 개장 여부
    is_trade_day: bool          # 거래일 여부
    weekday: str                # 요일코드


class DividendRow(BaseModel):
    stock_code: str
    record_date: str
    amount_per_share: str
    dividend_type: str
    pay_date: Optional[str] = None


class EstimateRow(BaseModel):
    stock_code: str
    period: str                 # 결산년월
    revenue: Optional[str] = None
    operating_profit: Optional[str] = None
    net_income: Optional[str] = None
    eps: Optional[str] = None
