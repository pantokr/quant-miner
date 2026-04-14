"""
분봉 차트 서비스 (통합)
- 특정 날짜의 전체 분봉 데이터 수집 및 조회
- DB 캐시 처리 및 API 연동
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
import requests

from models.stock import (
    KisCommonHeader,
    MinuteDailyChartRequest,
    MinuteDailyChartResponse,
    MinuteDailyChartItem,
)
from services.auth import APP_KEY, APP_SECRET, BASE_URL
from services.auth.cache import get_valid_token
from db.stock_minute import (
    get_existing_dates,
    mark_no_data_date,
    upsert_minute_chart,
    query_minute_range,
)

TR_ID = "FHKST03010230"  # 일별분봉 전용
_API_PATH = "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"

# 장 운영 시간 고정
MARKET_OPEN = "090000"
MARKET_CLOSE = "153000"


def _fetch_page(
    access_token: str,
    iscd: str,
    date: str,
    input_hour: str,
) -> Optional[MinuteDailyChartResponse]:
    """단일 페이지 (최대 30건) 조회"""
    header = KisCommonHeader(
        authorization=f"Bearer {access_token}",
        appkey=APP_KEY,
        appsecret=APP_SECRET,
        tr_id=TR_ID,
    )
    req = MinuteDailyChartRequest(
        FID_INPUT_ISCD=iscd,
        FID_INPUT_DATE_1=date,
        FID_INPUT_HOUR_1=input_hour,
    )
    res = requests.get(
        f"{BASE_URL}{_API_PATH}",
        headers=header.to_dict(),
        params=req.model_dump(),
    )
    if res.status_code != 200:
        logging.error(f"HTTP 오류: {res.status_code} {res.text}")
        return None

    result = MinuteDailyChartResponse(**res.json())
    if not result.is_success:
        logging.error(f"API 오류: {result.msg_cd} {result.msg1}")
        return None
    return result


def get_daily_minute_chart_api(
    iscd: str,
    date: str,
    access_token: str,
) -> List[MinuteDailyChartItem]:
    """특정 날짜의 전체 분봉 데이터 API 수집"""
    all_items: List[MinuteDailyChartItem] = []
    seen_times: set[str] = set()
    current_hour = MARKET_CLOSE

    while True:
        result = _fetch_page(access_token, iscd, date, current_hour)
        if result is None or not result.output2:
            break

        matched = [
            item for item in result.output2
            if item.stck_bsop_date == date and item.stck_cntg_hour not in seen_times
        ]

        if not matched and all_items:
            break

        all_items.extend(matched)
        seen_times.update(item.stck_cntg_hour for item in matched)

        oldest_item = result.output2[-1]
        oldest_time = oldest_item.stck_cntg_hour
        oldest_date = oldest_item.stck_bsop_date

        if oldest_date < date or oldest_time <= MARKET_OPEN:
            break

        current_hour = oldest_time

    filtered = [
        item for item in all_items
        if MARKET_OPEN <= item.stck_cntg_hour <= MARKET_CLOSE
    ]
    filtered.sort(key=lambda x: x.stck_cntg_hour)
    return filtered


def get_minute_chart(iscd: str, date: str) -> List[dict]:
    """
    특정 날짜의 분봉 데이터 조회 (DB 캐시 우선)
    시간은 090000 ~ 153000 고정
    """
    # 1. DB 캐시 확인
    existing_dates = get_existing_dates(iscd, date, date)

    if date not in existing_dates:
        # 2. 캐시 없으면 API 호출
        token = get_valid_token()
        if not token:
            raise RuntimeError("토큰 발급 실패")

        logging.info(f"[{iscd}] {date} DB 미존재 → API 호출")
        items = get_daily_minute_chart_api(
            iscd=iscd, date=date, access_token=token)

        if not items:
            mark_no_data_date(iscd, date)
            return []

        rows = [item.model_dump() for item in items]
        upsert_minute_chart(stock_code=iscd, trade_date=date, rows=rows)
        logging.info(f"[{iscd}] {date} {len(rows)}건 저장 완료")

    # 3. 데이터 조회 및 반환
    return query_minute_range(
        stock_code=iscd,
        start_date=date, start_time=MARKET_OPEN,
        end_date=date,   end_time=MARKET_CLOSE,
    )
