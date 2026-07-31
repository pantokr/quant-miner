"""일일 분봉의 빈 시간대 채우기 (조회 시점 전용).

체결이 없는 분에는 KIS가 봉을 아예 내려주지 않는다. 그대로 그리면 차트의 X축이
듬성듬성해지고 시간 간격이 왜곡되므로, 09:00~15:30 매 분을 채워서 돌려준다.

채우는 방법
    1) 순차탐색(forward fill)  — 직전 봉의 종가를 그 분의 시·고·저·종가로 쓴다.
    2) 역방향 순차탐색(backward fill) — 장 초반처럼 앞에 직전 봉이 없으면
       뒤에 처음 나오는 실제 봉의 시가를 쓴다.

거래량만 예외로 0을 넣는다. 체결이 없어서 봉이 없는 것이므로 직전 거래량을 복사하면
거래량 차트가 실제보다 부풀려진다. 누적거래대금은 누적값이라 직전 값을 유지한다.

DB에는 저장하지 않는다 — 채운 값은 실제 체결이 아니므로 조회 응답에만 얹고
`is_filled=True`로 표시해 원본과 구분할 수 있게 한다.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List

MARKET_OPEN = "090000"
MARKET_CLOSE = "153000"

# DB의 ts는 KST 벽시계 기준이고 서버 컨테이너는 UTC로 도는 경우가 많아
# "지금 몇 시인가"를 절대 로컬 시각으로 판단하면 안 된다.
KST = timezone(timedelta(hours=9))

# KIS 분봉은 실시간보다 1~2분 늦게 채워진다. 그만큼은 없어도 정상으로 본다.
FEED_LAG_MINUTES = 3


def now_kst() -> datetime:
    return datetime.now(KST)


def expected_last_minute(trade_date: str, now: datetime | None = None) -> str:
    """
    그 날짜에 '지금 시점에 존재해야 할' 마지막 분봉 시각(HHMMSS).

    과거 날짜면 장 마감(15:30). 오늘이면 현재 시각까지만 기대한다 —
    11시에 조회하면서 15:30까지 있기를 기대하면 매번 불완전 판정이 난다.
    장 시작 전이면 빈 문자열(기대할 봉이 없음).
    """
    now = now or now_kst()
    if trade_date != now.strftime("%Y%m%d"):
        return MARKET_CLOSE

    current = now - timedelta(minutes=FEED_LAG_MINUTES)
    hhmm = current.strftime("%H%M00")
    if hhmm < MARKET_OPEN:
        return ""
    return min(hhmm, MARKET_CLOSE)


def market_minutes(open_time: str = MARKET_OPEN, close_time: str = MARKET_CLOSE) -> List[str]:
    """장 운영 시간의 매 분 HHMMSS 목록 (09:00:00 ~ 15:30:00 = 391개)."""
    start = int(open_time[:2]) * 60 + int(open_time[2:4])
    end = int(close_time[:2]) * 60 + int(close_time[2:4])
    return [f"{m // 60:02d}{m % 60:02d}00" for m in range(start, end + 1)]


def fill_minute_gaps(
    rows: List[Dict],
    trade_date: str = "",
    open_time: str = MARKET_OPEN,
    close_time: str = "",
) -> List[Dict]:
    """
    분봉 리스트의 빈 시간대를 채운다.

    Args:
        rows:       query_minute_range가 돌려준 dict 리스트 (trade_time 오름차순 가정)
        trade_date: 채워 넣을 행의 trade_date. 비우면 rows에서 가져온다.
        close_time: 어디까지 채울지. 비우면 그 날짜 기준으로 자동 판정한다
                    (오늘이면 현재 시각까지, 과거면 15:30까지).
                    아직 오지 않은 시각까지 평선을 그려 넣지 않기 위함.

    Returns:
        open_time~close_time의 매 분이 존재하는 리스트. 채운 행은 is_filled=True.
    """
    if not rows:
        return []

    date_for_bound = trade_date or str(rows[0].get("trade_date", ""))
    if not close_time:
        close_time = expected_last_minute(date_for_bound) or MARKET_CLOSE

    by_time = {str(r["trade_time"]): r for r in rows}
    stock_code = rows[0].get("stock_code", "")
    date = trade_date or str(rows[0].get("trade_date", ""))

    minutes = market_minutes(open_time, close_time)

    # 1) 순차탐색 — 직전 실제 봉을 들고 가며 빈 자리를 메운다
    out: List[Dict] = []
    prev: Dict | None = None
    for t in minutes:
        actual = by_time.get(t)
        if actual is not None:
            row = dict(actual)
            row["is_filled"] = False
            prev = row
            out.append(row)
            continue

        if prev is None:
            # 앞에 채울 값이 없음 — 2)에서 역방향으로 메운다
            out.append({
                "stock_code": stock_code,
                "trade_date": date,
                "trade_time": t,
                "open_price": None, "high_price": None,
                "low_price": None, "close_price": None,
                "volume": 0, "cumul_amount": 0,
                "is_filled": True,
            })
            continue

        price = prev["close_price"]
        out.append({
            "stock_code": stock_code,
            "trade_date": date,
            "trade_time": t,
            "open_price": price, "high_price": price,
            "low_price": price, "close_price": price,
            "volume": 0,
            "cumul_amount": prev["cumul_amount"],
            "is_filled": True,
        })

    # 2) 역방향 순차탐색 — 장 초반의 빈 구간을 뒤쪽 첫 실제 봉의 시가로 메운다
    next_price = None
    next_cumul = 0
    for row in reversed(out):
        if row["close_price"] is None:
            row["open_price"] = row["high_price"] = row["low_price"] = row["close_price"] = next_price
            row["cumul_amount"] = next_cumul
        else:
            next_price = row["open_price"]
            next_cumul = row["cumul_amount"]

    # 하루 전체가 비어 있는 비정상 입력 방어
    return [r for r in out if r["close_price"] is not None]


def missing_minutes(rows: List[Dict], open_time: str = MARKET_OPEN,
                    close_time: str = MARKET_CLOSE) -> List[str]:
    """채우기 전 누락된 시각 목록 (진단·로깅용)."""
    have = {str(r["trade_time"]) for r in rows}
    return [t for t in market_minutes(open_time, close_time) if t not in have]
