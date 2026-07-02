"""데이터 수집 오케스트레이터 (배포 단위 ①).

대상 종목에 대해 분봉 누락분 + 일별 OHLCV를 주기적으로 수집해 DB에 적재한다.
기존 shared.services 로직을 재사용하며, 단발 실행(--once)과 루프 실행을 모두 지원한다.

실행:
    python -m collector.main --iscd 005930 000660 --start 20260101
    python -m collector.main --iscd 005930 --loop --interval 3600
"""
import os
import sys
import time
import argparse
import logging
from datetime import datetime

from shared.kis_auth import get_valid_token
from shared.services.quote.ohlcv import get_ohlcv_all
from collector.gap_filler import fill_minute_gaps

# 테이블 보장
from shared.db.stock_minute import create_table as create_minute_table
from shared.db.stock_ohlcv import create_table as create_ohlcv_table
from shared.db.token_store import create_table as create_token_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("collector")


def _target_stocks(cli_iscd) -> list[str]:
    if cli_iscd:
        return cli_iscd
    env = os.getenv("COLLECT_STOCKS", "")
    return [s.strip() for s in env.split(",") if s.strip()] or ["005930"]


def run_once(stocks: list[str], start: str) -> None:
    today = datetime.today().strftime("%Y%m%d")
    token = get_valid_token()
    if not token:
        logger.error("토큰 발급 실패 — 수집 중단")
        return
    for iscd in stocks:
        logger.info(f"=== {iscd} 수집 시작 ({start}~{today}) ===")
        try:
            get_ohlcv_all(iscd=iscd, start_date=start, period="D", save=True)
        except Exception as e:
            logger.exception(f"[{iscd}] OHLCV 수집 오류: {e}")
        try:
            fill_minute_gaps(iscd, start, today)
        except Exception as e:
            logger.exception(f"[{iscd}] 분봉 수집 오류: {e}")
        logger.info(f"=== {iscd} 완료 ===")


def main() -> None:
    parser = argparse.ArgumentParser(description="데이터 수집기")
    parser.add_argument("--iscd", nargs="+", help="종목코드 (미지정 시 COLLECT_STOCKS env)")
    parser.add_argument("--start", default=os.getenv("COLLECT_START", "20260101"))
    parser.add_argument("--loop", action="store_true", help="주기 반복 실행")
    parser.add_argument("--interval", type=int, default=int(os.getenv("COLLECT_INTERVAL", "3600")))
    args = parser.parse_args()

    create_token_table()
    create_minute_table()
    create_ohlcv_table()

    stocks = _target_stocks(args.iscd)
    logger.info(f"대상 종목: {stocks}")

    if not args.loop:
        run_once(stocks, args.start)
        return

    while True:
        run_once(stocks, args.start)
        logger.info(f"{args.interval}초 후 재수집")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
