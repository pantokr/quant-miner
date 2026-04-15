"""라우터 응답 스키마 (클라이언트에게 반환하는 API 응답 형태)"""
from pydantic import BaseModel
from typing import List


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
