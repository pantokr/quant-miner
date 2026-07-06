"""마이그레이션 001 — stock_minute_chart 를 TimescaleDB 하이퍼테이블로 전환(데이터 보존).

전제: 대상 DB(.env POSTGRES_*)가 **TimescaleDB 이미지로 교체된 상태**여야 함
      (timescaledb 확장 로드 가능). 일반 postgres에서는 실패한다.

동작:
  1. 구 스키마(stock_minute_chart: id/trade_date/trade_time)를 stock_minute_chart_old 로 rename
  2. 새 하이퍼테이블 생성 (shared.db.stock_minute.create_table)
  3. 구 데이터를 date+time → ts 로 변환해 복사 (ON CONFLICT DO NOTHING)
  4. 5분봉 연속집계 갱신 + 건수 비교 출력
  5. 구 테이블은 stock_minute_chart_old 로 남겨둠(검증 후 수동 DROP 권장)

실행:  venv/Scripts/python db/migrations/001_minute_to_timescale.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.db.connection import get_connection
import shared.db.stock_minute as sm


def _columns(cur, table: str) -> set:
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
        (table,),
    )
    return {r[0] for r in cur.fetchall()}


def main() -> None:
    # timescaledb 확장 가용성 사전 점검
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_available_extensions WHERE name='timescaledb'")
            if not cur.fetchone():
                print("[중단] 이 DB에는 timescaledb 확장이 없습니다. 먼저 db 컨테이너를 "
                      "timescale/timescaledb 이미지로 교체하세요.")
                return

            cols = _columns(cur, "stock_minute_chart")
            if "ts" in cols:
                print("[스킵] stock_minute_chart 가 이미 ts 기반(하이퍼테이블)입니다.")
                return
            if "trade_date" not in cols:
                print("[정보] 기존 stock_minute_chart 가 없어 rename 생략(새 테이블만 생성).")
                legacy = False
            else:
                legacy = True

    # 1) 구 테이블 rename
    if legacy:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("ALTER TABLE stock_minute_chart RENAME TO stock_minute_chart_old")
            conn.commit()
        print("1) 구 테이블 → stock_minute_chart_old 로 rename")

    # 2) 새 하이퍼테이블 + 압축 + 연속집계 생성
    sm.create_table()
    print("2) 새 하이퍼테이블(stock_minute_chart) 생성 완료")

    # 3) 데이터 변환 복사
    if legacy:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO stock_minute_chart
                        (stock_code, ts, open_price, high_price, low_price, close_price, volume, cumul_amount)
                    SELECT stock_code,
                           (to_char(trade_date,'YYYY-MM-DD') || ' ' ||
                            substr(trade_time,1,2) || ':' || substr(trade_time,3,2) || ':' ||
                            substr(trade_time,5,2))::timestamp,
                           open_price, high_price, low_price, close_price, volume, cumul_amount
                    FROM stock_minute_chart_old
                    ON CONFLICT (stock_code, ts) DO NOTHING
                    """
                )
                moved = cur.rowcount
            conn.commit()
        print(f"3) 데이터 복사: {moved}행 이관")

    # 4) 연속집계 갱신 + 검증
    with get_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            try:
                cur.execute("CALL refresh_continuous_aggregate('stock_minute_5m', NULL, NULL)")
                print("4) 5분봉 연속집계 갱신 완료")
            except Exception as e:
                print(f"4) 연속집계 갱신 건너뜀: {e}")
            cur.execute("SELECT count(*) FROM stock_minute_chart")
            new_cnt = cur.fetchone()[0]
            old_cnt = None
            if legacy:
                cur.execute("SELECT count(*) FROM stock_minute_chart_old")
                old_cnt = cur.fetchone()[0]
    print(f"   검증: 신규 {new_cnt}행" + (f" / 구 {old_cnt}행" if old_cnt is not None else ""))
    if legacy and old_cnt == new_cnt:
        print("   ✅ 건수 일치. 검증 후 'DROP TABLE stock_minute_chart_old;' 로 정리하세요.")
    elif legacy:
        print("   ⚠️ 건수 불일치 — stock_minute_chart_old 는 보존됨. 원인 확인 필요.")


if __name__ == "__main__":
    main()
