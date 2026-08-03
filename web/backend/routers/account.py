"""계좌 라우터 (api 게이트웨이 중계).

잔고·주문체결은 KIS 실시간 조회라 DB에 저장본이 없다. api 게이트웨이
(`api/routers/account.py`)가 KIS 호출을 담당하고, backend는 경로와 쿼리 파라미터를
그대로 넘겨 중계만 하므로 게이트웨이에 계좌 엔드포인트가 늘어도 여기는 그대로 둔다.
"""
from fastapi import APIRouter, Request

from web.backend.gateway import proxy_get

router = APIRouter(prefix="/account", tags=["account (proxy→api)"])


@router.get("/{sub_path:path}")
def account_proxy(sub_path: str, request: Request):
    """/account/** 전체를 게이트웨이로 중계 (잔고·일별 주문체결)."""
    return proxy_get(f"/account/{sub_path}", dict(request.query_params))
