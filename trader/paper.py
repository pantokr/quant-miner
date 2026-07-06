"""페이퍼(모의) 브로커 — 실제 주문 없이 가상 체결로 포지션/손익을 추적.

trader가 실주문 대신 이걸 사용한다. 실주문 전환 시에는 kis_client_trader로 교체.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Position:
    qty: int = 0
    avg_price: float = 0.0


@dataclass
class Fill:
    iscd: str
    side: str        # buy / sell
    qty: int
    price: float


class PaperBroker:
    def __init__(self, cash: float) -> None:
        self.initial_cash = cash
        self.cash = cash
        self.positions: Dict[str, Position] = {}
        self.fills: List[Fill] = []
        self.realized_pnl = 0.0

    def position(self, iscd: str) -> Position:
        return self.positions.get(iscd, Position())

    def held_count(self) -> int:
        return sum(1 for p in self.positions.values() if p.qty > 0)

    def buy(self, iscd: str, qty: int, price: float) -> Optional[Fill]:
        cost = qty * price
        if qty <= 0 or cost > self.cash:
            return None
        p = self.positions.setdefault(iscd, Position())
        p.avg_price = (p.avg_price * p.qty + cost) / (p.qty + qty)
        p.qty += qty
        self.cash -= cost
        f = Fill(iscd, "buy", qty, price)
        self.fills.append(f)
        return f

    def sell(self, iscd: str, qty: int, price: float) -> Optional[Fill]:
        p = self.positions.get(iscd)
        if not p or p.qty <= 0:
            return None
        qty = min(qty, p.qty)
        self.realized_pnl += (price - p.avg_price) * qty
        p.qty -= qty
        self.cash += qty * price
        if p.qty == 0:
            p.avg_price = 0.0
        f = Fill(iscd, "sell", qty, price)
        self.fills.append(f)
        return f

    def equity(self, prices: Dict[str, float]) -> float:
        """현금 + 보유 평가금액(현재가 prices 기준)."""
        market = sum(
            p.qty * prices.get(iscd, p.avg_price)
            for iscd, p in self.positions.items()
        )
        return self.cash + market
