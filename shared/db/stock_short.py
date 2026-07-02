import psycopg2.extras
from typing import List
from shared.db.connection import get_connection

CREATE_SHORT_SQL = """
CREATE TABLE IF NOT EXISTS stock_short_sell (
    id           BIGSERIAL PRIMARY KEY,
    stock_code   VARCHAR(10) NOT NULL,
    trade_date   DATE        NOT NULL,
    short_volume BIGINT,
    short_amount BIGINT,
    close_price  BIGINT,
    change_rate  NUMERIC(8,2),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_code, trade_date)
);
"""

CREATE_CREDIT_SQL = """
CREATE TABLE IF NOT EXISTS stock_credit (
    id             BIGSERIAL PRIMARY KEY,
    stock_code     VARCHAR(10) NOT NULL,
    trade_date     DATE        NOT NULL,
    credit_qty     BIGINT,
    credit_amount  BIGINT,
    credit_rate    NUMERIC(8,2),
    close_price    BIGINT,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_code, trade_date)
);
"""

UPSERT_SHORT_SQL = """
INSERT INTO stock_short_sell (stock_code, trade_date, short_volume, short_amount, close_price, change_rate)
VALUES %s
ON CONFLICT (stock_code, trade_date) DO UPDATE SET
    short_volume = EXCLUDED.short_volume,
    short_amount = EXCLUDED.short_amount,
    close_price  = EXCLUDED.close_price,
    change_rate  = EXCLUDED.change_rate;
"""

UPSERT_CREDIT_SQL = """
INSERT INTO stock_credit (stock_code, trade_date, credit_qty, credit_amount, credit_rate, close_price)
VALUES %s
ON CONFLICT (stock_code, trade_date) DO UPDATE SET
    credit_qty    = EXCLUDED.credit_qty,
    credit_amount = EXCLUDED.credit_amount,
    credit_rate   = EXCLUDED.credit_rate,
    close_price   = EXCLUDED.close_price;
"""


def create_tables() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_SHORT_SQL)
            cur.execute(CREATE_CREDIT_SQL)
        conn.commit()


def upsert_short_sell(stock_code: str, rows: List[dict]) -> int:
    if not rows:
        return 0
    values = [
        (
            stock_code,
            f"{r['stck_bsop_date'][:4]}-{r['stck_bsop_date'][4:6]}-{r['stck_bsop_date'][6:]}",
            int(r.get('smtn_smvl') or 0),
            int(r.get('smtn_tr_pbmn') or 0),
            int(r.get('stck_prpr') or 0),
            float(r.get('prdy_ctrt') or 0),
        )
        for r in rows
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_SHORT_SQL, values)
        conn.commit()
        return len(values)


def upsert_credit(stock_code: str, rows: List[dict]) -> int:
    if not rows:
        return 0
    values = [
        (
            stock_code,
            f"{r['stck_bsop_date'][:4]}-{r['stck_bsop_date'][4:6]}-{r['stck_bsop_date'][6:]}",
            int(r.get('crdt_rmnd_qty') or 0),
            int(r.get('crdt_rmnd_amt') or 0),
            float(r.get('crdt_rmnd_rate') or 0),
            int(r.get('stck_prpr') or 0),
        )
        for r in rows
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_CREDIT_SQL, values)
        conn.commit()
        return len(values)
