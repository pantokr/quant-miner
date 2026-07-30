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
        tr_id="FHPST04760000",
    )
    # 이 TR은 기준일(FID_INPUT_DATE_1) 하나만 받고 그 이전 30영업일을 돌려준다.
    # FID_COND_SCR_DIV_CODE(화면번호)가 없으면 "INPUT FIELD NOT FOUND"로 거부된다.
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/daily-credit-balance",
        headers=header.to_dict(),
        params={
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "20476",
            "FID_INPUT_ISCD": iscd,
            "FID_INPUT_DATE_1": end_date,
            "FID_DIV_CLS_CODE": "0",
        },
    )
    if res.status_code != 200:
        logging.warning(f"신용잔고 API 오류: {res.status_code}")
        return []
    result = CreditResponse(**res.json())
    if not result.is_success:
        logging.warning(f"신용잔고 오류: {result.msg1}")
        return []
    # 응답이 기준일 이전 30영업일 고정이므로 요청 구간으로 한 번 더 거른다.
    items = [i for i in result.output if start_date <= i.deal_date <= end_date]
    if save and items:
        upsert_credit(iscd, [i.model_dump() for i in items])
    return items
