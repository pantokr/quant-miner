"""분봉 저장/조회 — TimescaleDB 하이퍼테이블.

stock_minute_chart 는 (stock_code, ts) 기준 하이퍼테이블이며 ts 로 파티셔닝 + 압축한다.
외부 계약(서비스/API/프론트)은 그대로 유지하기 위해, 조회 시 ts에서 trade_date/trade_time을
파생해 반환한다(기존 MinuteChartRow 형태 동일).

ts 는 KST 벽시계 기준 TIMESTAMP(무 tz). KRX 전용이라 tz 변환 혼선을 피한다.
"""
import logging
import psycopg2.extras
from datetime import datetime, timedelta
from typing import List, Set, Optional, Tuple

from shared.db.connection import get_connection

# ── 스키마 (하이퍼테이블 + 압축) ─────────────────────────────
CREATE_TABLE_SQL = """
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS stock_minute_chart (
    stock_code   VARCHAR(10) NOT NULL,
    ts           TIMESTAMP   NOT NULL,   -- 봉 시각 (KST 벽시계)
    open_price   BIGINT      NOT NULL,
    high_price   BIGINT      NOT NULL,
    low_price    BIGINT      NOT NULL,
    close_price  BIGINT      NOT NULL,
    volume       BIGINT      NOT NULL,
    cumul_amount BIGINT      NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (stock_code, ts)
);

SELECT create_hypertable('stock_minute_chart', 'ts', if_not_exists => TRUE);

ALTER TABLE stock_minute_chart SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'stock_code',
    timescaledb.compress_orderby   = 'ts DESC'
);

SELECT add_compression_policy('stock_minute_chart', INTERVAL '7 days', if_not_exists => TRUE);

-- 데이터 없는 날짜(휴장 등) 표시 테이블 (소규모, 일반 테이블)
CREATE TABLE IF NOT EXISTS stock_minute_no_data (
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE        NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (stock_code, trade_date)
);
"""

UPSERT_SQL = """
INSERT INTO stock_minute_chart
    (stock_code, ts, open_price, high_price, low_price, close_price, volume, cumul_amount)
VALUES %s
ON CONFLICT (stock_code, ts) DO UPDATE SET
    open_price   = EXCLUDED.open_price,
    high_price   = EXCLUDED.high_price,
    low_price    = EXCLUDED.low_price,
    close_price  = EXCLUDED.close_price,
    volume       = EXCLUDED.volume,
    cumul_amount = EXCLUDED.cumul_amount;
"""

# ── 연속집계 (5분봉 롤업) ────────────────────────────────────
_CAGG_5M_SQL = """
CREATE MATERIALIZED VIEW IF NOT EXISTS stock_minute_5m
WITH (timescaledb.continuous) AS
SELECT
    stock_code,
    time_bucket('5 minutes', ts) AS bucket,
    first(open_price, ts)  AS open_price,
    max(high_price)        AS high_price,
    min(low_price)         AS low_price,
    last(close_price, ts)  AS close_price,
    sum(volume)            AS volume,
    last(cumul_amount, ts) AS cumul_amount
FROM stock_minute_chart
GROUP BY stock_code, bucket
WITH NO DATA;
"""

_CAGG_5M_POLICY_SQL = """
SELECT add_continuous_aggregate_policy('stock_minute_5m',
    start_offset      => INTERVAL '2 days',
    end_offset        => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists     => TRUE);
"""


def _ts(date: str, time: str) -> str:
    """YYYYMMDD + HHMMSS → 'YYYY-MM-DD HH:MM:SS'."""
    return f"{date[:4]}-{date[4:6]}-{date[6:]} {time[:2]}:{time[2:4]}:{time[4:6]}"


def _day_bounds(date: str) -> Tuple[str, str]:
    """해당 날짜의 [00:00, 다음날 00:00) 경계 timestamp 문자열."""
    d = datetime.strptime(date, "%Y%m%d")
    nxt = d + timedelta(days=1)
    return d.strftime("%Y-%m-%d 00:00:00"), nxt.strftime("%Y-%m-%d 00:00:00")


