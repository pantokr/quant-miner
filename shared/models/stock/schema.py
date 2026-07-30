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
    # 체결이 없어 KIS가 봉을 주지 않은 분을 직전 값으로 메운 행 (DB에는 없는 값)
    is_filled: bool = False


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


class StockMasterRow(BaseModel):
    """종목 마스터 행 (코드 ↔ 종목명 검색용)"""
    stock_code: str
    name: str
    market: str                 # KOSPI | KOSDAQ
    isin: Optional[str] = None


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
    """추정실적 한 기간. 확정 실적과 추정치가 함께 온다(is_estimate로 구분)."""
    stock_code: str
    period: str                             # 결산년월 YYYYMM
    period_label: str = ""                  # 원본 표기 ("2026.12E")
    is_estimate: bool = False
    analyst: Optional[str] = None
    opinion: Optional[str] = None

    revenue: Optional[float] = None          # 매출액 (억원)
    revenue_growth: Optional[float] = None    # 매출액 증감률 (%)
    operating_profit: Optional[float] = None  # 영업이익 (억원)
    op_growth: Optional[float] = None         # 영업이익 증감률 (%)
    net_income: Optional[float] = None        # 당기순이익 (억원)
    net_growth: Optional[float] = None        # 순이익 증감률 (%)
    ebitda: Optional[float] = None            # EBITDA (억원)
    eps: Optional[float] = None               # EPS (원)
    eps_growth: Optional[float] = None        # EPS 증감률 (%)
    per: Optional[float] = None               # PER (배)
    pbr: Optional[float] = None               # PBR (배)
    roe: Optional[float] = None               # ROE (%)
    debt_ratio: Optional[float] = None        # 부채비율 (%)
