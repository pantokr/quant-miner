"""국내 종목코드 전수 스윕 — KIS 종목기본조회로 stock_info / stock_master 적재.

'000000'부터 '999999'까지 6자리 코드를 순회하며 KIS 종목기본조회를 호출하고,
응답이 있는 코드만 DB에 적재한다. 국내 주식 전용(PRDT_TYPE_CD=300).

사용:
    python scripts/sweep_stock_info.py                      # 000000~999999 전체
    python scripts/sweep_stock_info.py --start 000000 --end 009999
    python scripts/sweep_stock_info.py --resume             # 체크포인트부터 이어서
    python scripts/sweep_stock_info.py --tr-id CTPF1604R    # TR ID 변경
    python scripts/sweep_stock_info.py --rps 15             # 초당 호출 수

중단해도 --resume 으로 이어서 돌릴 수 있도록 진행 코드를 체크포인트 파일에 남긴다.

⚠ 유효한 국내 종목코드는 100만 개 중 약 3,600개(0.36%)뿐이라 나머지 호출은 모두
  헛돌게 된다. 실전 계정 20 req/s 기준으로도 전체 1회 스윕에 약 14시간이 걸린다.
  이미 상장 종목 전체를 담고 있는 KIS 마스터 파일을 쓰는 `load_stock_master.py`가
  같은 목록을 수 초 만에 채우므로, 이 스크립트는 마스터 파일에 없는 상세 필드
  (상장주수·액면가·업종 등)를 채우는 용도로 쓰는 편이 낫다. `--codes-from-master`
  옵션을 주면 마스터에 있는 코드만 순회한다.
"""
import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

import requests

from shared.kis_auth import APP_KEY, APP_SECRET, BASE_URL, get_access_token, get_valid_token
from shared.db.stock_info import create_tables, upsert_stock_info
from shared.db.stock_master import create_table as create_master_table, upsert_master

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

CHECKPOINT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sweep_checkpoint.json")
ENDPOINT = "/uapi/domestic-stock/v1/quotations/search-stock-info"

REAL_HOST = "https://openapi.koreainvestment.com:9443"

# CTPF1002R / CTPF1604R은 모의투자에서 "모의투자 TR 이 아닙니다"(EGW02006)로 거부되므로
# KIS_ENV와 무관하게 기본은 실전 호스트를 쓴다. --host demo 로 강제할 수 있다.
HOSTS = {"real": REAL_HOST, "demo": "https://openapivts.koreainvestment.com:29443"}

# 응답 output에서 종목명을 찾을 때 시도할 필드 순서 (TR에 따라 키가 다름)
NAME_KEYS = ("prdt_abrv_name", "prdt_name", "prdt_eng_abrv_name")


class RateLimiter:
    """초당 호출 수 상한. KIS는 앱키 단위로 유량을 제한한다."""

    def __init__(self, rps: float):
        self.interval = 1.0 / rps if rps > 0 else 0.0
        self._next = 0.0

    def wait(self) -> None:
        if self.interval <= 0:
            return
        now = time.monotonic()
        if now < self._next:
            time.sleep(self._next - now)
        self._next = max(now, self._next) + self.interval


def load_checkpoint() -> Optional[str]:
    if not os.path.exists(CHECKPOINT):
        return None
    try:
        with open(CHECKPOINT, encoding="utf-8") as f:
            return json.load(f).get("last_code")
    except Exception:
        return None


def save_checkpoint(code: str, found: int) -> None:
    with open(CHECKPOINT, "w", encoding="utf-8") as f:
        json.dump({"last_code": code, "found": found}, f)


def resolve_token(host: str) -> Optional[str]:
    """호출에 쓸 호스트에서 직접 토큰을 발급한다.

    get_valid_token()은 KIS_ENV(BASE_URL) 기준으로 캐시된 토큰을 주므로, 모의 설정인
    상태에서 실전 호스트를 때리면 토큰 도메인이 어긋난다. 호스트가 같을 때만 캐시를 쓴다.
    """
    if host == BASE_URL:
        return get_valid_token()
    logger.info(f"  {host} 에서 토큰 발급 (KIS_ENV={os.getenv('KIS_ENV', 'demo')} 와 다름)")
    return get_access_token(APP_KEY, APP_SECRET, host)


def fetch_one(
    session: requests.Session,
    code: str,
    token: str,
    tr_id: str,
    prdt_type_cd: str,
    host: str,
) -> Optional[Dict[str, Any]]:
    """단일 종목 조회. 없는 코드/오류는 None (스윕이 멈추지 않도록 예외를 삼킨다)."""
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
    }
    try:
        res = session.get(
            f"{host}{ENDPOINT}",
            headers=headers,
            params={"PRDT_TYPE_CD": prdt_type_cd, "PDNO": code},
            timeout=10,
        )
    except requests.RequestException:
        return None

    if res.status_code != 200:
        return None
    try:
        body = res.json()
    except ValueError:
        return None
    if body.get("rt_cd") != "0":
        return None

    output = body.get("output") or {}
    if not any(str(output.get(k, "")).strip() for k in NAME_KEYS):
        return None   # 껍데기 응답 (존재하지 않는 코드)
    return output


