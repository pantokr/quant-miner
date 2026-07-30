import psycopg2.extras
from typing import List, Optional
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


def _to_date(yyyymmdd: str) -> Optional[str]:
    s = (yyyymmdd or "").strip()
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 else None


def _num(value, cast=int):
    try:
        return cast(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0


def upsert_short_sell(stock_code: str, rows: List[dict]) -> int:
    """FHPST04830000 output2 기준 (ssts_* 필드)."""
    values = []
    for r in rows:
        trade_date = _to_date(r.get("stck_bsop_date", ""))
        if not trade_date:
            continue
        values.append((
            stock_code,
            trade_date,
            _num(r.get("ssts_cntg_qty")),
            _num(r.get("ssts_tr_pbmn")),
            _num(r.get("stck_clpr")),
            _num(r.get("prdy_ctrt"), float),
        ))
    if not values:
        return 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_SHORT_SQL, values)
        conn.commit()
        return len(values)


def upsert_credit(stock_code: str, rows: List[dict]) -> int:
    """FHPST04760000 output 기준 (deal_date / whol_loan_* 필드)."""
    values = []
    for r in rows:
        trade_date = _to_date(r.get("deal_date", ""))
        if not trade_date:
            continue
        values.append((
            stock_code,
            trade_date,
            _num(r.get("whol_loan_rmnd_stcn")),
            _num(r.get("whol_loan_rmnd_amt")),
            _num(r.get("whol_loan_rmnd_rate"), float),
            _num(r.get("stck_prpr")),
        ))
    if not values:
        return 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_CREDIT_SQL, values)
        conn.commit()
        return len(values)
