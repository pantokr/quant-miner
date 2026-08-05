"""공매도·신용잔고 적재/조회.

표에 필요한 KIS 원본 필드를 모두 담는다. 예전에는 잔고 주수·금액 정도만 저장해서
DB에서 읽어 온 표는 절반이 빈 칸이었다 (KIS에서 막 받아온 응답과 화면이 달라졌다).
조회 함수는 KIS 응답과 같은 키 이름으로 돌려주므로, 라우터는 캐시든 실시간이든
같은 모양을 프론트로 넘긴다.
"""
import psycopg2.extras
from typing import List, Optional
from shared.db.connection import get_connection

CREATE_SHORT_SQL = """
CREATE TABLE IF NOT EXISTS stock_short_sell (
    id            BIGSERIAL PRIMARY KEY,
    stock_code    VARCHAR(10) NOT NULL,
    trade_date    DATE        NOT NULL,
    close_price   BIGINT,       -- stck_clpr
    change_rate   NUMERIC(8,2), -- prdy_ctrt
    volume        BIGINT,       -- acml_vol 거래량
    short_volume  BIGINT,       -- ssts_cntg_qty 공매도 수량
    short_ratio   NUMERIC(8,2), -- ssts_vol_rlim 거래량 대비 비중
    short_amount  BIGINT,       -- ssts_tr_pbmn 공매도 대금
    short_amt_rt  NUMERIC(8,2), -- ssts_tr_pbmn_rlim 거래대금 대비 비중
    short_cumul   BIGINT,       -- acml_ssts_cntg_qty 누적 공매도
    short_avg_prc BIGINT,       -- avrg_prc 공매도 평균가
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_code, trade_date)
);
"""

CREATE_CREDIT_SQL = """
CREATE TABLE IF NOT EXISTS stock_credit (
    id              BIGSERIAL PRIMARY KEY,
    stock_code      VARCHAR(10) NOT NULL,
    trade_date      DATE        NOT NULL,
    close_price     BIGINT,       -- stck_prpr
    change_rate     NUMERIC(8,2), -- prdy_ctrt
    volume          BIGINT,       -- acml_vol
    loan_new_qty    BIGINT,       -- whol_loan_new_stcn 융자 신규
    loan_redeem_qty BIGINT,       -- whol_loan_rdmp_stcn 융자 상환
    credit_qty      BIGINT,       -- whol_loan_rmnd_stcn 융자잔고 주수
    credit_amount   BIGINT,       -- whol_loan_rmnd_amt 융자잔고 금액
    credit_rate     NUMERIC(8,2), -- whol_loan_rmnd_rate 융자잔고 비율
    stln_remain_qty BIGINT,       -- whol_stln_rmnd_stcn 대주잔고 주수
    stln_remain_amt BIGINT,       -- whol_stln_rmnd_amt 대주잔고 금액
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stock_code, trade_date)
);
"""

# 좁은 스키마로 이미 만들어진 DB를 위한 이관. CREATE TABLE IF NOT EXISTS는
# 테이블이 있으면 아무것도 하지 않으므로 컬럼 추가는 따로 해 줘야 한다.
_MIGRATE_SQL = [
    "ALTER TABLE stock_short_sell ADD COLUMN IF NOT EXISTS volume        BIGINT",
    "ALTER TABLE stock_short_sell ADD COLUMN IF NOT EXISTS short_ratio   NUMERIC(8,2)",
    "ALTER TABLE stock_short_sell ADD COLUMN IF NOT EXISTS short_amt_rt  NUMERIC(8,2)",
    "ALTER TABLE stock_short_sell ADD COLUMN IF NOT EXISTS short_cumul   BIGINT",
    "ALTER TABLE stock_short_sell ADD COLUMN IF NOT EXISTS short_avg_prc BIGINT",
    "ALTER TABLE stock_credit ADD COLUMN IF NOT EXISTS change_rate     NUMERIC(8,2)",
    "ALTER TABLE stock_credit ADD COLUMN IF NOT EXISTS volume          BIGINT",
    "ALTER TABLE stock_credit ADD COLUMN IF NOT EXISTS loan_new_qty    BIGINT",
    "ALTER TABLE stock_credit ADD COLUMN IF NOT EXISTS loan_redeem_qty BIGINT",
    "ALTER TABLE stock_credit ADD COLUMN IF NOT EXISTS stln_remain_qty BIGINT",
    "ALTER TABLE stock_credit ADD COLUMN IF NOT EXISTS stln_remain_amt BIGINT",
]

UPSERT_SHORT_SQL = """
INSERT INTO stock_short_sell
    (stock_code, trade_date, close_price, change_rate, volume,
     short_volume, short_ratio, short_amount, short_amt_rt, short_cumul, short_avg_prc)
VALUES %s
ON CONFLICT (stock_code, trade_date) DO UPDATE SET
    close_price   = EXCLUDED.close_price,
    change_rate   = EXCLUDED.change_rate,
    volume        = EXCLUDED.volume,
    short_volume  = EXCLUDED.short_volume,
    short_ratio   = EXCLUDED.short_ratio,
    short_amount  = EXCLUDED.short_amount,
    short_amt_rt  = EXCLUDED.short_amt_rt,
    short_cumul   = EXCLUDED.short_cumul,
    short_avg_prc = EXCLUDED.short_avg_prc;
"""

