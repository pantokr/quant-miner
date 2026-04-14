"""외국인/기관 투자자 매매동향"""
import requests
import logging
from typing import List

from models.stock import KisCommonHeader, InvestorRequest, InvestorItem, InvestorResponse
from services.auth import APP_KEY, APP_SECRET, BASE_URL


def get_investor_trend(iscd: str, access_token: str = None) -> List[InvestorItem]:
    """
    주식현재가 투자자별 매매동향 조회
    ※ 모의투자 환경에서는 데이터가 없을 수 있음
    """
    from services.auth.cache import get_valid_token
    token = access_token or get_valid_token()

    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="FHKST01010900",
    )
    req = InvestorRequest(FID_INPUT_ISCD=iscd)
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor",
        headers=header.to_dict(),
        params=req.model_dump(),
    )
    res.raise_for_status()
    result = InvestorResponse(**res.json())
    if not result.is_success:
        logging.error(f"투자자동향 오류: {result.msg1}")
        return []
    return result.output2
