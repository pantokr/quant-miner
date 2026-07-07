"""ML 모델 레지스트리 — 학습된 모델(직렬화 아티팩트)과 메타데이터를 DB에 영구 저장.

아티팩트(scaler+estimator, joblib 압축)는 BYTEA로, 설정/메트릭은 JSONB로 보관한다.
model_id 로 어디서든(로컬/서버/컨테이너) 불러와 추론에 재사용.
"""
import json
import psycopg2
import psycopg2.extras
from typing import List, Optional
from shared.db.connection import get_connection

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ml_model (
    model_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iscd       VARCHAR(10) NOT NULL,
    target     VARCHAR(16) NOT NULL,   -- return | direction
    horizon    INT         NOT NULL,
    model_name VARCHAR(40) NOT NULL,
    features   JSONB       NOT NULL,
    params     JSONB       NOT NULL DEFAULT '{}',
    metrics    JSONB       NOT NULL,
    samples    JSONB       NOT NULL,
    artifact   BYTEA       NOT NULL,   -- joblib 직렬화(scaler+model)
    note       TEXT        DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ml_model_iscd ON ml_model (iscd, created_at DESC);
"""


def create_table() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()


def save_model(meta: dict, artifact: bytes) -> str:
    """모델 저장 후 model_id 반환. meta: iscd,target,horizon,model_name,features,params,metrics,samples,note."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ml_model
                    (iscd, target, horizon, model_name, features, params, metrics, samples, artifact, note)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING model_id
                """,
                (
                    meta["iscd"], meta["target"], meta["horizon"], meta["model_name"],
                    psycopg2.extras.Json(meta["features"]),
                    psycopg2.extras.Json(meta.get("params", {})),
                    psycopg2.extras.Json(meta["metrics"]),
                    psycopg2.extras.Json(meta["samples"]),
                    psycopg2.Binary(artifact),
                    meta.get("note", ""),
                ),
            )
            model_id = cur.fetchone()[0]
        conn.commit()
    return str(model_id)


def list_models(iscd: Optional[str] = None, limit: int = 50) -> List[dict]:
    """레지스트리 목록(아티팩트 제외)."""
    where = "WHERE iscd = %s" if iscd else ""
    args = ([iscd, limit] if iscd else [limit])
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT model_id::text, iscd, target, horizon, model_name,
                       features, metrics, samples, note, created_at
                FROM ml_model {where}
                ORDER BY created_at DESC LIMIT %s
                """,
                args,
            )
            return [dict(r) for r in cur.fetchall()]


def get_model(model_id: str) -> Optional[dict]:
    """메타 + 아티팩트(bytes) 반환. 없으면 None."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT model_id::text, iscd, target, horizon, model_name,
                       features, params, metrics, samples, note, created_at, artifact
                FROM ml_model WHERE model_id = %s
                """,
                (model_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    d = dict(row)
    d["artifact"] = bytes(d["artifact"])  # memoryview → bytes
    return d


def delete_model(model_id: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ml_model WHERE model_id = %s", (model_id,))
            deleted = cur.rowcount
        conn.commit()
    return deleted > 0