def _create_continuous_aggregates() -> None:
    """5분봉 연속집계 + 갱신 정책 (CAGG는 트랜잭션 밖에서 생성)."""
    conn = get_connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(_CAGG_5M_SQL)
            cur.execute(_CAGG_5M_POLICY_SQL)
    finally:
        conn.close()


def create_table() -> None:
    """하이퍼테이블/압축/no_data 테이블 생성 + 연속집계(best-effort)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()
    try:
        _create_continuous_aggregates()
    except Exception as e:  # 연속집계 실패가 기동을 막지 않도록
        logging.warning(f"연속집계(stock_minute_5m) 생성 건너뜀: {e}")


def upsert_minute_chart(stock_code: str, trade_date: str, rows: List[dict]) -> int:
    """분봉 upsert. rows는 MinuteDailyChartItem.model_dump() 리스트."""
    if not rows:
        return 0
    values = [
        (
            stock_code,
            _ts(trade_date, row["stck_cntg_hour"]),
            int(row["stck_oprc"]),
            int(row["stck_hgpr"]),
            int(row["stck_lwpr"]),
            int(row["stck_prpr"]),
            int(row["cntg_vol"]),
            int(row["acml_tr_pbmn"]),
        )
        for row in rows
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_SQL, values)
        conn.commit()
        return len(values)


def mark_no_data_date(stock_code: str, trade_date: str) -> None:
    """해당 날짜에 분봉 데이터 없음 기록(휴장 등) — 재조회 방지."""
    date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO stock_minute_no_data (stock_code, trade_date)
                VALUES (%s, %s) ON CONFLICT DO NOTHING
                """,
                (stock_code, date_str),
            )
        conn.commit()


def is_no_data_date(stock_code: str, trade_date: str) -> bool:
    date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM stock_minute_no_data WHERE stock_code = %s AND trade_date = %s",
                (stock_code, date_str),
            )
            return cur.fetchone() is not None


def get_minute_coverage(stock_code: str, trade_date: str) -> Tuple[Optional[str], Optional[str], int]:
    """해당 날짜의 (MIN HHMMSS, MAX HHMMSS, COUNT). 없으면 (None, None, 0)."""
    d0, d1 = _day_bounds(trade_date)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT to_char(MIN(ts), 'HH24MISS'), to_char(MAX(ts), 'HH24MISS'), COUNT(*)
                FROM stock_minute_chart
                WHERE stock_code = %s AND ts >= %s AND ts < %s
                """,
                (stock_code, d0, d1),
            )
            row = cur.fetchone()
            if row and row[0] is not None:
                return (row[0], row[1], row[2])
            return (None, None, 0)


def get_existing_dates(stock_code: str, start_date: str, end_date: str) -> Set[str]:
    """수집됨 + no_data 마킹된 날짜(YYYYMMDD) 집합."""
    d0, _ = _day_bounds(start_date)
    _, d1 = _day_bounds(end_date)
    s = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    e = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT to_char(ts, 'YYYYMMDD')
                FROM stock_minute_chart
                WHERE stock_code = %s AND ts >= %s AND ts < %s
                UNION
                SELECT DISTINCT to_char(trade_date, 'YYYYMMDD')
                FROM stock_minute_no_data
                WHERE stock_code = %s AND trade_date BETWEEN %s AND %s
                """,
                (stock_code, d0, d1, stock_code, s, e),
            )
            return {row[0] for row in cur.fetchall()}


def query_minute_range(
    stock_code: str,
    start_date: str, start_time: str,
    end_date: str,   end_time: str,
) -> List[dict]:
    """ts 범위 조회. 반환은 기존 계약대로 trade_date/trade_time 파생."""
    start_ts = _ts(start_date, start_time)
    end_ts = _ts(end_date, end_time)
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    stock_code,
                    to_char(ts, 'YYYYMMDD') AS trade_date,
                    to_char(ts, 'HH24MISS') AS trade_time,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                    cumul_amount
                FROM stock_minute_chart
                WHERE stock_code = %s AND ts >= %s AND ts <= %s
                ORDER BY ts
                """,
                (stock_code, start_ts, end_ts),
            )
            return [dict(row) for row in cur.fetchall()]
