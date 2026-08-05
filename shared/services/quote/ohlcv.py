"""국내주식기간별시세 조회"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from shared.models.stock import KisCommonHeader, PeriodOhlcvRequest, OhlcvItem, OhlcvResponse
from shared.config import KIS_TIMEOUT
from shared.kis_auth import APP_KEY, APP_SECRET, BASE_URL
from shared.kis_auth import get_valid_token
from shared.db.stock_ohlcv import get_ohlcv_coverage, upsert_ohlcv
from shared.services.quote.coverage import missing_ranges

# KIS API 1회 호출 최대 반환 레코드 수 (경험적 한계)
_PAGE_SIZE = 100

# 요청 구간이 100건을 넘으면 KIS는 최근 100건만 주고 앞쪽을 조용히 버린다.
# 그래서 period별로 100건에 못 미치도록 달력 일수를 잘라 순방향으로 이어 받는다.
# (일봉 120일 ≈ 영업일 85일, 주봉 600일 ≈ 85주, 월봉 2500일 ≈ 82개월)
_CHUNK_DAYS: Dict[str, int] = {"D": 120, "W": 600, "M": 2500, "Y": 30000}
_DEFAULT_CHUNK_DAYS = 120

# 이만큼 연속으로 빈 청크가 나오면 상장 전 구간에 들어선 것으로 보고 멈춘다.
_EMPTY_CHUNK_LIMIT = 3


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
        timeout=KIS_TIMEOUT,
    )
    # 예전에는 raise_for_status()로 끊었다. KIS가 오류 본문(rt_cd/msg1)을 담아 주는데도
    # 그게 사라지고 라우터에서 미처리 예외 → 화면에는 원인 없는 500만 남았다.
    if res.status_code != 200:
        logging.error(f"OHLCV HTTP 오류: [{res.status_code}] {res.text[:200]}")
        return []
    result = OhlcvResponse(**res.json())
    if not result.is_success:
        logging.error(f"OHLCV 오류: {result.msg_cd} {result.msg1}")
        return []
    return result.output2


def _collect_range(
    token: str,
    iscd: str,
    start_date: str,
    end_date: str,
    period: str,
) -> List[OhlcvItem]:
    """[start_date, end_date]를 청크로 나눠 수집 (일자 오름차순, 중복 제거).

    최근 쪽부터 거슬러 올라간다. KIS는 구간이 넓으면 최근 100건만 주므로 방향 자체는
    상관없지만, 상장 전까지 내려가면 빈 응답이 이어지는 것으로 끝을 알 수 있다.
    1990년부터 순방향으로 훑으면 상장 전 20년을 헛되이 두드리게 된다.
    """
    chunk = timedelta(days=_CHUNK_DAYS.get(period, _DEFAULT_CHUNK_DAYS))
    first = datetime.strptime(start_date, "%Y%m%d")
    cur_end = datetime.strptime(end_date, "%Y%m%d")

    items: List[OhlcvItem] = []
    seen: set[str] = set()
    empty_streak = 0

    while cur_end >= first:
        cur_start = max(cur_end - chunk + timedelta(days=1), first)
        page = _fetch_ohlcv_page(
            token, iscd,
            cur_start.strftime("%Y%m%d"), cur_end.strftime("%Y%m%d"), period,
        )
        fresh = [i for i in page if i.stck_bsop_date and i.stck_bsop_date not in seen]
        items.extend(fresh)
        seen.update(i.stck_bsop_date for i in fresh)

        # 상장 전이면 계속 빈 응답이다. 거래정지로 한두 청크가 빌 수는 있으니
        # 연속으로 비었을 때만 끝으로 본다.
        empty_streak = 0 if page else empty_streak + 1
        if empty_streak >= _EMPTY_CHUNK_LIMIT:
            break

        cur_end = cur_start - timedelta(days=1)

    items.sort(key=lambda x: x.stck_bsop_date)
    return items


def get_period_ohlcv(
    iscd: str,
    start_date: str,
    end_date: str,
    period: str = "D",
    access_token: str = None,
    save: bool = False,
) -> List[OhlcvItem]:
    """
    국내주식기간별시세 구간 조회

    Args:
        period: D(일) W(주) M(월) Y(년)
        save: True 시 DB 적재
    """
    token = access_token or get_valid_token()
    items = _collect_range(token, iscd, start_date, end_date, period)
    if save and items:
        upsert_ohlcv(iscd, period, [i.model_dump() for i in items])
    return items


# 이미 시도한 구간을 잠깐 기억한다. 상장 전 구간처럼 KIS에도 없는 기간이 요청에 섞이면
# 커버리지는 영원히 모자란 상태로 남아, 없으면 조회할 때마다 KIS를 다시 때리게 된다.
_ATTEMPT_TTL = timedelta(minutes=10)
_attempts: Dict[Tuple[str, str, str, str], datetime] = {}


def _should_attempt(key: Tuple[str, str, str, str]) -> bool:
    now = datetime.now()
    last = _attempts.get(key)
    if last and now - last < _ATTEMPT_TTL:
        return False
    _attempts[key] = now
    return True


def ensure_ohlcv_coverage(
    iscd: str,
    start_date: str,
    end_date: str,
    period: str = "D",
    access_token: str = None,
    save: bool = True,
) -> int:
    """요청 구간 중 DB에 빠진 부분만 KIS에서 받아 적재하고, 새로 받은 건수를 반환.

    DB에 있는 만큼만 돌려주면 "1년을 조회했는데 석 달만 나온다"가 된다. 그렇다고
    매번 전 구간을 다시 받으면 느리므로, 앞/뒤로 모자란 구간만 골라서 채운다.
    """
    gaps = missing_ranges(
        start_date, end_date,
        *get_ohlcv_coverage(iscd, period, start_date, end_date),
    )
    if not gaps:
        return 0

    token = access_token or get_valid_token()
    if not token:
        raise RuntimeError("KIS 토큰 발급 실패")

    filled = 0
    for gap_start, gap_end in gaps:
        if not _should_attempt((iscd, period, gap_start, gap_end)):
            logging.debug(f"[{iscd}] {gap_start}~{gap_end} 최근 시도함 — 재수집 생략")
            continue
        items = _collect_range(token, iscd, gap_start, gap_end, period)
        logging.info(
            f"[{iscd}] {period}봉 결손 {gap_start}~{gap_end} → {len(items)}건 수집"
        )
        if items and save:
            upsert_ohlcv(iscd, period, [i.model_dump() for i in items])
        filled += len(items)

    return filled


def get_ohlcv_all(
    iscd: str,
    start_date: str,
    access_token: str = None,
    period: str = "D",
    save: bool = False,
) -> List[OhlcvItem]:
    """
    start_date 부터 오늘까지 전체 OHLCV 수집 (페이지네이션 자동 처리)

    예전에는 3년씩 끊어 요청했는데, KIS가 한 번에 100건까지만 주므로 일봉 기준
    청크마다 뒤쪽 100일만 오고 나머지 2년 반이 조용히 비었다. 청크 크기는
    _CHUNK_DAYS가 period별로 100건 미만이 되도록 정한다.

    Args:
        iscd      : 종목코드
        start_date: 수집 시작일 YYYYMMDD (ex. "19900101")
        period    : D(일) W(주) M(월) Y(년)

    Returns:
        base_date 오름차순 OhlcvItem 리스트
    """
    token = access_token or get_valid_token()
    if not token:
        # 토큰 없이 부르면 헤더가 "Bearer None"이 되어 KIS가 거절하고,
        # 그 거절이 라우터까지 예외로 올라가 500이 된다. 여기서 끊는다.
        raise RuntimeError("KIS 토큰 발급 실패 (1분 1회 제한이거나 앱키 문제)")
    today = datetime.today().strftime("%Y%m%d")

    logging.info(f"[{iscd}] OHLCV 전체 수집 시작 ({start_date} ~ {today})")
    all_items = _collect_range(token, iscd, start_date, today, period)
    logging.info(f"[{iscd}] OHLCV 총 {len(all_items)}건 수집 완료")
    if save and all_items:
        upsert_ohlcv(iscd, period, [i.model_dump() for i in all_items])
    return all_items
