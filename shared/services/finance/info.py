"""종목기본정보 / 영업일 / 배당 / 추정실적 조회 서비스"""
import logging
import requests
from typing import Any, Dict, List, Optional

from shared.models.stock import KisCommonHeader
from shared.kis_auth import APP_KEY, APP_SECRET, BASE_URL, REAL_BASE_URL
from shared.kis_auth import get_valid_token, get_real_token
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
    # CTPF1002R은 모의투자에서 EGW02006으로 거부되므로 항상 실전 도메인으로 호출한다.
    token = access_token or get_real_token()
    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="CTPF1002R",
    )
    res = requests.get(
        f"{REAL_BASE_URL}/uapi/domestic-stock/v1/quotations/search-stock-info",
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
    # CTCA0903R도 모의투자 미지원 TR — 실전 도메인으로 호출한다.
    token = access_token or get_real_token()
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
            f"{REAL_BASE_URL}/uapi/domestic-stock/v1/quotations/chk-holiday",
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
    # 이 TR은 배당 내역을 output1으로 내려준다 (output 아님).
    rows = body.get("output1") or body.get("output") or []
    if save and rows:
        upsert_dividends(iscd, rows)
    return rows


def get_dividend_db(iscd: str, limit: int = 20) -> List[Dict[str, Any]]:
    """DB에서 배당 정보 조회"""
    return query_dividends(iscd, limit)


# ── 추정실적 ───────────────────────────────────────────────

# HHKST668300C0은 "항목 × 기간" 행렬로 응답한다.
#   output4[i].dt          → i번째 기간 (예: "2023.12", "2026.12E")
#   output2[r].data{i+1}   → 손익 항목 r의 i번째 기간 값
#   output3[r].data{i+1}   → 투자지표 항목 r의 i번째 기간 값
# 아래 순서는 삼성전자 확정 실적(2023년)과 대조해 확인했다.
_ESTIMATE_OUTPUT2 = [
    ("revenue", 1),              # 매출액 (억원)
    ("revenue_growth", 10),      # 매출액 증감률 (%)
    ("operating_profit", 1),     # 영업이익 (억원)
    ("op_growth", 10),           # 영업이익 증감률 (%)
    ("net_income", 1),           # 당기순이익 (억원)
    ("net_growth", 10),          # 순이익 증감률 (%)
]
# 비율·주당 지표는 0.1 단위로 내려온다(예: 368 → PER 36.8, 21310 → EPS 2,131원).
_ESTIMATE_OUTPUT3 = [
    ("ebitda", 1),               # EBITDA (억원)
    ("eps", 10),                 # EPS (원)
    ("eps_growth", 10),          # EPS 증감률 (%)
    ("per", 10),                 # PER (배)
    ("pbr", 10),                 # PBR (배)
    ("roe", 10),                 # ROE (%)
    ("debt_ratio", 10),          # 부채비율 (%)
    # output3[7]은 의미를 확인하지 못해 노출하지 않는다.
]


def _scaled(raw: Any, divisor: int) -> Optional[float]:
    try:
        value = float(str(raw).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return value / divisor if divisor != 1 else value


def _flatten_estimate(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    """행렬 응답을 기간별 dict 리스트로 변환."""
    periods = [str(p.get("dt", "")).strip() for p in body.get("output4") or []]
    if not periods:
        return []

    def column(block: List[Dict[str, Any]], spec, index: int) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for row_idx, (name, divisor) in enumerate(spec):
            if row_idx >= len(block):
                continue
            out[name] = _scaled(block[row_idx].get(f"data{index + 1}"), divisor)
        return out

    out2 = body.get("output2") or []
    out3 = body.get("output3") or []
    info = body.get("output1") or {}

    rows = []
    for i, period in enumerate(periods):
        if not period:
            continue
        row: Dict[str, Any] = {
            # "2026.12E"의 E는 추정치 표시 — 기간 키는 YYYYMM으로 정규화한다.
            "stac_yymm": period.replace(".", "").rstrip("E")[:6],
            "period_label": period,
            "is_estimate": period.endswith("E"),
            "analyst": str(info.get("name1", "")).strip(),
            "opinion": str(info.get("rcmd_name", "")).strip(),
        }
        row.update(column(out2, _ESTIMATE_OUTPUT2, i))
        row.update(column(out3, _ESTIMATE_OUTPUT3, i))
        rows.append(row)
    return rows


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

    rows = _flatten_estimate(body)
    if save and rows:
        upsert_estimate(iscd, rows)
    return rows


def get_estimate_db(iscd: str, limit: int = 8) -> List[Dict[str, Any]]:
    """DB에서 추정실적 조회"""
    return query_estimate(iscd, limit)
