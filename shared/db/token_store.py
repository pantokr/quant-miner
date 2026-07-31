"""
KIS 접근 토큰을 PostgreSQL에 저장/조회
컨테이너 재시작에도 토큰이 유지됨
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from shared.db.connection import get_connection

# KIS가 내려주는 만료 시각은 타임존 표기가 없는 KST 벽시계다.
KST = timezone(timedelta(hours=9))

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
    # KIS 응답의 expires_at은 "YYYY-MM-DD HH:MM:SS" 문자열이며 기준은 KST다.
    # 타임존을 붙이지 않으면 TIMESTAMPTZ 컬럼이 UTC로 해석해 만료가 9시간 뒤로 밀린다.
    # 그러면 이미 만료된 토큰을 유효하다고 판단해 KIS가 EGW00123으로 거절하고,
    # 실시간 조회(호가 등)가 하루 중 9시간 동안 통째로 죽는다.
    dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST)
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
