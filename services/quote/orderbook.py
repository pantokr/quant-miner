"""주식현재가 호가/예상체결 조회"""
import requests

from models.stock import KisCommonHeader, OrderBookRequest, OrderBookResponse
from services.auth import APP_KEY, APP_SECRET, BASE_URL


def get_orderbook(iscd: str, access_token: str = None) -> OrderBookResponse:
    """주식현재가 호가/예상체결 조회"""
    from services.auth.cache import get_valid_token
    token = access_token or get_valid_token()

    header = KisCommonHeader(
        authorization=f"Bearer {token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="FHKST01010200",
    )
    req = OrderBookRequest(FID_INPUT_ISCD=iscd)
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
        headers=header.to_dict(),
        params=req.model_dump(),
    )
    res.raise_for_status()
    data = res.json()
    o1 = data.get("output1", {})
    o2 = data.get("output2", {})
    return OrderBookResponse(
        rt_cd=data.get("rt_cd", ""),
        msg_cd=data.get("msg_cd", ""),
        msg1=data.get("msg1", ""),
        ask_prices=[int(o1.get(f"askp{i}", 0) or 0) for i in range(1, 11)],
        bid_prices=[int(o1.get(f"bidp{i}", 0) or 0) for i in range(1, 11)],
        ask_quantities=[int(o1.get(f"askp_rsqn{i}", 0) or 0) for i in range(1, 11)],
        bid_quantities=[int(o1.get(f"bidp_rsqn{i}", 0) or 0) for i in range(1, 11)],
        total_ask_qty=int(o1.get("total_askp_rsqn", 0) or 0),
        total_bid_qty=int(o1.get("total_bidp_rsqn", 0) or 0),
        expected_price=o2.get("antc_cnpr", "") if o2 else "",
    )
