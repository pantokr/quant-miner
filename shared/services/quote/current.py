"""주식현재가 시세 조회"""
import requests

from shared.models.stock import KisCommonHeader, CurrentPriceRequest, CurrentPriceItem, CurrentPriceResponse
from shared.kis_auth import APP_KEY, APP_SECRET, BASE_URL
from shared.kis_auth import get_valid_token


def get_current_price(iscd: str, access_token: str = None) -> CurrentPriceItem:
    """주식현재가 시세 조회"""
    token = access_token or get_valid_token()

    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="FHKST01010100",
    )
    req = CurrentPriceRequest(FID_INPUT_ISCD=iscd)
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
        headers=header.to_dict(),
        params=req.model_dump(),
    )
    res.raise_for_status()
    result = CurrentPriceResponse(**res.json())
    if not result.is_success:
        raise RuntimeError(result.msg1)
    return result.output
