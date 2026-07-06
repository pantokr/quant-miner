"""단순 백테스트 엔진.

종가 시퀀스에 전략(trader.strategy.Strategy)을 적용해 성과를 계산한다.
규칙(프로토타입): 매수 시그널→전량 매수(현금 소진), 매도 시그널→전량 매도.
"""
from dataclasses import dataclass, field
from typing import List, Sequence

from trader.strategy import Strategy


@dataclass
class BacktestResult:
    strategy: str
    initial_cash: float
    final_equity: float
    return_pct: float
    buy_hold_pct: float
    mdd_pct: float
    n_trades: int
    win_rate_pct: float
    equity_curve: List[float] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"전략: {self.strategy}\n"
            f"  초기자본   : {self.initial_cash:,.0f}\n"
            f"  최종평가   : {self.final_equity:,.0f}\n"
            f"  수익률     : {self.return_pct:+.2f}%\n"
            f"  Buy&Hold   : {self.buy_hold_pct:+.2f}%\n"
            f"  MDD        : {self.mdd_pct:.2f}%\n"
            f"  매매횟수   : {self.n_trades} (승률 {self.win_rate_pct:.1f}%)"
        )


def run_backtest(
    closes: Sequence[float],
    strategy: Strategy,
    initial_cash: float = 10_000_000,
) -> BacktestResult:
    cash = initial_cash
    qty = 0
    avg = 0.0
    equity_curve: List[float] = []
    n_trades = 0
    wins = 0

    for i in range(len(closes)):
        price = closes[i]
        side = strategy.signal(closes[: i + 1])

        if side == "buy" and qty == 0 and price > 0:
            qty = int(cash // price)
            if qty > 0:
                cash -= qty * price
                avg = price
        elif side == "sell" and qty > 0:
            pnl = (price - avg) * qty
            cash += qty * price
            n_trades += 1
            wins += 1 if pnl > 0 else 0
            qty = 0
            avg = 0.0

        equity_curve.append(cash + qty * price)

    final = equity_curve[-1] if equity_curve else initial_cash

    # MDD
    peak = float("-inf")
    mdd = 0.0
    for e in equity_curve:
        peak = max(peak, e)
        if peak > 0:
            mdd = max(mdd, (peak - e) / peak)

    ret = (final - initial_cash) / initial_cash * 100
    bh = ((closes[-1] - closes[0]) / closes[0] * 100) if closes and closes[0] > 0 else 0.0
    win_rate = (wins / n_trades * 100) if n_trades else 0.0

    return BacktestResult(
        strategy=strategy.name,
        initial_cash=initial_cash,
        final_equity=final,
        return_pct=ret,
        buy_hold_pct=bh,
        mdd_pct=mdd * 100,
        n_trades=n_trades,
        win_rate_pct=win_rate,
        equity_curve=equity_curve,
    )
