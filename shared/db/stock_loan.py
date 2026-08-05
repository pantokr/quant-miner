"""대차거래추이 적재/조회 (HHPST074500C0 output1)."""
import psycopg2.extras
from typing import List, Optional
from shared.db.connection import get_connection

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_loan_trans (
    id           BIGSERIAL PRIMARY KEY,
    stock_code   VARCHAR(10) NOT NULL,
    trade_date   DATE        NOT NULL,
    close_price  NUMERIC(16,2),   -- 지수 조회 시 소수가 붙어 정수로 못 받는다
    change_rate  NUMERIC(8,2),
    volume       BIGINT,          -- 누적 거래량
    new_qty      BIGINT,          -- 대차 신규 체결
    redeem_qty   BIGINT,          -- 대차 상환
    remain_qty   BIGINT,          -- 대차잔고 주수
    remain_amt   BIGINT,          -- 대차잔고 금액(백만원 단위로 온다)
    remain_diff  BIGINT,          -- 전일 대비 잔고 증감
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_code, trade_date)
);
"""

UPSERT_SQL = """
INSERT INTO stock_loan_trans
    (stock_code, trade_date, close_price, change_rate, volume,
     new_qty, redeem_qty, remain_qty, remain_amt, remain_diff)
VALUES %s
ON CONFLICT (stock_code, trade_date) DO UPDATE SET
    close_price = EXCLUDED.close_price,
    change_rate = EXCLUDED.change_rate,
    volume      = EXCLUDED.volume,
    new_qty     = EXCLUDED.new_qty,
    redeem_qty  = EXCLUDED.redeem_qty,
    remain_qty  = EXCLUDED.remain_qty,
    remain_amt  = EXCLUDED.remain_amt,
    remain_diff = EXCLUDED.remain_diff;
"""


def create_table() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


def _to_date(yyyymmdd: str) -> Optional[str]:
    s = (yyyymmdd or "").strip()
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 else None


def _num(value, cast=int):
    try:
        return cast(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0


def upsert_loan_trans(stock_code: str, rows: List[dict]) -> int:
    values = []
    for r in rows:
        trade_date = _to_date(r.get("bsop_date", ""))
        if not trade_date:
            continue
        values.append((
            stock_code,
            trade_date,
            _num(r.get("stck_prpr"), float),
            _num(r.get("prdy_ctrt"), float),
            _num(r.get("acml_vol")),
            _num(r.get("new_stcn")),
            _num(r.get("rdmp_stcn")),
            _num(r.get("rmnd_stcn")),
            _num(r.get("rmnd_amt")),
            _num(r.get("prdy_rmnd_vrss")),
        ))
    if not values:
        return 0
    create_table()
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_SQL, values)
        conn.commit()
        return len(values)


def query_loan_trans(stock_code: str, start_date: str, end_date: str) -> List[dict]:
    """DB에서 기간별 대차거래추이 조회 (일자 오름차순)."""
    s = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    e = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
    create_table()
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT TO_CHAR(trade_date, 'YYYYMMDD') AS bsop_date,
                       close_price AS stck_prpr,
                       change_rate AS prdy_ctrt,
                       volume      AS acml_vol,
                       new_qty     AS new_stcn,
                       redeem_qty  AS rdmp_stcn,
                       remain_qty  AS rmnd_stcn,
                       remain_amt  AS rmnd_amt,
                       remain_diff AS prdy_rmnd_vrss
                FROM stock_loan_trans
                WHERE stock_code = %s AND trade_date BETWEEN %s AND %s
                ORDER BY trade_date ASC
                """,
                (stock_code, s, e),
            )
            return [dict(r) for r in cur.fetchall()]
