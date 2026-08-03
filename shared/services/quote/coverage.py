"""기간 조회의 DB 커버리지 판정.

"요청한 기간을 DB가 채우고 있는가"를 DB 값만 보고 판단하고, 모자라면 어느 구간을
더 받아야 하는지 돌려준다. 수집을 맡는 api와 중계만 하는 web/backend가 같은 기준으로
판단해야 하므로 KIS 의존 없이 따로 뒀다.

휴장일 달력이 없으므로 평일 수를 근사치로 쓴다. 그래서 판정은 "정확히 며칠이 비었나"가
아니라 "다시 받아 볼 만큼 비었나"를 본다 — 하루 이틀 차이로 KIS를 다시 때리면 조회가
느려지기만 하고 얻는 게 없다.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

_FMT = "%Y%m%d"

# 국내 증시 휴장일은 연 15일 안팎이라 영업일은 평일의 대략 94%다.
# 달력 없이 판단하므로 여유를 두고 이 비율을 "구멍 없음"의 하한으로 쓴다.
MIN_FILL_RATIO = 0.9

# 과거 쪽(요청 시작일 ~ DB 최초일자)은 이만큼 평일이 비어야 결손으로 본다.
# 설·추석 연휴가 평일을 4~5일 통째로 먹으므로, 이보다 짧은 공백은 휴장으로 본다.
MIN_GAP_WEEKDAYS = 6

# 최근 쪽(DB 최종일자 ~ 요청 종료일)은 훨씬 예민하게 본다. 어제 종가가 비어 있으면
# 바로 눈에 띄는데, 과거와 같은 잣대를 쓰면 한 주 내내 안 채워진다. 대신 이 구간은
# 청크 하나로 끝나서 싸다.
MIN_TAIL_GAP_WEEKDAYS = 1


def weekday_count(start: str, end: str) -> int:
    """[start, end] 사이 평일(월~금) 수 — 영업일 근사치."""
    if not start or not end or start > end:
        return 0
    cur = datetime.strptime(start, _FMT)
    last = datetime.strptime(end, _FMT)
    n = 0
    while cur <= last:
        if cur.weekday() < 5:
            n += 1
        cur += timedelta(days=1)
    return n


def shift(date: str, days: int) -> str:
    return (datetime.strptime(date, _FMT) + timedelta(days=days)).strftime(_FMT)


def missing_ranges(
    start: str,
    end: str,
    min_date: Optional[str],
    max_date: Optional[str],
    count: int,
    today: Optional[str] = None,
) -> List[Tuple[str, str]]:
    """요청 구간에서 API로 더 받아야 할 [시작, 종료] 구간 목록.

    Args:
        start, end        : 사용자가 요청한 기간 (YYYYMMDD)
        min_date, max_date: 그 기간 안에서 DB가 가진 최초/최종 일자 (없으면 None)
        count             : 그 기간 안의 DB 보유 건수

    Returns:
        빈 리스트면 DB만으로 충분하다는 뜻.
    """
    today = today or datetime.today().strftime(_FMT)
    # 미래 구간은 어디에도 없다. 이걸 결손으로 세면 오늘 이후를 영원히 다시 받는다.
    end = min(end, today)
    if start > end:
        return []

    if not count or not min_date or not max_date:
        return [(start, end)]

    gaps: List[Tuple[str, str]] = []
    # 경계 날짜를 구간에 포함시킨다 — 하루 겹쳐 받는 비용보다 한 칸 빠뜨리는 쪽이 나쁘다.
    if weekday_count(start, shift(min_date, -1)) >= MIN_GAP_WEEKDAYS:
        gaps.append((start, min_date))
    if weekday_count(shift(max_date, 1), end) >= MIN_TAIL_GAP_WEEKDAYS:
        gaps.append((max_date, end))
    if gaps:
        return gaps

    # 양 끝은 멀쩡한데 건수가 모자라면 중간이 뚫린 것이다. 어디가 뚫렸는지는
    # 휴장일 달력 없이 알 수 없으므로 구간을 통째로 다시 받는다 (upsert라 안전).
    if count < weekday_count(min_date, max_date) * MIN_FILL_RATIO:
        return [(start, end)]

    return []
