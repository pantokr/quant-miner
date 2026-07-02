"""재무정보 조회 서비스 (재무상태표 / 손익계산서 / 재무비율 / 수익성 / 안정성 / 성장성)"""
import logging
import requests
from typing import Any, Dict, List

from shared.models.stock import KisCommonHeader
from shared.kis_auth import APP_KEY, APP_SECRET, BASE_URL
from shared.kis_auth import get_valid_token
from shared.db.stock_finance import upsert_finance, query_finance

logger = logging.getLogger(__name__)

# ── TR_ID 매핑 ────────────────────────────────────────────
_FINANCE_META: Dict[str, Dict[str, str]] = {
    "balance_sheet": {
        "path": "/uapi/domestic-stock/v1/finance/balance-sheet",
        "tr_id": "FHKST66430100",
    },
    "income_statement": {
        "path": "/uapi/domestic-stock/v1/finance/income-statement",
        "tr_id": "FHKST66430200",
    },
    "financial_ratio": {
        "path": "/uapi/domestic-stock/v1/finance/financial-ratio",
        "tr_id": "FHKST66430300",
    },
    "profit_ratio": {
        "path": "/uapi/domestic-stock/v1/finance/profit-ratio",
        "tr_id": "FHKST66430400",
    },
    "stability_ratio": {
        "path": "/uapi/domestic-stock/v1/finance/stability-ratio",
        "tr_id": "FHKST66430600",
    },
    "growth_ratio": {
        "path": "/uapi/domestic-stock/v1/finance/growth-ratio",
        "tr_id": "FHKST66430800",
    },
}


def _fetch_finance(
    token: str,
    finance_type: str,
    iscd: str,
    div_cls_code: str,
) -> List[Dict[str, Any]]:
    """단일 재무 API 호출 → output 리스트 반환"""
    meta = _FINANCE_META[finance_type]
    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY,
        appsecret=APP_SECRET,
        tr_id=meta["tr_id"],
    )
    params = {
        "FID_DIV_CLS_CODE": div_cls_code,
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": iscd,
    }
    res = requests.get(
        f"{BASE_URL}{meta['path']}",
        headers=header.to_dict(),
        params=params,
    )
    res.raise_for_status()
    body = res.json()
    if body.get("rt_cd") != "0":
        logger.error(f"[{finance_type}] {iscd} 오류: {body.get('msg1')}")
        return []
    return body.get("output", [])


def get_finance(
    iscd: str,
    finance_type: str,
    period_type: str = "A",
    access_token: str = None,
    save: bool = False,
) -> List[Dict[str, Any]]:
    """
    재무 데이터 조회

    Args:
        iscd:         종목코드
        finance_type: balance_sheet | income_statement | financial_ratio |
                      profit_ratio | stability_ratio | growth_ratio
        period_type:  "A" 연간 | "Q" 분기
        save:         True 시 DB 적재
    """
    if finance_type not in _FINANCE_META:
        raise ValueError(f"지원하지 않는 finance_type: {finance_type}")

    token = access_token or get_valid_token()
    div_cls_code = "0" if period_type == "A" else "1"
    rows = _fetch_finance(token, finance_type, iscd, div_cls_code)

    if save and rows:
        upsert_finance(iscd, finance_type, period_type, rows)

    return rows


def get_finance_from_db(
    iscd: str,
    finance_type: str,
    period_type: str = "A",
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """DB에서 재무 데이터 조회 (API 호출 없음)"""
    return query_finance(iscd, finance_type, period_type, limit)
