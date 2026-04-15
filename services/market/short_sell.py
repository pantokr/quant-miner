"""공매도 현황 조회"""
import requests
import logging
from typing import List

from models.stock import KisCommonHeader, ShortSellRequest, ShortSellItem, ShortSellResponse
from services.auth import APP_KEY, APP_SECRET, BASE_URL
from services.auth.cache import get_valid_token
from db.stock_short import upsert_short_sell


def get_short_sell(
    iscd: str,
    start_date: str,
    end_date: str,
    access_token: str = None,
    save: bool = False,
) -> List[ShortSellItem]:
    """
    공매도 현황 조회
    ※ 모의투자 환경에서는 지원 안 됨
    """
    token = access_token or get_valid_token()

    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="FHPST10010000",
    )
    req = ShortSellRequest(
        FID_INPUT_ISCD=iscd,
        FID_INPUT_DATE_1=start_date,
        FID_INPUT_DATE_2=end_date,
    )
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-short",
        headers=header.to_dict(),
        params=req.model_dump(),
    )
    if res.status_code != 200:
        logging.warning(f"공매도 API 오류: {res.status_code}")
        return []
    result = ShortSellResponse(**res.json())
    if not result.is_success:
        logging.warning(f"공매도 오류: {result.msg1}")
        return []
    items = result.output1
    if save and items:
        upsert_short_sell(iscd, [i.model_dump() for i in items])
    return items
