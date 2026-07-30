"""종목 마스터 라우터 (DB 전용).

종목명 ↔ 코드 검색. KIS 호출이 전혀 없는 순수 DB 조회이므로 게이트웨이를 거치지 않는다.
적재는 `scripts/load_stock_master.py`가 주기적으로 수행한다.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from shared.models.stock.schema import StockMasterRow
from shared.db.stock_master import get_by_codes, get_one, search_master

router = APIRouter(prefix="/stock", tags=["master (DB)"])


@router.get("/search", response_model=List[StockMasterRow])
def search(
    q: Optional[str] = Query(None, description="종목명 또는 종목코드 (부분 일치)"),
    codes: Optional[str] = Query(None, description="쉼표로 구분한 종목코드 목록"),
    limit: int = Query(20, ge=1, le=100),
):
    """종목 검색. `q`로 부분 일치 검색하거나 `codes`로 여러 종목을 한 번에 조회한다."""
    if codes:
        wanted = [c.strip() for c in codes.split(",") if c.strip()]
        return get_by_codes(wanted)
    if q:
        return search_master(q, limit=limit)
    return []


@router.get("/master/{iscd}", response_model=StockMasterRow)
def master_one(iscd: str):
    """종목코드 하나의 마스터 정보."""
    row = get_one(iscd)
    if not row:
        raise HTTPException(status_code=404, detail=f"마스터에 없는 종목코드: {iscd}")
    return row
