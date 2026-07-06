"""트레이딩 오케스트레이터 (배포 단위: trader) — 페이퍼 모드.

DB의 일봉 종가로 전략 시그널을 만들고, 리스크 검사 후 페이퍼 브로커로 가상 체결한다.
실제 주문은 내지 않는다(안전). 실주문 전환은 별도 작업(kis_client_trader).

실행:
    python -m trader.main --iscd 005930 000660
    python -m trader.main --iscd 005930 --short 5 --long 20 --loop --interval 60
"""
import os
import time
import argparse
import logging
from datetime import datetime, timedelta
from typing import List

from shared.db.stock_ohlcv import query_ohlcv
from trader.strategy import MovingAverageCrossStrategy, Strategy
from trader.paper import PaperBroker
from trader.risk_manager import RiskManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("trader")


def _target_stocks(cli_iscd) -> List[str]:
    if cli_iscd:
        return cli_iscd
    env = os.getenv("TRADE_STOCKS", "")
    return [s.strip() for s in env.split(",") if s.strip()] or ["005930"]


def load_closes(iscd: str, days: int = 200) -> List[float]:
    """DB에서 최근 일봉 종가(오름차순)를 로드."""
    end = datetime.today()
    start = end - timedelta(days=days)
    rows = query_ohlcv(iscd, "D", start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
    return [float(r["close"]) for r in rows if r.get("close") is not None]


def run_once(stocks: List[str], strategy: Strategy, risk: RiskManager, broker: PaperBroker) -> None:
    prices = {}
    for iscd in stocks:
        closes = load_closes(iscd)
        if len(closes) < strategy.warmup:
            logger.info(f"[{iscd}] 데이터 부족({len(closes)}<{strategy.warmup}) — 관망 (collector 먼저 실행)")
            continue
        price = closes[-1]
        prices[iscd] = price
        side = strategy.signal(closes)

        if side == "buy":
            qty = risk.size_for(price)
            if risk.approve_buy(broker, iscd, price, qty):
                broker.buy(iscd, qty, price)
                logger.info(f"[{iscd}] BUY  {qty}주 @ {price:,.0f} ({strategy.name})")
            else:
                logger.info(f"[{iscd}] BUY 시그널이나 리스크 한도로 스킵")
        elif side == "sell":
            pos = broker.position(iscd)
            if pos.qty > 0:
                broker.sell(iscd, pos.qty, price)
                logger.info(f"[{iscd}] SELL {pos.qty}주 @ {price:,.0f} ({strategy.name})")
            else:
                logger.info(f"[{iscd}] SELL 시그널이나 보유 없음 — 스킵")
        else:
            logger.info(f"[{iscd}] 관망 @ {price:,.0f}")

    equity = broker.equity(prices)
    ret = (equity - broker.initial_cash) / broker.initial_cash * 100
    logger.info(
        f"[포트폴리오] 현금 {broker.cash:,.0f} · 평가 {equity:,.0f} "
        f"· 실현손익 {broker.realized_pnl:,.0f} · 수익률 {ret:+.2f}% · 보유 {broker.held_count()}종목"
    )


def main() -> None:
    p = argparse.ArgumentParser(description="트레이더 (페이퍼 모드)")
    p.add_argument("--iscd", nargs="+")
    p.add_argument("--cash", type=int, default=int(os.getenv("TRADE_CASH", "10000000")))
    p.add_argument("--short", type=int, default=5)
    p.add_argument("--long", type=int, default=20)
    p.add_argument("--loop", action="store_true")
    p.add_argument("--interval", type=int, default=int(os.getenv("TRADE_INTERVAL", "60")))
    args = p.parse_args()

    stocks = _target_stocks(args.iscd)
    strategy = MovingAverageCrossStrategy(args.short, args.long)
    risk = RiskManager()
    broker = PaperBroker(cash=args.cash)
    logger.info(f"트레이더 시작 [페이퍼] 전략={strategy.name} 초기현금={args.cash:,} 대상={stocks}")

    if not args.loop:
        run_once(stocks, strategy, risk, broker)
        return
    while True:
        run_once(stocks, strategy, risk, broker)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
