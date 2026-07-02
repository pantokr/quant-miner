from pydantic import BaseModel


class KisCommonHeader(BaseModel):
    """KIS API 공통 요청 헤더 (auth 제외 대부분의 요청에 사용)"""
    content_type: str = "application/json"
    authorization: str          # "Bearer {access_token}"
    appkey: str
    appsecret: str
    tr_id: str                  # 거래ID (API마다 상이)
    custtype: str = "P"         # 고객타입 (P: 개인)

    def to_dict(self) -> dict:
        return {
            "Content-Type": self.content_type,
            "authorization": self.authorization,
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": self.tr_id,
            "custtype": self.custtype,
        }


class KisApiResponse(BaseModel):
    """KIS API 공통 응답 베이스"""
    rt_cd: str      # 응답코드 ("0": 성공)
    msg_cd: str     # 메시지코드
    msg1: str       # 메시지

    @property
    def is_success(self) -> bool:
        return self.rt_cd == "0"
