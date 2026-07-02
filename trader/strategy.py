"""매매 전략 인터페이스 (스텁).

TODO: 실제 전략 구현. 시그널 생성만 담당하고, 주문 실행은 main 루프가 담당한다.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional

Side = Literal["buy", "sell", "hold"]


@dataclass
class Signal:
    iscd: str
    side: Side
    qty: int = 0
    price: int = 0          # 0 = 시장가
    reason: str = ""


class Strategy(ABC):
    """모든 전략의 베이스."""

    @abstractmethod
    def generate(self, iscd: str) -> Optional[Signal]:
        """종목에 대한 매매 시그널 생성. hold면 None 가능."""
        ...


class NoopStrategy(Strategy):
    """항상 관망하는 기본 전략 (스캐폴드)."""

    def generate(self, iscd: str) -> Optional[Signal]:
        # TODO: shared.services 시세/지표를 사용해 시그널 산출
        return Signal(iscd=iscd, side="hold", reason="noop")
