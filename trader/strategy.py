"""매매 전략.

전략은 종가 시퀀스(closes)를 받아 최신 봉 시점의 액션(buy/sell/hold)을 돌려주는
`signal()` 순수 함수 중심으로 설계한다. → trader(라이브 페이퍼)와 research(백테스트)가
같은 전략을 그대로 공유한다.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Sequence

Side = Literal["buy", "sell", "hold"]


@dataclass
class Signal:
    iscd: str
    side: Side
    qty: int = 0
    price: int = 0          # 0 = 시장가
    reason: str = ""


def sma(values: Sequence[float], n: int) -> float:
    return sum(values[-n:]) / n


class Strategy(ABC):
    """모든 전략의 베이스. name/warmup을 노출하고 signal()을 구현한다."""
    name: str = "base"
    warmup: int = 0   # 판단에 필요한 최소 봉 수

    @abstractmethod
    def signal(self, closes: Sequence[float]) -> Side:
        """closes(오름차순 종가) 기준, 마지막 봉 시점의 액션."""
        ...


class MovingAverageCrossStrategy(Strategy):
    """이동평균 교차: 골든크로스=매수, 데드크로스=매도."""

    def __init__(self, short: int = 5, long: int = 20) -> None:
        if short >= long:
            raise ValueError("short < long 이어야 합니다")
        self.short = short
        self.long = long
        self.name = f"MA-Cross({short}/{long})"
        self.warmup = long + 1

    def signal(self, closes: Sequence[float]) -> Side:
        if len(closes) < self.warmup:
            return "hold"
        s_now, l_now = sma(closes, self.short), sma(closes, self.long)
        prev = closes[:-1]
        s_prev, l_prev = sma(prev, self.short), sma(prev, self.long)
        if s_prev <= l_prev and s_now > l_now:
            return "buy"    # 골든크로스
        if s_prev >= l_prev and s_now < l_now:
            return "sell"   # 데드크로스
        return "hold"


class NoopStrategy(Strategy):
    """항상 관망."""
    name = "Noop"
    warmup = 0

    def signal(self, closes: Sequence[float]) -> Side:
        return "hold"
