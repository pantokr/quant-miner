"""종목기본정보 / 영업일 / 배당 / 추정실적 조회 서비스"""
import logging
import requests
from typing import Any, Dict, List, Optional

from shared.models.stock import KisCommonHeader
from shared.kis_auth import APP_KEY, APP_SECRET, BASE_URL
from shared.kis_auth import get_valid_token
from shared.db.stock_info import (
    upsert_stock_info, get_stock_info,
    upsert_dividends, query_dividends,
    upsert_estimate, query_estimate,
)
from shared.db.stock_holiday import upsert_holidays, get_trade_days

logger = logging.getLogger(__name__)


# ── 종목기본조회 ───────────────────────────────────────────

def get_stock_info_api(
    iscd: str,
    prdt_type_cd: str = "300",
    access_token: str = None,
    save: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    주식기본조회 (CTPF1002R)

    Args:
        iscd:          종목코드 (6자리)
        prdt_type_cd:  300:주식/ETF/ETN/ELW  302:채권  306:ELS
        save:          True 시 DB 저장
    """
    token = access_token or get_valid_token()
    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="CTPF1002R",
    )
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/search-stock-info",
        headers=header.to_dict(),
        params={"PRDT_TYPE_CD": prdt_type_cd, "PDNO": iscd},
    )
    res.raise_for_status()
    body = res.json()
    if body.get("rt_cd") != "0":
        logger.error(f"주식기본조회 오류: {body.get('msg1')}")
        return None
    output = body.get("output", {})
    if save and output:
        upsert_stock_info(iscd, output)
    return output


def get_stock_info_db(iscd: str) -> Optional[Dict[str, Any]]:
    """DB에서 종목기본정보 조회"""
    return get_stock_info(iscd)


# ── 영업일조회 ────────────────────────────────────────────

def fetch_holidays(
    bass_dt: str,
    access_token: str = None,
    save: bool = False,
) -> List[Dict[str, Any]]:
    """
    영업일조회 (CTCA0903R) - 기준일 이후 100개 영업일 정보 반환
    ※ 단기간 내 1회 호출 권장

    Args:
        bass_dt: 기준일자 YYYYMMDD
        save:    True 시 DB 적재
    """
    token = access_token or get_valid_token()
    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="CTCA0903R",
    )
    all_rows: List[Dict[str, Any]] = []
    ctx_fk = ""
    ctx_nk = ""

    while True:
        res = requests.get(
            f"{BASE_URL}/uapi/domestic-stock/v1/quotations/chk-holiday",
            headers=header.to_dict(),
            params={"BASS_DT": bass_dt, "CTX_AREA_FK": ctx_fk, "CTX_AREA_NK": ctx_nk},
        )
        res.raise_for_status()
        body = res.json()
        if body.get("rt_cd") != "0":
            logger.error(f"영업일조회 오류: {body.get('msg1')}")
            break

        rows = body.get("output", [])
        all_rows.extend(rows)

        # 연속 조회 여부
        tr_cont = body.get("tr_cont", "")
        if tr_cont not in ("M", "F"):
            break
        ctx_fk = body.get("CTX_AREA_FK", "")
        ctx_nk = body.get("CTX_AREA_NK", "")
        if not ctx_nk:
            break

    if save and all_rows:
        upsert_holidays(all_rows)
    return all_rows


def get_trade_days_db(start_date: str, end_date: str) -> List[str]:
    """DB에서 거래일 목록 조회"""
    return get_trade_days(start_date, end_date)


# ── 배당금 ────────────────────────────────────────────────

def get_dividend(
    iscd: str,
    start_dt: str,
    end_dt: str,
    access_token: str = None,
    save: bool = False,
) -> List[Dict[str, Any]]:
    """
    배당금 조회 (HHKDB669102C0)

    Args:
        iscd:     종목코드
        start_dt: 시작일 YYYYMMDD
        end_dt:   종료일 YYYYMMDD
        save:     True 시 DB 적재
    """
    token = access_token or get_valid_token()
    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="HHKDB669102C0",
    )
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/ksdinfo/dividend",
        headers=header.to_dict(),
        params={
            "SHT_CD": iscd,
            "F_DT": start_dt,
            "T_DT": end_dt,
            "GB1": "",
            "CTS": "",
            "HIGH_GB": "",
        },
    )
    res.raise_for_status()
    body = res.json()
    if body.get("rt_cd") != "0":
        logger.warning(f"배당금조회 오류: {body.get('msg1')}")
        return []
    rows = body.get("output", [])
    if save and rows:
        upsert_dividends(iscd, rows)
    return rows


def get_dividend_db(iscd: str, limit: int = 20) -> List[Dict[str, Any]]:
    """DB에서 배당 정보 조회"""
    return query_dividends(iscd, limit)


# ── 추정실적 ───────────────────────────────────────────────

def get_estimate_perform(
    iscd: str,
    access_token: str = None,
    save: bool = False,
) -> List[Dict[str, Any]]:
    """
    추정실적 조회 (HHKST668300C0)

    Args:
        iscd: 종목코드
        save: True 시 DB 적재
    """
    token = access_token or get_valid_token()
    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="HHKST668300C0",
    )
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/estimate-perform",
        headers=header.to_dict(),
        params={"SHT_CD": iscd},
    )
    res.raise_for_status()
    body = res.json()
    if body.get("rt_cd") != "0":
        logger.warning(f"추정실적조회 오류: {body.get('msg1')}")
        return []
    rows = body.get("output", [])
    if save and rows:
        upsert_estimate(iscd, rows)
    return rows


def get_estimate_db(iscd: str, limit: int = 8) -> List[Dict[str, Any]]:
    """DB에서 추정실적 조회"""
    return query_estimate(iscd, limit)
