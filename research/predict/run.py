"""가격 예측 모델 프로토타입 + 테스트 결과.

적재된 분봉(TimescaleDB)으로 기술적 특징을 만들어 '미래 return'을 예측하는 모델
몇 개를 시간순 분할로 학습/평가한다. 트레이딩 관점에서 방향 정확도(Dir.Acc)가 핵심.

원칙(누수 방지):
  - 특징은 시점 t까지만, 타깃은 t→t+H 미래 return
  - 시간순 70/30 분할(셔플 금지), 스케일러는 train으로만 fit
  - 베이스라인(무변화) 대비로 실질 성능 판단

실행: venv/Scripts/python -m research.predict.run --iscd 005930 --horizon 5
"""
import os
import sys
import argparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from shared.db.connection import get_connection


def load_minute(iscd: str) -> pd.DataFrame:
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute(
                "SELECT ts, close_price, volume FROM stock_minute_chart "
                "WHERE stock_code=%s ORDER BY ts", (iscd,))
            rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["ts", "close", "volume"])
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).rolling(n).mean()
    dn = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def build(df: pd.DataFrame, horizon: int):
    df = df.copy()
    df["ret"] = df["close"].pct_change()
    for lag in range(1, 6):
        df[f"ret_lag{lag}"] = df["ret"].shift(lag)
    df["ma5"] = df["close"].rolling(5).mean() / df["close"] - 1
    df["ma20"] = df["close"].rolling(20).mean() / df["close"] - 1
    df["vol5"] = df["ret"].rolling(5).std()
    df["rsi14"] = rsi(df["close"], 14)
    df["vchg"] = df["volume"].pct_change().clip(-5, 5)
    df["target"] = df["close"].shift(-horizon) / df["close"] - 1  # 미래 H분 return
    feats = [f"ret_lag{l}" for l in range(1, 6)] + ["ma5", "ma20", "vol5", "rsi14", "vchg"]
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=feats + ["target"])
    return df[feats].values, df["target"].values, feats


def evaluate(name, y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred)) * 1e4   # bp
    mae = mean_absolute_error(y_true, y_pred) * 1e4            # bp
    dir_acc = np.mean(np.sign(y_pred) == np.sign(y_true)) * 100
    r2 = r2_score(y_true, y_pred)
    print(f"  {name:<22} RMSE {rmse:6.2f}bp · MAE {mae:6.2f}bp · Dir.Acc {dir_acc:5.1f}% · R² {r2:+.4f}")
    return dir_acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iscd", default="005930")
    ap.add_argument("--horizon", type=int, default=5, help="예측 지평(분)")
    args = ap.parse_args()

    df = load_minute(args.iscd)
    X, y, feats = build(df, args.horizon)
    n = len(X)
    split = int(n * 0.7)
    Xtr, Xte, ytr, yte = X[:split], X[split:], y[:split], y[split:]

    scaler = StandardScaler().fit(Xtr)
    Xtr_s, Xte_s = scaler.transform(Xtr), scaler.transform(Xte)

    print(f"\n종목 {args.iscd} · 지평 {args.horizon}분 · 표본 {n:,} (train {split:,}/test {n-split:,}) · 특징 {len(feats)}개")
    print("=" * 78)
    print("테스트셋 성능 (Dir.Acc = 방향 적중률, 50%가 동전던지기)")
    print("-" * 78)

    # 0) 베이스라인 — 항상 무변화(0) 예측
    base = np.zeros_like(yte)
    up_rate = np.mean(yte > 0) * 100
    print(f"  {'Baseline(무변화)':<22} RMSE {np.sqrt(mean_squared_error(yte, base))*1e4:6.2f}bp · "
          f"MAE {mean_absolute_error(yte, base)*1e4:6.2f}bp · "
          f"Dir.Acc  n/a  · 상승비율 {up_rate:.1f}%")

    models = {
        "Ridge": Ridge(alpha=1.0),
        "RandomForest": RandomForestRegressor(n_estimators=120, max_depth=6, n_jobs=-1, random_state=0),
        "GradientBoosting": GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=0),
    }
    results = {}
    for name, m in models.items():
        m.fit(Xtr_s, ytr)
        results[name] = evaluate(name, yte, m.predict(Xte_s))

    best = max(results, key=results.get)
    print("-" * 78)
    print(f"방향 적중 최고: {best} ({results[best]:.1f}%)")
    print("\n해석: Dir.Acc가 50%를 유의미하게 넘어야 예측력 있음. 분봉 단기예측은 대개 50% 부근"
          "(효율적시장)이라, 지평(--horizon)·특징을 바꿔가며 비교하는 게 핵심.")


if __name__ == "__main__":
    main()
