"""로그 라우터 (스텁).

TODO: collector/trader 실행 로그를 DB 테이블 또는 파일에서 조회해 반환.
현재는 구조만 제공한다.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Literal

router = APIRouter(prefix="/logs", tags=["logs"])


class LogEntry(BaseModel):
    ts: str                          # ISO8601
    source: str                      # "collector" | "trader" | "api"
    level: str                       # INFO/WARN/ERROR
    message: str


@router.get("", response_model=List[LogEntry])
def list_logs(
    source: Literal["collector", "trader", "api", "all"] = Query("all"),
    limit: int = Query(100, le=1000),
):
    """실행 로그 조회 (스텁 — 빈 배열).

    TODO: 로그 저장소(예: app_log 테이블) 연동.
    """
    return []
