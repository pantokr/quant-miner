"""종목기본정보 / 배당 / 추정실적 DB 레이어"""
import json
import psycopg2.extras
from typing import Any, Dict, List, Optional
from db.connection import get_connection

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_info (
    stock_code       VARCHAR(10)  PRIMARY KEY,
    name             VARCHAR(100),
    market           VARCHAR(10),
    sector           VARCHAR(100),
    listed_shares    BIGINT,
    listed_date      DATE,
    isin             VARCHAR(20),
    settlement_month VARCHAR(4),
    raw              JSONB,
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stock_dividend (
    id               BIGSERIAL   PRIMARY KEY,
    stock_code       VARCHAR(10) NOT NULL,
    record_date      DATE        NOT NULL,
    amount_per_share VARCHAR(20),
    dividend_type    VARCHAR(20),
    pay_date         DATE,
    raw              JSONB,
    UNIQUE (stock_code, record_date)
);

CREATE TABLE IF NOT EXISTS stock_estimate (
    id           BIGSERIAL   PRIMARY KEY,
    stock_code   VARCHAR(10) NOT NULL,
    period       VARCHAR(6)  NOT NULL,  -- YYYYMM
    data         JSONB       NOT NULL,
    updated_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_code, period)
);
"""


def create_tables() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


# ── 종목기본정보 ───────────────────────────────────────────

def upsert_stock_info(stock_code: str, raw: Dict[str, Any]) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO stock_info
                    (stock_code, name, market, sector,
                     listed_shares, listed_date, isin, settlement_month, raw)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (stock_code) DO UPDATE SET
                    name             = EXCLUDED.name,
                    market           = EXCLUDED.market,
                    sector           = EXCLUDED.sector,
                    listed_shares    = EXCLUDED.listed_shares,
                    listed_date      = EXCLUDED.listed_date,
                    isin             = EXCLUDED.isin,
                    settlement_month = EXCLUDED.settlement_month,
                    raw              = EXCLUDED.raw,
                    updated_at       = NOW()
                """,
                (
                    stock_code,
                    raw.get("prdt_abrv_name") or raw.get("prdt_eng_name", ""),
                    raw.get("mket_id_cd", ""),
                    raw.get("scrt_grp_cls_code", ""),
                    _to_int(raw.get("lstg_stqty")),
                    _to_date(raw.get("lstg_dt")),
                    raw.get("std_pdno", ""),
                    raw.get("setl_mmdd", ""),
                    json.dumps(raw, ensure_ascii=False),
                ),
            )
        conn.commit()


def get_stock_info(stock_code: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM stock_info WHERE stock_code = %s",
                (stock_code,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


# ── 배당 ──────────────────────────────────────────────────

def upsert_dividends(stock_code: str, rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0
    values = []
    for r in rows:
        record_date = _to_date(r.get("record_date") or r.get("bass_dt", ""))
        if not record_date:
            continue
        values.append((
            stock_code,
            record_date,
            r.get("per_sto_divi_amt", ""),
            r.get("divi_kind", ""),
            _to_date(r.get("divi_pay_dt")),
            json.dumps(r, ensure_ascii=False),
        ))
    if not values:
        return 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO stock_dividend
                    (stock_code, record_date, amount_per_share, dividend_type, pay_date, raw)
                VALUES %s
                ON CONFLICT (stock_code, record_date) DO UPDATE SET
                    amount_per_share = EXCLUDED.amount_per_share,
                    dividend_type    = EXCLUDED.dividend_type,
                    pay_date         = EXCLUDED.pay_date,
                    raw              = EXCLUDED.raw
                """,
                values,
            )
        conn.commit()
    return len(values)


def query_dividends(stock_code: str, limit: int = 20) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT stock_code,
                       TO_CHAR(record_date, 'YYYYMMDD') AS record_date,
                       amount_per_share, dividend_type,
                       TO_CHAR(pay_date, 'YYYYMMDD') AS pay_date
                FROM stock_dividend
                WHERE stock_code = %s
                ORDER BY record_date DESC
                LIMIT %s
                """,
                (stock_code, limit),
            )
            return [dict(r) for r in cur.fetchall()]


# ── 추정실적 ───────────────────────────────────────────────

def upsert_estimate(stock_code: str, rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0
    values = [
        (
            stock_code,
            r.get("stac_yymm", ""),
            json.dumps(r, ensure_ascii=False),
        )
        for r in rows if r.get("stac_yymm")
    ]
    if not values:
        return 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO stock_estimate (stock_code, period, data)
                VALUES %s
                ON CONFLICT (stock_code, period) DO UPDATE SET
                    data       = EXCLUDED.data,
                    updated_at = NOW()
                """,
                values,
            )
        conn.commit()
    return len(values)


def query_estimate(stock_code: str, limit: int = 8) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT stock_code, period, data
                FROM stock_estimate
                WHERE stock_code = %s
                ORDER BY period DESC
                LIMIT %s
                """,
                (stock_code, limit),
            )
            return [dict(r) for r in cur.fetchall()]


# ── helpers ────────────────────────────────────────────────

def _to_int(val) -> Optional[int]:
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None


def _to_date(val: Optional[str]) -> Optional[str]:
    """YYYYMMDD → YYYY-MM-DD (PostgreSQL DATE 형식)"""
    if not val or len(val) < 8:
        return None
    return f"{val[:4]}-{val[4:6]}-{val[6:8]}"
