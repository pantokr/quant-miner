"""트레이딩용 KIS 클라이언트 (스텁).

주문/정정/취소 등 매매 API 래퍼. 수집용과 앱키를 분리할 수 있도록 별도 클라이언트로 둔다.
TODO: 실제 주문 API(TR: 매수 TTTC0802U/VTTC0802U, 매도 TTTC0801U/VTTC0801U 등) 구현.
"""
from typing import Optional

from shared.kis_auth import get_valid_token
from shared.config import CANO, ACNT_PRDT_CD


class TraderKisClient:
    def __init__(self) -> None:
        self.cano = CANO
        self.acnt_prdt_cd = ACNT_PRDT_CD

    def token(self) -> Optional[str]:
        return get_valid_token()

    def buy(self, iscd: str, qty: int, price: int = 0) -> dict:
        """시장가/지정가 매수. TODO: 실제 주문 API 호출."""
        raise NotImplementedError("주문 API 미구현")

    def sell(self, iscd: str, qty: int, price: int = 0) -> dict:
        """시장가/지정가 매도. TODO: 실제 주문 API 호출."""
        raise NotImplementedError("주문 API 미구현")


trader_client = TraderKisClient()
