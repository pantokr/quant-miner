"""영업일/휴장일 DB 레이어"""
import psycopg2.extras
from typing import List, Optional, Set
from db.connection import get_connection

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_holiday (
    base_date    DATE    PRIMARY KEY,
    weekday_cd   CHAR(2),      -- 01:일 02:월 ... 07:토
    is_open      BOOLEAN,      -- 개장 여부
    is_trade_day BOOLEAN,      -- 거래일 여부
    is_settle    BOOLEAN        -- 결제일 여부
);
"""

UPSERT_SQL = """
INSERT INTO stock_holiday (base_date, weekday_cd, is_open, is_trade_day, is_settle)
VALUES %s
ON CONFLICT (base_date) DO UPDATE SET
    weekday_cd   = EXCLUDED.weekday_cd,
    is_open      = EXCLUDED.is_open,
    is_trade_day = EXCLUDED.is_trade_day,
    is_settle    = EXCLUDED.is_settle;
"""


def create_table() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


def upsert_holidays(rows: List[dict]) -> int:
    """영업일 데이터 upsert (HolidayItem 리스트)"""
    if not rows:
        return 0

    values = []
    for r in rows:
        dt = r.get("bass_dt", "")
        if not dt or len(dt) < 8:
            continue
        date_str = f"{dt[:4]}-{dt[4:6]}-{dt[6:8]}"
        values.append((
            date_str,
            r.get("wday_dvsn_cd", ""),
            r.get("opnd_yn", "N") == "Y",
            r.get("tr_day_yn", "N") == "Y",
            r.get("sttl_day_yn", "N") == "Y",
        ))

    if not values:
        return 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_SQL, values)
        conn.commit()
    return len(values)


def get_trade_days(start_date: str, end_date: str) -> List[str]:
    """거래일 목록 조회 (YYYYMMDD 형식)"""
    s = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    e = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT TO_CHAR(base_date, 'YYYYMMDD')
                FROM stock_holiday
                WHERE base_date BETWEEN %s AND %s
                  AND is_trade_day = TRUE
                ORDER BY base_date
                """,
                (s, e),
            )
            return [row[0] for row in cur.fetchall()]


def is_trade_day(date: str) -> Optional[bool]:
    """특정 날짜가 거래일인지 확인. DB에 없으면 None 반환."""
    date_str = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT is_trade_day FROM stock_holiday WHERE base_date = %s",
                (date_str,),
            )
            row = cur.fetchone()
            return row[0] if row else None
