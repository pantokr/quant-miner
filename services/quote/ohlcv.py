"""국내주식기간별시세 조회"""
import requests
import logging
from datetime import datetime, timedelta
from typing import List

from models.stock import KisCommonHeader, PeriodOhlcvRequest, OhlcvItem, OhlcvResponse
from services.auth import APP_KEY, APP_SECRET, BASE_URL

# KIS API 1회 호출 최대 반환 레코드 수 (경험적 한계)
_PAGE_SIZE = 100


def _fetch_ohlcv_page(
    access_token: str,
    iscd: str,
    start_date: str,
    end_date: str,
    period: str,
) -> List[OhlcvItem]:
    """단일 날짜 범위 OHLCV 조회"""
    header = KisCommonHeader(
        authorization=f"Bearer {access_token}",
        appkey=APP_KEY, appsecret=APP_SECRET,
        tr_id="FHKST03010100",
    )
    req = PeriodOhlcvRequest(
        FID_INPUT_ISCD=iscd,
        FID_INPUT_DATE_1=start_date,
        FID_INPUT_DATE_2=end_date,
        FID_PERIOD_DIV_CODE=period,
    )
    res = requests.get(
        f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
        headers=header.to_dict(),
        params=req.model_dump(),
    )
    res.raise_for_status()
    result = OhlcvResponse(**res.json())
    if not result.is_success:
        logging.error(f"OHLCV 오류: {result.msg1}")
        return []
    return result.output2


def get_period_ohlcv(
    iscd: str,
    start_date: str,
    end_date: str,
    period: str = "D",
    access_token: str = None,
) -> List[OhlcvItem]:
    """
    국내주식기간별시세 단일 구간 조회

    Args:
        period: D(일) W(주) M(월) Y(년)
    """
    from services.auth.cache import get_valid_token
    token = access_token or get_valid_token()
    return _fetch_ohlcv_page(token, iscd, start_date, end_date, period)


def get_ohlcv_all(
    iscd: str,
    start_date: str,
    access_token: str = None,
    period: str = "D",
) -> List[OhlcvItem]:
    """
    start_date 부터 오늘까지 전체 OHLCV 수집 (페이지네이션 자동 처리)

    KIS API는 1회 조회에 ~100건 반환. 날짜 범위를 청크로 나눠 순방향으로 수집.

    Args:
        iscd      : 종목코드
        start_date: 수집 시작일 YYYYMMDD (ex. "19900101")
        period    : D(일) W(주) M(월) Y(년)

    Returns:
        base_date 오름차순 OhlcvItem 리스트
    """
    from services.auth.cache import get_valid_token
    token = access_token or get_valid_token()

    today = datetime.today().strftime("%Y%m%d")
    all_items: List[OhlcvItem] = []
    seen_dates: set[str] = set()

    cur_start = start_date
    chunk_years = 3  # 한 번에 3년치씩 요청

    logging.info(f"[{iscd}] OHLCV 전체 수집 시작 ({start_date} ~ {today})")

    while cur_start <= today:
        # 청크 종료일: cur_start + chunk_years년
        cur_start_dt = datetime.strptime(cur_start, "%Y%m%d")
        cur_end_dt = min(
            cur_start_dt.replace(year=cur_start_dt.year + chunk_years),
            datetime.strptime(today, "%Y%m%d"),
        )
        cur_end = cur_end_dt.strftime("%Y%m%d")

        items = _fetch_ohlcv_page(token, iscd, cur_start, cur_end, period)
        new_items = [i for i in items if i.stck_bsop_date not in seen_dates]

        if new_items:
            all_items.extend(new_items)
            seen_dates.update(i.stck_bsop_date for i in new_items)
            logging.info(f"  {cur_start}~{cur_end}: {len(new_items)}건 수집")
        else:
            logging.debug(f"  {cur_start}~{cur_end}: 데이터 없음")

        # 다음 청크: cur_end + 1일
        next_start_dt = cur_end_dt + timedelta(days=1)
        cur_start = next_start_dt.strftime("%Y%m%d")

    # base_date 오름차순 정렬
    all_items.sort(key=lambda x: x.stck_bsop_date)
    logging.info(f"[{iscd}] OHLCV 총 {len(all_items)}건 수집 완료")
    return all_items