def master_row(code: str, output: Dict[str, Any]) -> Dict[str, Any]:
    name = next(
        (str(output[k]).strip() for k in NAME_KEYS if str(output.get(k, "")).strip()),
        code,
    )
    # 상장일이 채워진 쪽으로 시장을 판정한다
    if str(output.get("kosdaq_mket_lstg_dt", "")).strip():
        market = "KOSDAQ"
    elif str(output.get("scts_mket_lstg_dt", "")).strip():
        market = "KOSPI"
    else:
        market = "ETC"
    return {
        "stock_code": code,
        "name": name[:80],
        "market": market,
        "isin": (str(output.get("std_pdno", "")).strip() or None),
    }


def target_codes(args) -> List[str]:
    if args.codes_from_master:
        from shared.db.stock_master import search_master  # noqa: F401
        import psycopg2.extras
        from shared.db.connection import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT stock_code FROM stock_master ORDER BY stock_code")
                codes = [r[0] for r in cur.fetchall()]
        logger.info(f"마스터 기준 {len(codes)}개 코드만 순회")
        return codes

    start, end = int(args.start), int(args.end)
    return [f"{i:06d}" for i in range(start, end + 1)]


def main() -> int:
    p = argparse.ArgumentParser(description="국내 종목코드 전수 스윕")
    p.add_argument("--start", default="000000", help="시작 코드 (기본 000000)")
    p.add_argument("--end", default="999999", help="종료 코드 (기본 999999)")
    p.add_argument("--tr-id", default="CTPF1002R", help="TR ID (CTPF1002R | CTPF1604R)")
    p.add_argument("--prdt-type-cd", default="300", help="300:주식/ETF/ETN/ELW")
    p.add_argument("--host", choices=("real", "demo"), default="real",
                   help="호출 도메인. 두 TR 모두 실전 전용이므로 기본 real")
    p.add_argument("--rps", type=float, default=5.0,
                   help="초당 호출 수. 실전 20 이하 권장 (기본 5)")
    p.add_argument("--resume", action="store_true", help="체크포인트 이후부터 재개")
    p.add_argument("--codes-from-master", action="store_true",
                   help="stock_master에 있는 코드만 순회 (권장)")
    p.add_argument("--batch", type=int, default=50, help="DB 반영 배치 크기")
    args = p.parse_args()

    codes = target_codes(args)

    if args.resume:
        last = load_checkpoint()
        if last and last in codes:
            codes = codes[codes.index(last) + 1:]
            logger.info(f"체크포인트 {last} 이후부터 재개 — 남은 {len(codes)}개")

    if not codes:
        logger.info("순회할 코드가 없습니다.")
        return 0

    host = HOSTS[args.host]
    logger.info(f"대상 {len(codes)}개 | TR={args.tr_id} | {args.rps} req/s "
                f"| 예상 {len(codes) / max(args.rps, 0.001) / 3600:.1f}시간")
    logger.info(f"호스트={host}")

    create_tables()
    create_master_table()

    token = resolve_token(host)
    if not token:
        logger.error("토큰 발급 실패 — KIS_APP_KEY/SECRET 확인")
        return 1

    session = requests.Session()
    limiter = RateLimiter(args.rps)

    found = 0
    errors = 0
    pending_master: List[Dict[str, Any]] = []
    started = time.time()

    try:
        for i, code in enumerate(codes, 1):
            limiter.wait()
            output = fetch_one(session, code, token, args.tr_id, args.prdt_type_cd, host)

            if output:
                found += 1
                row = master_row(code, output)
                pending_master.append(row)
                try:
                    upsert_stock_info(code, output)
                except Exception as e:
                    errors += 1
                    logger.warning(f"  {code} 저장 실패: {e}")
                logger.info(f"  [{found}] {code}  {row['name']}  ({row['market']})")

            if len(pending_master) >= args.batch:
                upsert_master(pending_master)
                pending_master.clear()

            if i % 1000 == 0:
                elapsed = time.time() - started
                rate = i / elapsed if elapsed else 0
                logger.info(f"진행 {i}/{len(codes)}  발견 {found}  "
                            f"{rate:.1f} req/s  경과 {elapsed / 60:.1f}분")
                save_checkpoint(code, found)

    except KeyboardInterrupt:
        logger.warning("\n중단됨 — 체크포인트 저장 후 종료 (--resume 으로 재개)")
    finally:
        if pending_master:
            upsert_master(pending_master)
        if codes:
            save_checkpoint(code, found)
        logger.info(f"\n완료: 발견 {found}건 / 저장오류 {errors}건 "
                    f"/ 경과 {(time.time() - started) / 60:.1f}분")

    return 0


if __name__ == "__main__":
    sys.exit(main())
