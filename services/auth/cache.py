"""
토큰 캐시 — PostgreSQL 저장 (컨테이너 재시작에도 유지)
만료 5분 전 자동 갱신
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from services.auth.token import _fetch_token_response, APP_KEY, APP_SECRET, BASE_URL, ENV_DV

_EXPIRY_BUFFER = timedelta(minutes=5)


def get_valid_token() -> Optional[str]:
    """
    유효한 토큰 반환.
    DB 캐시 우선, 만료 5분 전이면 재발급.
    """
    from db.token_store import load_token, save_token

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
