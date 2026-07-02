"""트레이딩 오케스트레이터 (배포 단위 ②, 스캐폴드).

전략에서 시그널을 받아 리스크 검사 후 주문을 실행하는 루프 뼈대.
현재는 NoopStrategy + 미구현 주문으로 실제 매매하지 않는다.

실행:
    python -m trader.main --iscd 005930 --loop --interval 60
"""
import os
import time
import argparse
import logging

from trader.strategy import NoopStrategy
from trader.risk_manager import RiskManager
from trader.kis_client_trader import trader_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("trader")


def _target_stocks(cli_iscd) -> list[str]:
    if cli_iscd:
        return cli_iscd
    env = os.getenv("TRADE_STOCKS", "")
    return [s.strip() for s in env.split(",") if s.strip()] or ["005930"]


def run_once(stocks, strategy, risk) -> None:
    for iscd in stocks:
        sig = strategy.generate(iscd)
        if not sig or not risk.approve(sig):
            logger.info(f"[{iscd}] 관망")
            continue
        logger.info(f"[{iscd}] 시그널 {sig.side} qty={sig.qty} ({sig.reason})")
        try:
            if sig.side == "buy":
                trader_client.buy(iscd, sig.qty, sig.price)
            elif sig.side == "sell":
                trader_client.sell(iscd, sig.qty, sig.price)
        except NotImplementedError:
            logger.warning(f"[{iscd}] 주문 API 미구현 — 실행 스킵 (스캐폴드)")


def main() -> None:
    parser = argparse.ArgumentParser(description="트레이더 (스캐폴드)")
    parser.add_argument("--iscd", nargs="+")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=int, default=int(os.getenv("TRADE_INTERVAL", "60")))
    args = parser.parse_args()

    stocks = _target_stocks(args.iscd)
    strategy = NoopStrategy()
    risk = RiskManager()
    logger.info(f"트레이더 시작 (스캐폴드). 대상: {stocks}")

    if not args.loop:
        run_once(stocks, strategy, risk)
        return
    while True:
        run_once(stocks, strategy, risk)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
