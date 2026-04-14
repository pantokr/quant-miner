import os
import requests
import logging
from typing import Optional
from dotenv import load_dotenv

from models.auth import (
    AuthTokenRequest, AuthTokenResponse,
    RevokeTokenRequest, RevokeTokenResponse,
    WSApprovalRequest, WSApprovalResponse,
)

load_dotenv()

APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
ENV_DV = os.getenv("KIS_ENV", "demo")  # "real" or "demo"

BASE_URL = (
    "https://openapi.koreainvestment.com:9443"
    if ENV_DV == "real"
    else "https://openapivts.koreainvestment.com:29443"
)

_AUTH_HEADERS = {
    "Content-Type": "application/json",
    "charset": "UTF-8",
}


def _fetch_token_response(appkey: str, appsecret: str, base_url: str) -> Optional[AuthTokenResponse]:
    """접근 토큰 발급 — 응답 전체 반환 (만료시간 포함)"""
    req = AuthTokenRequest(appkey=appkey, appsecret=appsecret)
    res = requests.post(
        f"{base_url}/oauth2/tokenP",
        headers=_AUTH_HEADERS,
        data=req.model_dump_json(),
    )
    if res.status_code != 200:
        logging.error(f"토큰 발급 실패: [{res.status_code}] {res.text}")
        return None
    return AuthTokenResponse(**res.json())


def get_access_token(appkey: str, appsecret: str, base_url: str) -> Optional[str]:
    """접근 토큰(Access Token) 발급 — 토큰 문자열만 반환"""
    resp = _fetch_token_response(appkey, appsecret, base_url)
    return resp.access_token if resp else None


def revoke_token(appkey: str, appsecret: str, token: str, base_url: str) -> bool:
    """접근 토큰(Access Token) 해지"""
    req = RevokeTokenRequest(appkey=appkey, appsecret=appsecret, token=token)
    res = requests.post(
        f"{base_url}/oauth2/revokeP",
        headers=_AUTH_HEADERS,
        data=req.model_dump_json(),
    )
    if res.status_code != 200:
        logging.error(f"토큰 해지 실패: [{res.status_code}] {res.text}")
        return False
    result = RevokeTokenResponse(**res.json())
    return result.code == "200"


def get_ws_token(appkey: str, appsecret: str, base_url: str) -> Optional[str]:
    """웹소켓 접속키(Approval Key) 발급"""
    req = WSApprovalRequest(appkey=appkey, secretkey=appsecret)
    res = requests.post(
        f"{base_url}/oauth2/Approval",
        headers=_AUTH_HEADERS,
        data=req.model_dump_json(),
    )
    if res.status_code != 200:
        logging.error(f"WS 접속키 발급 실패: [{res.status_code}] {res.text}")
        return None
    return WSApprovalResponse(**res.json()).approval_key
