from pydantic import BaseModel


class AuthTokenRequest(BaseModel):
    grant_type: str = "client_credentials"
    appkey: str
    appsecret: str


class RevokeTokenRequest(BaseModel):
    appkey: str
    appsecret: str
    token: str


class WSApprovalRequest(BaseModel):
    grant_type: str = "client_credentials"
    appkey: str
    secretkey: str
