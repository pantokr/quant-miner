"""KIS 종목 마스터 파일을 내려받아 stock_master 테이블에 적재.

사용:
    python scripts/load_stock_master.py            # KOSPI + KOSDAQ 적재
    python scripts/load_stock_master.py --dry-run  # 적재 없이 파싱 결과만 확인
    python scripts/load_stock_master.py --keep-delisted  # 폐지 종목 삭제 안 함

사명 변경·시장 이전·신규 상장/폐지가 반영되므로 주기적으로(주 1회 정도) 실행한다.

마스터 파일 형식
    - 인코딩 cp949, 고정폭 레코드
    - 각 줄의 끝쪽 고정 길이(KOSPI 228 / KOSDAQ 222)를 잘라낸 앞부분이
      [단축코드 9][표준코드(ISIN) 12][한글종목명 나머지]
    - 6자리 숫자 코드만 취한다(ETF/ETN 포함, 펀드류의 9자리 코드는 제외)
"""
import argparse
import io
import logging
import sys
import zipfile

import requests

from shared.db.stock_master import (
    count_master,
    create_table,
    delete_missing,
    upsert_master,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://new.real.download.dws.co.kr/common/master"

# (파일명, 줄 끝에서 잘라낼 고정폭 길이, 시장구분)
SOURCES = [
    ("kospi_code", 228, "KOSPI"),
    ("kosdaq_code", 222, "KOSDAQ"),
]


def fetch(name: str) -> bytes:
    url = f"{BASE_URL}/{name}.mst.zip"
    logger.info(f"  내려받는 중: {url}")
    res = requests.get(url, timeout=60)
    res.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
        return z.read(z.namelist()[0])


def parse(raw: bytes, tail: int, market: str) -> list[dict]:
    rows = []
    for line in io.StringIO(raw.decode("cp949", errors="replace")):
        line = line.rstrip("\r\n")
        if not line:
            continue
        head = line[0: len(line) - tail]
        code = head[0:9].rstrip()
        isin = head[9:21].rstrip()
        name = head[21:].strip()
        if len(code) != 6 or not code.isdigit() or not name:
            continue
        rows.append({
            "stock_code": code,
            "name": name,
            "market": market,
            "isin": isin or None,
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="KIS 종목 마스터 적재")
    parser.add_argument("--dry-run", action="store_true", help="DB에 쓰지 않고 결과만 출력")
    parser.add_argument("--keep-delisted", action="store_true",
                        help="마스터에 없는 기존 종목을 삭제하지 않음")
    args = parser.parse_args()

    all_rows: list[dict] = []
    for name, tail, market in SOURCES:
        try:
            raw = fetch(name)
        except Exception as e:
            logger.error(f"  실패: {name} — {e}")
            return 1
        rows = parse(raw, tail, market)
        logger.info(f"  {market:6} {len(rows):>5}건 파싱")
        all_rows.extend(rows)

    if not all_rows:
        logger.error("파싱된 종목이 없습니다. 마스터 파일 형식이 바뀌었을 수 있습니다.")
        return 1

    # 같은 코드가 두 파일에 모두 있으면 뒤(KOSDAQ)가 이기지 않도록 앞선 것을 유지
    unique: dict[str, dict] = {}
    for row in all_rows:
        unique.setdefault(row["stock_code"], row)
    rows = list(unique.values())

    if args.dry_run:
        logger.info(f"\n[dry-run] 적재 대상 {len(rows)}건. 샘플:")
        for r in rows[:5]:
            logger.info(f"  {r['stock_code']}  {r['market']:6} {r['name']}")
        return 0

    create_table()
    saved = upsert_master(rows)
    logger.info(f"\n  적재 {saved}건")

    if not args.keep_delisted:
        removed = delete_missing([r["stock_code"] for r in rows])
        if removed:
            logger.info(f"  폐지/제외 {removed}건 삭제")

    logger.info(f"  stock_master 총 {count_master()}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
