"""공통 설정 — 환경변수 중앙화.

기존에 db/connection.py, services/auth/token.py, services/account/account.py 등에
흩어져 있던 os.getenv 호출을 한 곳으로 모은다. 모든 배포 유닛(collector/trader/api)이
이 모듈을 통해 설정을 읽는다.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── KIS OpenAPI ────────────────────────────────────────────
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
ENV_DV = os.getenv("KIS_ENV", "demo")  # "real" or "demo"

BASE_URL = (
    "https://openapi.koreainvestment.com:9443"
    if ENV_DV == "real"
    else "https://openapivts.koreainvestment.com:29443"
)

# 계좌
CANO = os.getenv("KIS_CANO", "")
ACNT_PRDT_CD = os.getenv("KIS_ACNT_PRDT_CD", "01")

# ── PostgreSQL ─────────────────────────────────────────────
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


def database_url() -> str:
    """SQLAlchemy 접속 URL (db_models 스키마 생성용)."""
    return (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
