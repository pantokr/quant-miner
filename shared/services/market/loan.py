"""종목별 일별 대차거래추이 조회 (HHPST074500C0).

대차잔고는 "빌려 놓았지만 아직 갚지 않은 주식"이다. 공매도는 대차로 빌린 주식을
파는 것이므로 대차잔고가 늘면 공매도 압력이 쌓이고 있다는 신호로 읽힌다.
공매도 체결량(이미 일어난 일)보다 한 발 앞서는 지표라 따로 받아 둘 값어치가 있다.

※ 실전투자 계정 전용 — 모의 도메인에는 이 TR이 없다.
"""
import logging
import requests
from typing import List

from shared.models.stock import KisCommonHeader
from shared.config import KIS_TIMEOUT
from shared.kis_auth import APP_KEY, APP_SECRET, BASE_URL
from shared.kis_auth import get_valid_token
from shared.db.stock_loan import upsert_loan_trans

_TR_ID = "HHPST074500C0"
_PATH = "/uapi/domestic-stock/v1/quotations/daily-loan-trans"

# MRKT_DIV_CLS_CODE — 1:코스피 2:코스닥 3:종목.
# 1/2를 주면 종목코드를 넣어도 시장 전체 집계가 돌아온다 (값이 지수 수준으로 나와
# 종목 데이터인 줄 알고 쓰면 조용히 틀린다). 종목별은 반드시 3이다.
_MARKET_DIV_STOCK = "3"


def get_loan_trans(
    iscd: str,
    start_date: str,
    end_date: str,
    access_token: str = None,
    save: bool = False,
) -> List[dict]:
    """종목별 일별 대차거래추이 조회 (일자 오름차순)."""
    token = access_token or get_valid_token()

    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id=_TR_ID,
    )
    params = {
        "MRKT_DIV_CLS_CODE": _MARKET_DIV_STOCK,
        "MKSC_SHRN_ISCD": iscd,
        "START_DATE": start_date,
        "END_DATE": end_date,
        "CTS": "",
    }
    res = requests.get(f"{BASE_URL}{_PATH}", headers=header.to_dict(),
                       params=params, timeout=KIS_TIMEOUT)
    if res.status_code != 200:
        logging.warning(f"대차거래 API 오류: {res.status_code}")
        return []

    body = res.json()
    if body.get("rt_cd") != "0":
        logging.warning(f"대차거래 오류: {body.get('msg_cd')} {body.get('msg1')}")
        return []

    rows = body.get("output1") or []
    rows.sort(key=lambda r: r.get("bsop_date", ""))
    if save and rows:
        upsert_loan_trans(iscd, rows)
    return rows
