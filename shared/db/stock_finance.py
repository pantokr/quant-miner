"""재무정보 DB 레이어 (재무상태표 / 손익계산서 / 재무비율 등)"""
import json
import psycopg2.extras
from typing import Any, Dict, List, Optional
from shared.db.connection import get_connection

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_finance (
    id           BIGSERIAL    PRIMARY KEY,
    stock_code   VARCHAR(10)  NOT NULL,
    finance_type VARCHAR(30)  NOT NULL,  -- balance_sheet / income_statement / financial_ratio / ...
    period_type  CHAR(1)      NOT NULL,  -- A:연간  Q:분기
    period       VARCHAR(6)   NOT NULL,  -- YYYYMM
    data         JSONB        NOT NULL,
    updated_at   TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (stock_code, finance_type, period_type, period)
);

CREATE INDEX IF NOT EXISTS idx_sf_code_type
    ON stock_finance (stock_code, finance_type, period_type);
"""

UPSERT_SQL = """
INSERT INTO stock_finance (stock_code, finance_type, period_type, period, data)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (stock_code, finance_type, period_type, period) DO UPDATE SET
    data       = EXCLUDED.data,
    updated_at = NOW();
"""


def create_table() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


def upsert_finance(
    stock_code: str,
    finance_type: str,
    period_type: str,
    rows: List[Dict[str, Any]],
    period_key: str = "stac_yymm",
) -> int:
    """
    재무 데이터 upsert

    Args:
        stock_code:   종목코드
        finance_type: balance_sheet | income_statement | financial_ratio | ...
        period_type:  "A" 연간 | "Q" 분기
        rows:         KIS API output 리스트 (dict)
        period_key:   결산년월 필드명 (기본: stac_yymm)
    """
    if not rows:
        return 0

    values = []
    for row in rows:
        period = row.get(period_key, "")
        if not period:
            continue
        values.append((
            stock_code,
            finance_type,
            period_type,
            period,
            json.dumps(row, ensure_ascii=False),
        ))

    if not values:
        return 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_SQL, values)
        conn.commit()
    return len(values)


def query_finance(
    stock_code: str,
    finance_type: str,
    period_type: str = "A",
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """재무 데이터 조회 (최신순)"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT stock_code, finance_type, period_type, period, data
                FROM stock_finance
                WHERE stock_code = %s
                  AND finance_type = %s
                  AND period_type = %s
                ORDER BY period DESC
                LIMIT %s
                """,
                (stock_code, finance_type, period_type, limit),
            )
            return [dict(r) for r in cur.fetchall()]
