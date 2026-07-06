"""
분봉 차트 서비스 (통합)
- 특정 날짜의 전체 분봉 데이터 수집 및 조회
- DB 캐시 처리 및 API 연동
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
import requests

from shared.models.stock import (
    KisCommonHeader,
    MinuteDailyChartRequest,
    MinuteDailyChartResponse,
    MinuteDailyChartItem,
)
from shared.kis_auth import APP_KEY, APP_SECRET, BASE_URL
from shared.kis_auth import get_valid_token
from shared.db.stock_minute import (
    is_no_data_date,
    get_minute_coverage,
    mark_no_data_date,
    upsert_minute_chart,
    query_minute_range,
)

TR_ID = "FHKST03010230"  # 일별분봉 전용
_API_PATH = "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"

# 장 운영 시간 고정
MARKET_OPEN = "090000"
MARKET_CLOSE = "153000"

# 09:00~15:30 = 390분, 완전한 데이터 최소 기준 (여유 두고 380)
MIN_COMPLETE_COUNT = 380


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
    시간은 090000 ~ 153000 고정.
    캐시가 있어도 09:00~15:30 범위가 불완전하면 API 재조회.
    """
    # 1. 휴장일 등 no_data 마킹된 날짜는 재시도 없이 반환
    if is_no_data_date(iscd, date):
        return []

    # 2. DB 커버리지 확인 (시간 범위 + 건수)
    min_time, max_time, count = get_minute_coverage(iscd, date)
    is_complete = (
        min_time == MARKET_OPEN
        and max_time == MARKET_CLOSE
        and count >= MIN_COMPLETE_COUNT
    )

    if is_complete:
        return query_minute_range(
            stock_code=iscd,
            start_date=date, start_time=MARKET_OPEN,
            end_date=date,   end_time=MARKET_CLOSE,
        )

    # 3. 데이터 없거나 불완전 → API 호출
    token = get_valid_token()
    if not token:
        raise RuntimeError("토큰 발급 실패")

    if min_time is not None:
        logging.info(
            f"[{iscd}] {date} 데이터 불완전 "
            f"({min_time}~{max_time}, {count}건) → API 재조회"
        )
    else:
        logging.info(f"[{iscd}] {date} DB 미존재 → API 호출")

    items = get_daily_minute_chart_api(
        iscd=iscd, date=date, access_token=token)

    if not items:
        raise RuntimeError(f"API에서 {iscd} {date} 분봉 데이터를 가져올 수 없음")

    rows = [item.model_dump() for item in items]
    upsert_minute_chart(stock_code=iscd, trade_date=date, rows=rows)
    logging.info(f"[{iscd}] {date} {len(rows)}건 저장 완료")

    return query_minute_range(
        stock_code=iscd,
        start_date=date, start_time=MARKET_OPEN,
        end_date=date,   end_time=MARKET_CLOSE,
    )


def _dates_between(start_date: str, end_date: str) -> List[str]:
    cur = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    out = []
    while cur <= end:
        out.append(cur.strftime("%Y%m%d"))
        cur += timedelta(days=1)
    return out


def get_minute_chart_range(iscd: str, start_date: str, end_date: str) -> List[dict]:
    """
    특정 종목의 특정 기간 [start_date, end_date] 분봉 전체 조회.

    각 날짜를 DB 캐시 우선으로 확보(없으면 FHKST03010230 API 수집·적재)한 뒤,
    기간 전체를 시간 오름차순으로 합쳐서 반환한다. 휴장/무데이터 날짜는 no_data로
    마킹해 다음 호출부터 재조회하지 않는다.

    Returns: MinuteChartRow 형태 dict 리스트 (stock_code, trade_date, trade_time, ...)
    """
    for date in _dates_between(start_date, end_date):
        if is_no_data_date(iscd, date):
            continue
        try:
            get_minute_chart(iscd, date)
        except RuntimeError:
            # API에서도 데이터 없음(휴장 등) → 마킹 후 다음 날짜로
            mark_no_data_date(iscd, date)
            logging.info(f"[{iscd}] {date} 무데이터(휴장 등) — 스킵 마킹")

    return query_minute_range(
        stock_code=iscd,
        start_date=start_date, start_time=MARKET_OPEN,
        end_date=end_date,     end_time=MARKET_CLOSE,
    )
