"""
주식일별분봉조회 — 특정 날짜의 전체 분봉 데이터를 페이지네이션으로 수집
KIS API: FHKST03010230 (일별분봉전용, FHKST03010200은 당일전용)
- FID_INPUT_DATE_1 + FID_INPUT_HOUR_1 으로 날짜+시각 앵커 지정
- 응답 항목의 stck_bsop_date로 실제 날짜 확인
"""

import logging
import requests
from typing import List, Optional

from models.stock import (
    KisCommonHeader,
    MinuteDailyChartRequest,
    MinuteDailyChartResponse,
    MinuteDailyChartItem,
)
from services.auth import APP_KEY, APP_SECRET, BASE_URL

TR_ID = "FHKST03010230"  # 일별분봉 전용 (FHKST03010200은 당일분봉 전용)
_API_PATH = "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"


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


def get_daily_minute_chart(
    iscd: str,
    date: str,
    access_token: str,
    market_open: str = "090000",
    market_close: str = "153000",
) -> List[MinuteDailyChartItem]:
    """
    특정 날짜의 전체 분봉 데이터 조회 (페이지네이션 자동 처리)

    - FID_INPUT_DATE_1=date, FID_INPUT_HOUR_1=market_close 에서 시작
    - 응답 항목의 stck_bsop_date가 요청 날짜와 일치하는 것만 수집
    - 응답 중 요청 날짜 항목이 없으면 해당 날짜 데이터 없음(휴장일 등)으로 판단

    Returns:
        체결시간 오름차순 정렬된 MinuteDailyChartItem 리스트
    """
    all_items: List[MinuteDailyChartItem] = []
    seen_times: set[str] = set()
    current_hour = market_close

    logging.info(f"[{iscd}] {date} 분봉 조회 시작")

    while True:
        result = _fetch_page(access_token, iscd, date, current_hour)
        if result is None or not result.output2:
            break

        # 요청한 날짜와 일치하는 항목만 수집
        matched = [
            item for item in result.output2
            if item.stck_bsop_date == date and item.stck_cntg_hour not in seen_times
        ]

        # 페이지에 해당 날짜 항목이 하나도 없으면 종료
        if not matched and all_items:
            break

        all_items.extend(matched)
        seen_times.update(item.stck_cntg_hour for item in matched)

        oldest_item = result.output2[-1]
        oldest_time = oldest_item.stck_cntg_hour
        oldest_date = oldest_item.stck_bsop_date

        logging.debug(f"  {len(matched)}건 수집 (최고오래된: {oldest_date}/{oldest_time})")

        # 날짜를 넘어갔거나 장 시작 시각 이전이면 종료
        if oldest_date < date or oldest_time <= market_open:
            break

        current_hour = oldest_time

    # 장 시간 범위 필터 + 오름차순 정렬
    filtered = [
        item for item in all_items
        if market_open <= item.stck_cntg_hour <= market_close
    ]
    filtered.sort(key=lambda x: x.stck_cntg_hour)

    if filtered:
        logging.info(f"[{iscd}] {date} {len(filtered)}건 분봉 수집 완료")
    else:
        logging.warning(f"[{iscd}] {date} 분봉 데이터 없음 (휴장일 또는 조회 범위 초과)")

    return filtered
