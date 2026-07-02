from pydantic import BaseModel


class AuthTokenResponse(BaseModel):
    access_token: str
    access_token_token_expired: str
    token_type: str
    expires_in: int


class RevokeTokenResponse(BaseModel):
    code: str
    message: str


class WSApprovalResponse(BaseModel):
    approval_key: str
