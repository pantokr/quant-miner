"""데이터 수집 오케스트레이터 (배포 단위: collector).

대상 종목의 일별 OHLCV · 분봉 누락분 · 투자자 매매동향을 수집해 DB에 적재한다.
--only 로 특정 데이터만 수집, 단발/루프 실행을 지원한다.

실행:
    python -m collector.main --iscd 005930 000660 --start 20260101
    python -m collector.main --iscd 005930 --only ohlcv
    python -m collector.main --iscd 005930 --loop --interval 3600
"""
import os
import time
import argparse
import logging
from datetime import datetime
from typing import List

from shared.kis_auth import get_valid_token
from shared.services.quote.ohlcv import get_ohlcv_all
from shared.services.quote.investor import get_investor_trend
from collector.gap_filler import fill_minute_gaps

# 테이블 보장
from shared.db.stock_minute import create_table as create_minute_table
from shared.db.stock_ohlcv import create_table as create_ohlcv_table
from shared.db.stock_investor import create_table as create_investor_table
from shared.db.token_store import create_table as create_token_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("collector")

KINDS = ("ohlcv", "minute", "investor")


def _target_stocks(cli_iscd) -> List[str]:
    if cli_iscd:
        return cli_iscd
    env = os.getenv("COLLECT_STOCKS", "")
    return [s.strip() for s in env.split(",") if s.strip()] or ["005930"]


def _collect_stock(iscd: str, start: str, today: str, kinds) -> dict:
    """한 종목 수집. 종류별 건수/오류를 dict로 반환."""
    stat = {}
    if "ohlcv" in kinds:
        try:
            items = get_ohlcv_all(iscd=iscd, start_date=start, period="D", save=True)
            stat["ohlcv"] = len(items)
        except Exception as e:
            logger.exception(f"[{iscd}] OHLCV 오류: {e}")
            stat["ohlcv"] = "ERR"
    if "investor" in kinds:
        try:
            items = get_investor_trend(iscd, save=True)
            stat["investor"] = len(items)
        except Exception as e:
            logger.exception(f"[{iscd}] 투자자 오류: {e}")
            stat["investor"] = "ERR"
    if "minute" in kinds:
        try:
            stat["minute"] = fill_minute_gaps(iscd, start, today)
        except Exception as e:
            logger.exception(f"[{iscd}] 분봉 오류: {e}")
            stat["minute"] = "ERR"
    return stat


def run_once(stocks: List[str], start: str, kinds) -> None:
    today = datetime.today().strftime("%Y%m%d")
    if not get_valid_token():
        logger.error("토큰 발급 실패 — 수집 중단")
        return

    summary = {}
    for i, iscd in enumerate(stocks, 1):
        logger.info(f"=== ({i}/{len(stocks)}) {iscd} 수집 [{','.join(kinds)}] ({start}~{today}) ===")
        summary[iscd] = _collect_stock(iscd, start, today, kinds)
        logger.info(f"=== {iscd} 완료: {summary[iscd]} ===")

    logger.info("── 수집 요약 ──")
    for iscd, stat in summary.items():
        logger.info(f"  {iscd}: " + " · ".join(f"{k}={stat.get(k, '-')}" for k in KINDS if k in kinds))


def main() -> None:
    p = argparse.ArgumentParser(description="데이터 수집기")
    p.add_argument("--iscd", nargs="+", help="종목코드 (미지정 시 COLLECT_STOCKS env)")
    p.add_argument("--start", default=os.getenv("COLLECT_START", "20260101"))
    p.add_argument("--only", choices=KINDS, nargs="+", help="특정 데이터만 수집 (기본: 전체)")
    p.add_argument("--loop", action="store_true", help="주기 반복 실행")
    p.add_argument("--interval", type=int, default=int(os.getenv("COLLECT_INTERVAL", "3600")))
    args = p.parse_args()

    create_token_table()
    create_minute_table()
    create_ohlcv_table()
    create_investor_table()

    stocks = _target_stocks(args.iscd)
    kinds = tuple(args.only) if args.only else KINDS
    logger.info(f"대상 종목: {stocks} · 수집종류: {kinds}")

    if not args.loop:
        run_once(stocks, args.start, kinds)
        return

    while True:
        run_once(stocks, args.start, kinds)
        logger.info(f"{args.interval}초 후 재수집")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
