"""대시보드 라우터 — 계좌 요약.

잔고/포지션은 실시간(브로커) 데이터이므로 api 게이트웨이(/account/balance)를 중계한다.
backend는 KIS를 직접 호출하지 않는다.
"""
from fastapi import APIRouter, Request

from web.backend.gateway import proxy_get

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(request: Request):
    """계좌 요약 + 보유 포지션 (게이트웨이 /account/balance 중계)."""
    return proxy_get("/account/balance", dict(request.query_params))
