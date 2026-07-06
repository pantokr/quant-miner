"""리스크 관리 — 주문 실행 전 한도 검사 + 매수 수량 산정.

페이퍼 브로커(trader.paper.PaperBroker)의 포지션/현금을 기준으로 판단한다.
"""
from dataclasses import dataclass

from trader.paper import PaperBroker


@dataclass
class RiskLimits:
    order_krw: int = 1_000_000        # 1회 매수 금액
    max_position_krw: int = 10_000_000  # 종목당 최대 평가금액
    max_positions: int = 10           # 최대 동시 보유 종목 수


class RiskManager:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def size_for(self, price: float) -> int:
        """1회 매수 금액 한도 내 매수 수량."""
        if price <= 0:
            return 0
        return int(self.limits.order_krw // price)

    def approve_buy(self, broker: PaperBroker, iscd: str, price: float, qty: int) -> bool:
        if qty <= 0 or price <= 0:
            return False
        pos = broker.position(iscd)
        # 종목당 최대 평가금액
        if (pos.qty + qty) * price > self.limits.max_position_krw:
            return False
        # 최대 보유 종목 수 (신규 종목 진입 시에만 카운트)
        if pos.qty == 0 and broker.held_count() >= self.limits.max_positions:
            return False
        # 현금 한도
        if qty * price > broker.cash:
            return False
        return True
