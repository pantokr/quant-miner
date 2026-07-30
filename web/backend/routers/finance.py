"""재무/기업정보 라우터 (api 게이트웨이 중계).

재무제표·배당·추정실적·종목기본정보는 api 게이트웨이(`api/routers/finance.py`)가
KIS 호출과 DB 적재를 모두 담당한다. backend는 경로와 쿼리 파라미터를 그대로 넘겨
중계만 하므로, 게이트웨이에 엔드포인트가 추가되어도 여기를 고칠 필요가 없다.
"""
from fastapi import APIRouter, Request

from web.backend.gateway import proxy_get

router = APIRouter(prefix="/finance", tags=["finance (proxy→api)"])


@router.get("/{sub_path:path}")
def finance_proxy(sub_path: str, request: Request):
    """/finance/** 전체를 게이트웨이로 중계 (재무제표·배당·추정실적·기본정보)."""
    return proxy_get(f"/finance/{sub_path}", dict(request.query_params))
