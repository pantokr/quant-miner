import psycopg2.extras
from typing import List, Set
from db.connection import get_connection


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_minute_chart (
    id           BIGSERIAL PRIMARY KEY,
    stock_code   VARCHAR(10)  NOT NULL,
    trade_date   DATE         NOT NULL,
    trade_time   VARCHAR(6)   NOT NULL,
    open_price   BIGINT       NOT NULL,
    high_price   BIGINT       NOT NULL,
    low_price    BIGINT       NOT NULL,
    close_price  BIGINT       NOT NULL,
    volume       BIGINT       NOT NULL,
    cumul_amount BIGINT       NOT NULL,
    created_at   TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (stock_code, trade_date, trade_time)
);

-- 날짜 조회용 인덱스
CREATE INDEX IF NOT EXISTS idx_smc_code_date
    ON stock_minute_chart (stock_code, trade_date);

-- 데이터 없는 날짜 표시 테이블 (휴장일, 조회 범위 초과 등)
CREATE TABLE IF NOT EXISTS stock_minute_no_data (
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE        NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (stock_code, trade_date)
);
"""

UPSERT_SQL = """
INSERT INTO stock_minute_chart
    (stock_code, trade_date, trade_time,
     open_price, high_price, low_price, close_price,
     volume, cumul_amount)
VALUES %s
ON CONFLICT (stock_code, trade_date, trade_time) DO UPDATE SET
    open_price   = EXCLUDED.open_price,
    high_price   = EXCLUDED.high_price,
    low_price    = EXCLUDED.low_price,
    close_price  = EXCLUDED.close_price,
    volume       = EXCLUDED.volume,
    cumul_amount = EXCLUDED.cumul_amount;
"""


def create_table() -> None:
    """테이블 및 인덱스 생성"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


def upsert_minute_chart(stock_code: str, trade_date: str, rows: List[dict]) -> int:
    """
    분봉 데이터 upsert (중복 시 갱신)

    Args:
        stock_code: 종목코드 (ex. "005930")
        trade_date: 날짜 YYYYMMDD — rows의 stck_bsop_date와 일치해야 함
        rows      : MinuteDailyChartItem.model_dump() 리스트

    Returns:
        삽입/갱신된 행 수
    """
    if not rows:
        return 0

    date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"

    values = [
        (
            stock_code,
            date_str,
            row["stck_cntg_hour"],
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
    """
    해당 날짜에 분봉 데이터가 없음을 기록 (휴장일, 조회 범위 초과 등).
    다음 조회 시 재시도하지 않도록 방지.
    """
    date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO stock_minute_no_data (stock_code, trade_date)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (stock_code, date_str),
            )
        conn.commit()


def get_existing_dates(stock_code: str, start_date: str, end_date: str) -> Set[str]:
    """
    해당 종목+날짜 범위에서 이미 처리된 날짜 집합 반환.
    실제 데이터가 있는 날짜 + no_data로 표시된 날짜 모두 포함.

    Returns:
        YYYYMMDD 형식 날짜 집합
    """
    start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    end   = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT TO_CHAR(trade_date, 'YYYYMMDD')
                FROM stock_minute_chart
                WHERE stock_code = %s AND trade_date BETWEEN %s AND %s
                UNION
                SELECT DISTINCT TO_CHAR(trade_date, 'YYYYMMDD')
                FROM stock_minute_no_data
                WHERE stock_code = %s AND trade_date BETWEEN %s AND %s
                """,
                (stock_code, start, end, stock_code, start, end),
            )
            return {row[0] for row in cur.fetchall()}


def query_minute_range(
    stock_code: str,
    start_date: str, start_time: str,
    end_date: str,   end_time: str,
) -> List[dict]:
    """
    날짜+시간 범위로 분봉 데이터 조회 (시간 오름차순)
    """
    s_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    e_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    stock_code,
                    TO_CHAR(trade_date, 'YYYYMMDD') AS trade_date,
                    trade_time,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                    cumul_amount
                FROM stock_minute_chart
                WHERE stock_code = %s
                  AND (trade_date, trade_time) >= (%s::date, %s)
                  AND (trade_date, trade_time) <= (%s::date, %s)
                ORDER BY trade_date, trade_time
                """,
                (stock_code, s_date, start_time, e_date, end_time),
            )
            return [dict(row) for row in cur.fetchall()]
