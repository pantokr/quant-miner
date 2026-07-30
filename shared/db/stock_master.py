"""종목 마스터 DB 레이어 (코드 ↔ 종목명 검색).

KIS가 공개하는 마스터 파일(kospi_code.mst / kosdaq_code.mst)을 적재해 두고,
종목명·코드 검색에 사용한다. 적재는 `scripts/load_stock_master.py`가 담당.
"""
import psycopg2.extras
from typing import Any, Dict, List, Optional

from shared.db.connection import get_connection

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_master (
    stock_code VARCHAR(6)  PRIMARY KEY,
    name       VARCHAR(80) NOT NULL,
    market     VARCHAR(10) NOT NULL,   -- KOSPI | KOSDAQ
    isin       VARCHAR(12),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stock_master_name ON stock_master (name);
"""

UPSERT_SQL = """
INSERT INTO stock_master (stock_code, name, market, isin)
VALUES %s
ON CONFLICT (stock_code) DO UPDATE SET
    name       = EXCLUDED.name,
    market     = EXCLUDED.market,
    isin       = EXCLUDED.isin,
    updated_at = NOW();
"""

# 매칭 품질 순으로 정렬한다: 코드 완전일치 → 종목명 완전일치 → 종목명 접두 →
# 코드 접두 → 종목명 부분일치. 같은 점수 안에서는 짧은 이름을 앞세운다
# (예: "삼성전자" 검색 시 "삼성전자우"보다 "삼성전자"가 먼저).
SEARCH_SQL = """
SELECT stock_code, name, market, isin,
       CASE
           WHEN stock_code = %(q)s           THEN 0
           WHEN lower(name) = lower(%(q)s)   THEN 1
           WHEN name ILIKE %(prefix)s        THEN 2
           WHEN stock_code LIKE %(prefix)s   THEN 3
           ELSE 4
       END AS score
FROM stock_master
WHERE stock_code LIKE %(prefix)s
   OR name ILIKE %(contains)s
ORDER BY score, length(name), name
LIMIT %(limit)s;
"""


def create_table() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


def upsert_master(rows: List[Dict[str, Any]]) -> int:
    """rows: [{stock_code, name, market, isin}] 형태."""
    if not rows:
        return 0

    values = [
        (r["stock_code"], r["name"], r["market"], r.get("isin"))
        for r in rows
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, UPSERT_SQL, values)
        conn.commit()
    return len(values)


def delete_missing(keep_codes: List[str]) -> int:
    """마스터 파일에 더 이상 없는 종목(상장폐지 등)을 제거하고 삭제 건수를 반환."""
    if not keep_codes:
        return 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM stock_master WHERE stock_code <> ALL(%s)",
                (keep_codes,),
            )
            deleted = cur.rowcount
        conn.commit()
    return deleted


def search_master(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """종목명·코드 부분 일치 검색 (매칭 품질 순)."""
    q = query.strip()
    if not q:
        return []

    params = {
        "q": q,
        "prefix": f"{q}%",
        "contains": f"%{q}%",
        "limit": limit,
    }
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(SEARCH_SQL, params)
            rows = cur.fetchall()
    return [
        {k: v for k, v in dict(r).items() if k != "score"}
        for r in rows
    ]


def get_by_codes(codes: List[str]) -> List[Dict[str, Any]]:
    """종목코드 목록으로 조회 (요청 순서를 그대로 유지해 반환)."""
    if not codes:
        return []
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT stock_code, name, market, isin
                FROM stock_master
                WHERE stock_code = ANY(%s)
                """,
                (codes,),
            )
            found = {r["stock_code"]: dict(r) for r in cur.fetchall()}
    return [found[c] for c in codes if c in found]


def get_one(code: str) -> Optional[Dict[str, Any]]:
    rows = get_by_codes([code])
    return rows[0] if rows else None


def count_master() -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM stock_master")
            return cur.fetchone()[0]
