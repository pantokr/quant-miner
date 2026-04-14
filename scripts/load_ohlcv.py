"""
일봉(OHLCV) 데이터 전 기간 일괄 적재 스크립트

상장 이래 오늘까지의 일봉 데이터를 DB에 적재합니다.
3년 단위 청크로 순방향 페이지네이션합니다.

사용법:
    python scripts/load_ohlcv.py --iscd 005930
    python scripts/load_ohlcv.py --iscd 005930 000660  # 다중 종목
    python scripts/load_ohlcv.py --iscd 005930 --start 20200101  # 시작일 지정
"""

import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.quote.ohlcv import get_ohlcv_all
from db.stock_ohlcv import create_table, upsert_ohlcv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    parser = argparse.ArgumentParser(description="일봉 전 기간 DB 적재")
    parser.add_argument("--iscd", nargs="+", required=True, help="종목코드 (복수 가능)")
    parser.add_argument(
        "--start",
        default="19900101",
        help="수집 시작일 YYYYMMDD (기본: 19900101)",
    )
    parser.add_argument(
        "--period",
        default="D",
        choices=["D", "W", "M", "Y"],
        help="기간 단위 D:일 W:주 M:월 Y:년 (기본: D)",
    )
    args = parser.parse_args()

    create_table()

    for iscd in args.iscd:
        logging.info(f"=== {iscd} 일봉 수집 시작 ({args.start} ~) ===")
        items = get_ohlcv_all(iscd=iscd, start_date=args.start, period=args.period)
        if not items:
            logging.warning(f"[{iscd}] 수집된 데이터 없음")
            continue
        count = upsert_ohlcv(iscd, args.period, [i.model_dump() for i in items])
        logging.info(f"=== {iscd} 완료: {count}건 저장 ===")


if __name__ == "__main__":
    main()
