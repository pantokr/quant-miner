"""백테스트 실행 CLI.

DB의 일봉으로 이동평균 교차 전략을 과거 구간에 돌려 성과를 출력한다.
DB에 데이터가 없으면 KIS에서 받아 적재(save=True) 후 재조회한다.

실행:
    python -m research.backtest.run --iscd 005930 --start 20240101
    python -m research.backtest.run --iscd 005930 --start 20230101 --short 5 --long 20
"""
import argparse
import logging
from datetime import datetime

from shared.db.stock_ohlcv import query_ohlcv
from trader.strategy import MovingAverageCrossStrategy
from research.backtest.engine import run_backtest

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("backtest")


def load_closes(iscd: str, start: str, end: str) -> list[float]:
    """DB 우선, 없으면 KIS에서 받아 적재 후 재조회."""
    rows = query_ohlcv(iscd, "D", start, end)
    if not rows:
        logger.info(f"[{iscd}] DB에 데이터 없음 → KIS에서 수집(save)...")
        # 지연 import: KIS 호출은 필요할 때만
        from shared.services.quote.ohlcv import get_ohlcv_all
        get_ohlcv_all(iscd=iscd, start_date=start, period="D", save=True)
        rows = query_ohlcv(iscd, "D", start, end)
    return [float(r["close"]) for r in rows if r.get("close") is not None]


def main() -> None:
    p = argparse.ArgumentParser(description="이동평균 교차 백테스트")
    p.add_argument("--iscd", required=True)
    p.add_argument("--start", default="20240101")
    p.add_argument("--end", default=datetime.today().strftime("%Y%m%d"))
    p.add_argument("--short", type=int, default=5)
    p.add_argument("--long", type=int, default=20)
    p.add_argument("--cash", type=int, default=10_000_000)
    args = p.parse_args()

    closes = load_closes(args.iscd, args.start, args.end)
    if len(closes) < args.long + 1:
        logger.error(f"데이터 부족: {len(closes)}개 (최소 {args.long + 1} 필요)")
        return

    strategy = MovingAverageCrossStrategy(args.short, args.long)
    result = run_backtest(closes, strategy, initial_cash=args.cash)

    print(f"\n=== 백테스트 {args.iscd} ({args.start}~{args.end}, {len(closes)}봉) ===")
    print(result.summary())


if __name__ == "__main__":
    main()
