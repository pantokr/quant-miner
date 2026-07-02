"""리스크 관리 (스텁).

주문 실행 전 포지션/손실 한도 등을 검사한다.
TODO: 실제 한도 로직(종목당 최대 비중, 일일 손실 한도, 최대 포지션 수 등) 구현.
"""
from dataclasses import dataclass

from trader.strategy import Signal


@dataclass
class RiskLimits:
    max_position_krw: int = 10_000_000     # 종목당 최대 평가금액
    max_daily_loss_krw: int = 1_000_000    # 일일 최대 손실
    max_positions: int = 10                # 최대 동시 보유 종목 수


class RiskManager:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def approve(self, signal: Signal) -> bool:
        """시그널을 실제 주문으로 낼지 승인. TODO: 실제 검사."""
        if signal.side == "hold":
            return False
        # TODO: 현재 잔고/포지션 조회 후 한도 검사
        return True
