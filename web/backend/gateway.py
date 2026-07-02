"""KIS 게이트웨이(api) 호출 클라이언트.

web/backend는 KIS를 직접 호출하지 않고, 실시간 데이터가 필요할 때 이 클라이언트로
api 게이트웨이(HTTP)를 중계 호출한다.
"""
import os
import requests
from fastapi import HTTPException

GATEWAY_URL = os.getenv("KIS_GATEWAY_URL", "http://localhost:9000")


def proxy_get(path: str, params: dict | None = None):
    """api 게이트웨이의 GET 엔드포인트를 중계 호출하고 JSON을 반환."""
    try:
        r = requests.get(f"{GATEWAY_URL}{path}", params=params or {}, timeout=30)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"게이트웨이 연결 실패: {e}")
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text[:300])
    return r.json()