UPSERT_CREDIT_SQL = """
INSERT INTO stock_credit
    (stock_code, trade_date, close_price, change_rate, volume,
     loan_new_qty, loan_redeem_qty, credit_qty, credit_amount, credit_rate,
     stln_remain_qty, stln_remain_amt)
VALUES %s
ON CONFLICT (stock_code, trade_date) DO UPDATE SET
    close_price     = EXCLUDED.close_price,
    change_rate     = EXCLUDED.change_rate,
    volume          = EXCLUDED.volume,
    loan_new_qty    = EXCLUDED.loan_new_qty,
    loan_redeem_qty = EXCLUDED.loan_redeem_qty,
    credit_qty      = EXCLUDED.credit_qty,
    credit_amount   = EXCLUDED.credit_amount,
    credit_rate     = EXCLUDED.credit_rate,
    stln_remain_qty = EXCLUDED.stln_remain_qty,
    stln_remain_amt = EXCLUDED.stln_remain_amt;
"""


def create_tables() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_SHORT_SQL)
            cur.execute(CREATE_CREDIT_SQL)
            for sql in _MIGRATE_SQL:
                cur.execute(sql)
        conn.commit()


def _to_date(yyyymmdd: str) -> Optional[str]:
    s = (yyyymmdd or "").strip()
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 else None


def _num(value, cast=int):
    try:
        return cast(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0


def _range(start_date: str, end_date: str) -> tuple:
    return (
        f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
        f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
    )


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
            _num(r.get("stck_clpr")),
            _num(r.get("prdy_ctrt"), float),
            _num(r.get("acml_vol")),
            _num(r.get("ssts_cntg_qty")),
            _num(r.get("ssts_vol_rlim"), float),
            _num(r.get("ssts_tr_pbmn")),
            _num(r.get("ssts_tr_pbmn_rlim"), float),
            _num(r.get("acml_ssts_cntg_qty")),
            _num(r.get("avrg_prc")),
        ))
    if not values:
        return 0
    create_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_SHORT_SQL, values)
        conn.commit()
        return len(values)


def upsert_credit(stock_code: str, rows: List[dict]) -> int:
    """FHPST04760000 output 기준 (deal_date / whol_* 필드)."""
    values = []
    for r in rows:
        trade_date = _to_date(r.get("deal_date", ""))
        if not trade_date:
            continue
        values.append((
            stock_code,
            trade_date,
            _num(r.get("stck_prpr")),
            _num(r.get("prdy_ctrt"), float),
            _num(r.get("acml_vol")),
            _num(r.get("whol_loan_new_stcn")),
            _num(r.get("whol_loan_rdmp_stcn")),
            _num(r.get("whol_loan_rmnd_stcn")),
            _num(r.get("whol_loan_rmnd_amt")),
            _num(r.get("whol_loan_rmnd_rate"), float),
            _num(r.get("whol_stln_rmnd_stcn")),
            _num(r.get("whol_stln_rmnd_amt")),
        ))
    if not values:
        return 0
    create_tables()
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_CREDIT_SQL, values)
        conn.commit()
        return len(values)


def query_short_sell(stock_code: str, start_date: str, end_date: str) -> List[dict]:
    """DB에서 기간별 공매도 조회 (일자 오름차순). KIS 응답과 같은 키로 반환."""
    s, e = _range(start_date, end_date)
    create_tables()
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT TO_CHAR(trade_date, 'YYYYMMDD') AS stck_bsop_date,
                       close_price   AS stck_clpr,
                       change_rate   AS prdy_ctrt,
                       volume        AS acml_vol,
                       short_volume  AS ssts_cntg_qty,
                       short_ratio   AS ssts_vol_rlim,
                       short_amount  AS ssts_tr_pbmn,
                       short_amt_rt  AS ssts_tr_pbmn_rlim,
                       short_cumul   AS acml_ssts_cntg_qty,
                       short_avg_prc AS avrg_prc
                FROM stock_short_sell
                WHERE stock_code = %s AND trade_date BETWEEN %s AND %s
                  -- 좁은 스키마 시절에 적재된 행은 새 칸이 전부 NULL이라 표가 반쯤 빈다.
                  -- 없는 셈 치면 라우터가 다시 받아 채우므로 한 번 조회하면 스스로 낫는다.
                  AND short_cumul IS NOT NULL
                ORDER BY trade_date ASC
                """,
                (stock_code, s, e),
            )
            return [dict(r) for r in cur.fetchall()]


def query_credit(stock_code: str, start_date: str, end_date: str) -> List[dict]:
    """DB에서 기간별 신용잔고 조회 (일자 오름차순). KIS 응답과 같은 키로 반환."""
    s, e = _range(start_date, end_date)
    create_tables()
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT TO_CHAR(trade_date, 'YYYYMMDD') AS deal_date,
                       close_price     AS stck_prpr,
                       change_rate     AS prdy_ctrt,
                       volume          AS acml_vol,
                       loan_new_qty    AS whol_loan_new_stcn,
                       loan_redeem_qty AS whol_loan_rdmp_stcn,
                       credit_qty      AS whol_loan_rmnd_stcn,
                       credit_amount   AS whol_loan_rmnd_amt,
                       credit_rate     AS whol_loan_rmnd_rate,
                       stln_remain_qty AS whol_stln_rmnd_stcn,
                       stln_remain_amt AS whol_stln_rmnd_amt
                FROM stock_credit
                WHERE stock_code = %s AND trade_date BETWEEN %s AND %s
                  -- 위와 같은 이유 (예전 스키마로 적재된 부분 행은 없는 셈 친다)
                  AND change_rate IS NOT NULL
                ORDER BY trade_date ASC
                """,
                (stock_code, s, e),
            )
            return [dict(r) for r in cur.fetchall()]
