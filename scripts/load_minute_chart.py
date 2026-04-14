"""
분봉 데이터 일괄 적재 스크립트

26년 1월부터 오늘까지 지정 종목(들)의 분봉 데이터를 DB에 적재합니다.
DB에 이미 있는 날짜(데이터 있음 + 휴장일 포함)는 건너뜁니다.

사용법:
    python scripts/load_minute_chart.py --iscd 005930
    python scripts/load_minute_chart.py --iscd 005930 --start 20260101
    python scripts/load_minute_chart.py --iscd 005930 000660  # 다중 종목
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.auth.cache import get_valid_token
from services.chart.minute import get_daily_minute_chart
from db.stock_minute import (
    create_table,
    get_existing_dates,
    mark_no_data_date,
    upsert_minute_chart,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


def _dates_between(start: str, end: str) -> list[str]:
    cur = datetime.strptime(start, "%Y%m%d")
    end_dt = datetime.strptime(end, "%Y%m%d")
    dates = []
    while cur <= end_dt:
        dates.append(cur.strftime("%Y%m%d"))
        cur += timedelta(days=1)
    return dates


def load_stock(iscd: str, start_date: str, end_date: str, token: str) -> None:
    all_dates = _dates_between(start_date, end_date)
    existing = get_existing_dates(iscd, start_date, end_date)
    missing = [d for d in all_dates if d not in existing]

    logging.info(f"[{iscd}] 전체 {len(all_dates)}일 / 기존 {len(existing)}일 / 미수집 {len(missing)}일")

    for i, date in enumerate(missing, 1):
        logging.info(f"[{iscd}] ({i}/{len(missing)}) {date} 조회 중...")
        items = get_daily_minute_chart(iscd=iscd, date=date, access_token=token)
        if not items:
            mark_no_data_date(iscd, date)
            logging.info(f"[{iscd}] {date} 데이터 없음 (휴장일 등) — 기록 완료")
            continue
        count = upsert_minute_chart(
            stock_code=iscd,
            trade_date=date,
            rows=[item.model_dump() for item in items],
        )
        logging.info(f"[{iscd}] {date} {count}건 저장")


def main():
    parser = argparse.ArgumentParser(description="분봉 데이터 일괄 적재")
    parser.add_argument("--iscd", nargs="+", required=True, help="종목코드 (복수 가능)")
    parser.add_argument("--start", default="20260101", help="시작일 YYYYMMDD (기본: 20260101)")
    parser.add_argument(
        "--end",
        default=datetime.today().strftime("%Y%m%d"),
        help="종료일 YYYYMMDD (기본: 오늘)",
    )
    args = parser.parse_args()

    create_table()

    token = get_valid_token()
    if not token:
        logging.error("토큰 발급 실패")
        sys.exit(1)

    for iscd in args.iscd:
        logging.info(f"=== {iscd} 시작 ({args.start} ~ {args.end}) ===")
        load_stock(iscd, args.start, args.end, token)
        logging.info(f"=== {iscd} 완료 ===")


if __name__ == "__main__":
    main()
