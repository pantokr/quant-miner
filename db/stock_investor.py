import psycopg2.extras
from typing import List
from db.connection import get_connection

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_investor_trend (
    id               BIGSERIAL PRIMARY KEY,
    stock_code       VARCHAR(10) NOT NULL,
    trade_date       DATE        NOT NULL,
    prsn_ntby_qty    BIGINT,   -- 개인 순매수량
    frgn_ntby_qty    BIGINT,   -- 외국인 순매수량
    orgn_ntby_qty    BIGINT,   -- 기관 순매수량
    prsn_ntby_amt    BIGINT,   -- 개인 순매수대금
    frgn_ntby_amt    BIGINT,   -- 외국인 순매수대금
    orgn_ntby_amt    BIGINT,   -- 기관 순매수대금
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_code, trade_date)
);
"""

UPSERT_SQL = """
INSERT INTO stock_investor_trend
    (stock_code, trade_date,
     prsn_ntby_qty, frgn_ntby_qty, orgn_ntby_qty,
     prsn_ntby_amt, frgn_ntby_amt, orgn_ntby_amt)
VALUES %s
ON CONFLICT (stock_code, trade_date) DO UPDATE SET
    prsn_ntby_qty = EXCLUDED.prsn_ntby_qty,
    frgn_ntby_qty = EXCLUDED.frgn_ntby_qty,
    orgn_ntby_qty = EXCLUDED.orgn_ntby_qty,
    prsn_ntby_amt = EXCLUDED.prsn_ntby_amt,
    frgn_ntby_amt = EXCLUDED.frgn_ntby_amt,
    orgn_ntby_amt = EXCLUDED.orgn_ntby_amt;
"""


def create_table() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


def upsert_investor_trend(stock_code: str, rows: List[dict]) -> int:
    if not rows:
        return 0
    values = [
        (
            stock_code,
            f"{r['stck_bsop_date'][:4]}-{r['stck_bsop_date'][4:6]}-{r['stck_bsop_date'][6:]}",
            int(r.get('prsn_ntby_qty') or 0),
            int(r.get('frgn_ntby_qty') or 0),
            int(r.get('orgn_ntby_qty') or 0),
            int(r.get('prsn_ntby_tr_pbmn') or 0),
            int(r.get('frgn_ntby_tr_pbmn') or 0),
            int(r.get('orgn_ntby_tr_pbmn') or 0),
        )
        for r in rows
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_SQL, values)
        conn.commit()
        return len(values)
