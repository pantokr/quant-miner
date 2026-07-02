"""KIS 인증 공통 모듈.

기존 services/auth/token.py(토큰 발급/해지/WS접속키) + services/auth/cache.py(DB 캐시)를
통합. 모든 배포 유닛이 `from shared.kis_auth import get_valid_token` 형태로 사용한다.

설정값(APP_KEY 등)은 shared.config에서 가져오며, 하위 호환을 위해 이 모듈에서도 재노출한다.
"""
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

from shared.config import APP_KEY, APP_SECRET, BASE_URL, ENV_DV, CANO, ACNT_PRDT_CD
from shared.models.auth import (
    AuthTokenRequest, AuthTokenResponse,
    RevokeTokenRequest, RevokeTokenResponse,
    WSApprovalRequest, WSApprovalResponse,
)
from shared.db.token_store import load_token, save_token

_AUTH_HEADERS = {
    "Content-Type": "application/json",
    "charset": "UTF-8",
}

_EXPIRY_BUFFER = timedelta(minutes=5)


# ── 토큰 발급/해지/WS ──────────────────────────────────────

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


# ── 유효 토큰 (DB 캐시 우선, 만료 5분 전 재발급) ────────────

def get_valid_token() -> Optional[str]:
    """
    유효한 토큰 반환.
    DB 캐시 우선, 만료 5분 전이면 재발급.
    """
    cached = load_token(ENV_DV)
    if cached:
        expires_at = cached["expires_at"]
        # psycopg2는 TIMESTAMPTZ를 aware datetime으로 반환
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(tz=timezone.utc) < expires_at - _EXPIRY_BUFFER:
            logging.debug("DB 캐시 토큰 사용")
            return cached["access_token"]
        logging.info("토큰 만료 임박 — 재발급")

    resp = _fetch_token_response(APP_KEY, APP_SECRET, BASE_URL)
    if not resp:
        return None

    save_token(ENV_DV, resp.access_token, resp.access_token_token_expired)
    logging.info(f"토큰 발급 완료 (만료: {resp.access_token_token_expired})")
    return resp.access_token
