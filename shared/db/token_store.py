"""
KIS 접근 토큰을 PostgreSQL에 저장/조회
컨테이너 재시작에도 토큰이 유지됨
"""
from datetime import datetime
from typing import Optional
from shared.db.connection import get_connection

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS kis_token (
    env        VARCHAR(10) PRIMARY KEY,   -- 'real' or 'demo'
    token      TEXT        NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def create_table() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


def load_token(env: str) -> Optional[dict]:
    """저장된 토큰 조회. 없으면 None."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT token, expires_at FROM kis_token WHERE env = %s",
                (env,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {"access_token": row[0], "expires_at": row[1]}


def save_token(env: str, token: str, expires_at: str) -> None:
    """토큰 저장 (upsert)."""
    # KIS 응답의 expires_at은 "YYYY-MM-DD HH:MM:SS" 문자열
    dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO kis_token (env, token, expires_at, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (env) DO UPDATE SET
                    token      = EXCLUDED.token,
                    expires_at = EXCLUDED.expires_at,
                    updated_at = NOW()
                """,
                (env, token, dt),
            )
        conn.commit()
