"""분봉 누락 구간 채우기.

shared.services.chart.minute(DB 캐시 + 커버리지 판정)와 shared.db.stock_minute의
기존 로직을 재사용한다. 이미 수집됐거나 휴장일로 마킹된 날짜는 건너뛴다.
"""
import logging
from datetime import datetime, timedelta
from typing import List

from shared.services.chart.minute import get_minute_chart
from shared.db.stock_minute import get_existing_dates

logger = logging.getLogger(__name__)


def _dates_between(start: str, end: str) -> List[str]:
    cur = datetime.strptime(start, "%Y%m%d")
    end_dt = datetime.strptime(end, "%Y%m%d")
    out = []
    while cur <= end_dt:
        out.append(cur.strftime("%Y%m%d"))
        cur += timedelta(days=1)
    return out


def missing_dates(iscd: str, start: str, end: str) -> List[str]:
    """DB에 아직 없는(수집/휴장 마킹 모두 없는) 날짜 목록."""
    existing = set(get_existing_dates(iscd, start, end))
    return [d for d in _dates_between(start, end) if d not in existing]


def fill_minute_gaps(iscd: str, start: str, end: str) -> int:
    """누락 날짜를 순회하며 분봉 수집(get_minute_chart가 캐시/휴장 처리 + DB 적재).

    Returns: 실제 시도한(채운) 날짜 수.
    """
    targets = missing_dates(iscd, start, end)
    logger.info(f"[{iscd}] 누락 {len(targets)}일 채우기 시작 ({start}~{end})")
    filled = 0
    for d in targets:
        try:
            get_minute_chart(iscd=iscd, date=d)  # 내부에서 캐시/휴장/API/DB 처리
            filled += 1
        except RuntimeError as e:
            logger.warning(f"[{iscd}] {d} 수집 실패: {e}")
    logger.info(f"[{iscd}] 채우기 완료: {filled}/{len(targets)}일")
    return filled
