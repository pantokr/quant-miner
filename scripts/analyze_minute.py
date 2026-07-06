"""분봉 데이터 종합 테스트/분석 (TimescaleDB).

특정 종목의 적재된 분봉으로 인벤토리·커버리지·압축·5분봉 리샘플·백테스트를 수행한다.

실행: venv/Scripts/python scripts/analyze_minute.py --iscd 005930
"""
import os
import sys
import argparse

# Windows 콘솔(cp949)에서도 한글이 깨지지 않도록 출력 인코딩 강제
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.db.connection import get_connection
from trader.strategy import MovingAverageCrossStrategy
from research.backtest.engine import run_backtest


def section(t):
    print("\n" + "=" * 60 + f"\n{t}\n" + "=" * 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iscd", default="005930")
    ap.add_argument("--short", type=int, default=5)
    ap.add_argument("--long", type=int, default=20)
    args = ap.parse_args()
    iscd = args.iscd

    # 1) 인벤토리 -----------------------------------------------------
    section(f"1. 인벤토리 — {iscd}")
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT count(*), min(ts), max(ts), count(distinct ts::date) "
                "FROM stock_minute_chart WHERE stock_code=%s", (iscd,))
            n, mn, mx, days = cur.fetchone()
            print(f"  행수 {n:,} · 기간 {mn} ~ {mx} · {days} 거래일")
            cur.execute(
                "SELECT count(*) FROM timescaledb_information.chunks "
                "WHERE hypertable_name='stock_minute_chart'")
            print(f"  하이퍼테이블 청크 수: {cur.fetchone()[0]}")

    # 2) 커버리지(최근 10일 일별 봉 개수) -----------------------------
    section("2. 커버리지 — 최근 10 거래일 봉 개수 (390이면 완전)")
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT ts::date d, count(*) FROM stock_minute_chart "
                "WHERE stock_code=%s GROUP BY d ORDER BY d DESC LIMIT 10", (iscd,))
            for d, cnt in cur.fetchall():
                bar = "█" * (cnt * 30 // 390)
                print(f"  {d}  {cnt:>4}  {bar}")

    # 3) 압축 (7일 지난 청크 압축 후 절감률) --------------------------
    section("3. 압축 — 7일 지난 청크 압축")
    with get_connection() as c:
        c.autocommit = True
        with c.cursor() as cur:
            cur.execute("SELECT show_chunks('stock_minute_chart', older_than => INTERVAL '7 days')")
            chunks = [r[0] for r in cur.fetchall()]
            comp = 0
            for ch in chunks:
                try:
                    cur.execute("SELECT compress_chunk(%s, if_not_compressed => true)", (ch,))
                    comp += 1
                except Exception:
                    pass
            print(f"  대상 청크 {len(chunks)} · 압축 실행 {comp}")
            cur.execute("""
                SELECT pg_size_pretty(sum(before_compression_total_bytes)),
                       pg_size_pretty(sum(after_compression_total_bytes))
                FROM hypertable_compression_stats('stock_minute_chart')
            """)
            before, after = cur.fetchone()
            print(f"  압축 전 {before} → 압축 후 {after}")

    # 4) 5분봉 CAGG (갱신 후 최근 샘플) -------------------------------
    section("4. 5분봉 연속집계 (리샘플)")
    # refresh_continuous_aggregate 는 트랜잭션 밖에서만 실행 가능 → raw autocommit 커넥션
    c = get_connection()
    c.autocommit = True
    try:
        with c.cursor() as cur:
            try:
                cur.execute("CALL refresh_continuous_aggregate('stock_minute_5m', NULL, NULL)")
            except Exception as e:
                print(f"  갱신 경고: {e}")
            cur.execute("SELECT count(*) FROM stock_minute_5m WHERE stock_code=%s", (iscd,))
            print(f"  총 5분봉: {cur.fetchone()[0]}")
            cur.execute(
                "SELECT bucket, open_price, high_price, low_price, close_price, volume "
                "FROM stock_minute_5m WHERE stock_code=%s ORDER BY bucket DESC LIMIT 5", (iscd,))
            for b, o, h, l, cl, v in cur.fetchall():
                print(f"  {b}  O{o} H{h} L{l} C{cl} V{v}")
    finally:
        c.close()

    # 5) 일봉 백테스트 (분봉→일별 종가, MA 교차) ----------------------
    section(f"5. 백테스트 — 일봉 MA-Cross({args.short}/{args.long})")
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT time_bucket('1 day', ts) d, last(close_price, ts) "
                "FROM stock_minute_chart WHERE stock_code=%s GROUP BY d ORDER BY d", (iscd,))
            daily = [float(r[1]) for r in cur.fetchall()]
    print(f"  일봉 {len(daily)}개")
    res = run_backtest(daily, MovingAverageCrossStrategy(args.short, args.long))
    print("  " + res.summary().replace("\n", "\n  "))

    # 6) 인트라데이 백테스트 (1분봉, 참고) ----------------------------
    section(f"6. 백테스트 — 인트라데이 1분봉 MA-Cross({args.short}/{args.long})")
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT close_price FROM stock_minute_chart WHERE stock_code=%s ORDER BY ts", (iscd,))
            mins = [float(r[0]) for r in cur.fetchall()]
    print(f"  1분봉 {len(mins):,}개")
    res2 = run_backtest(mins, MovingAverageCrossStrategy(args.short, args.long))
    print("  " + res2.summary().replace("\n", "\n  "))


if __name__ == "__main__":
    main()
