"""신용잔고 조회"""
import requests
import logging
from typing import List

from shared.models.stock import KisCommonHeader, CreditRequest, CreditItem, CreditResponse
from shared.kis_auth import APP_KEY, APP_SECRET, BASE_URL
from shared.kis_auth import get_valid_token
from shared.db.stock_short import upsert_credit


def get_credit(
    iscd: str,
    start_date: str,
    end_date: str,
    access_token: str = None,
    save: bool = False,
) -> List[CreditItem]:
    """
    신용잔고 조회
    ※ 모의투자 환경에서는 지원 안 됨
    """
    token = access_token or get_valid_token()

    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="FHKST01650300",
    )
    req = CreditRequest(
        FID_INPUT_ISCD=iscd,
        FID_INPUT_DATE_1=start_date,
        FID_INPUT_DATE_2=end_date,
    )
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-credit-by-company",
        headers=header.to_dict(),
        params=req.model_dump(),
    )
    if res.status_code != 200:
        logging.warning(f"신용잔고 API 오류: {res.status_code}")
        return []
    result = CreditResponse(**res.json())
    if not result.is_success:
        logging.warning(f"신용잔고 오류: {result.msg1}")
        return []
    items = result.output1
    if save and items:
        upsert_credit(iscd, [i.model_dump() for i in items])
    return items
