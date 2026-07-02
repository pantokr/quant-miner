import psycopg2.extras
from typing import List
from shared.db.connection import get_connection

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_ohlcv (
    id          BIGSERIAL PRIMARY KEY,
    stock_code  VARCHAR(10) NOT NULL,
    period_type CHAR(1)     NOT NULL,   -- D/W/M/Y
    base_date   DATE        NOT NULL,
    open_price  BIGINT      NOT NULL,
    high_price  BIGINT      NOT NULL,
    low_price   BIGINT      NOT NULL,
    close_price BIGINT      NOT NULL,
    volume      BIGINT      NOT NULL,
    amount      BIGINT      NOT NULL,
    change_sign CHAR(1),                -- 1:상한 2:상승 3:보합 4:하한 5:하락
    change_val  BIGINT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_code, period_type, base_date)
);
"""

UPSERT_SQL = """
INSERT INTO stock_ohlcv
    (stock_code, period_type, base_date,
     open_price, high_price, low_price, close_price,
     volume, amount, change_sign, change_val)
VALUES %s
ON CONFLICT (stock_code, period_type, base_date) DO UPDATE SET
    open_price  = EXCLUDED.open_price,
    high_price  = EXCLUDED.high_price,
    low_price   = EXCLUDED.low_price,
    close_price = EXCLUDED.close_price,
    volume      = EXCLUDED.volume,
    amount      = EXCLUDED.amount,
    change_sign = EXCLUDED.change_sign,
    change_val  = EXCLUDED.change_val;
"""


def create_table() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


def upsert_ohlcv(stock_code: str, period_type: str, rows: List[dict]) -> int:
    if not rows:
        return 0
    values = [
        (
            stock_code,
            period_type,
            f"{r['stck_bsop_date'][:4]}-{r['stck_bsop_date'][4:6]}-{r['stck_bsop_date'][6:]}",
            int(r['stck_oprc'] or 0),
            int(r['stck_hgpr'] or 0),
            int(r['stck_lwpr'] or 0),
            int(r['stck_clpr'] or 0),
            int(r['acml_vol'] or 0),
            int(r['acml_tr_pbmn'] or 0),
            r.get('prdy_vrss_sign', ''),
            int(r.get('prdy_vrss') or 0),
        )
        for r in rows
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_SQL, values)
        conn.commit()
        return len(values)


def query_ohlcv(stock_code: str, period_type: str, start_date: str, end_date: str) -> List[dict]:
    """DB에서 기간별 OHLCV 조회 (base_date 오름차순). OhlcvRow 스키마와 동일 형태 반환."""
    s = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    e = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    TO_CHAR(base_date, 'YYYYMMDD') AS date,
                    open_price  AS open,
                    high_price  AS high,
                    low_price   AS low,
                    close_price AS close,
                    volume,
                    amount,
                    COALESCE(change_sign, '') AS change_sign,
                    COALESCE(change_val, 0)   AS change_val
                FROM stock_ohlcv
                WHERE stock_code = %s AND period_type = %s
                  AND base_date BETWEEN %s AND %s
                ORDER BY base_date ASC
                """,
                (stock_code, period_type, s, e),
            )
            return [dict(r) for r in cur.fetchall()]
