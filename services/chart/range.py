"""
분봉 범위 조회 서비스

입력: 종목코드 + 시작/종료 일시
처리: DB 캐시 확인 → 없는 날짜만 API 호출 + 저장 → 전체 반환

휴장일·데이터 없는 날짜는 조회 시도 후 건너뜀.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from services.auth.cache import get_valid_token
from services.chart.minute import get_daily_minute_chart
from db.stock_minute import (
    get_existing_dates,
    mark_no_data_date,
    upsert_minute_chart,
    query_minute_range,
)


def _parse(dt_str: str) -> tuple[str, str]:
    """"YYYYMMDD HHMMSS" → (date, time)"""
    parts = dt_str.strip().split()
    if len(parts) != 2:
        raise ValueError(
            f"날짜+시간 형식이 올바르지 않습니다: '{dt_str}' (예: '20260102 090000')"
        )
    return parts[0], parts[1]


def _dates_between(start_date: str, end_date: str) -> List[str]:
    """YYYYMMDD ~ YYYYMMDD 사이 모든 날짜 반환 (양 끝 포함)"""
    cur = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    dates = []
    while cur <= end:
        dates.append(cur.strftime("%Y%m%d"))
        cur += timedelta(days=1)
    return dates


def get_minute_chart_range(
    iscd: str,
    start: str,
    end: str,
) -> List[dict]:
    """
    분봉 데이터 범위 조회.
    DB에 없는 날짜는 API에서 가져와 저장 후 반환.
    API에도 데이터가 없는 날짜(휴장일 등)는 no_data로 표시해 재조회 방지.

    Args:
        iscd : 종목코드 (ex. "005930")
        start: 시작 일시 "YYYYMMDD HHMMSS" (ex. "20260102 090000")
        end  : 종료 일시 "YYYYMMDD HHMMSS" (ex. "20260105 153000")
    """
    start_date, start_time = _parse(start)
    end_date,   end_time   = _parse(end)

    if start_date > end_date or (start_date == end_date and start_time > end_time):
        raise ValueError("start가 end보다 늦을 수 없습니다.")

    all_dates      = _dates_between(start_date, end_date)
    existing_dates = get_existing_dates(iscd, start_date, end_date)  # data + no_data 포함
    missing_dates  = [d for d in all_dates if d not in existing_dates]

    if missing_dates:
        token = get_valid_token()
        if not token:
            raise RuntimeError("토큰 발급 실패")

        for date in missing_dates:
            logging.info(f"[{iscd}] {date} DB 미존재 → API 호출")
            items = get_daily_minute_chart(iscd=iscd, date=date, access_token=token)
            if not items:
                # 데이터 없음(휴장일 등)으로 표시 → 다음 조회 시 재시도 안 함
                mark_no_data_date(iscd, date)
                continue
            rows = [item.model_dump() for item in items]
            count = upsert_minute_chart(stock_code=iscd, trade_date=date, rows=rows)
            logging.info(f"[{iscd}] {date} {count}건 저장 완료")

    return query_minute_range(
        stock_code=iscd,
        start_date=start_date, start_time=start_time,
        end_date=end_date,     end_time=end_time,
    )
