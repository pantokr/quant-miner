"""설정 주도(config-driven) 가격 예측 코어.

CLI와 API가 공통으로 호출하는 순수 학습/평가 로직. 특징은 화이트리스트 레지스트리에서만
선택(임의 코드 주입 방지), 시간순 분할·누수 방지는 여기 고정한다.

핵심:
  FEATURES  : 이름 → (df) -> Series  (선택 가능한 특징 카탈로그)
  MODELS    : task별 사용 가능한 모델 이름
  PredictSpec : 학습 설정(입력)
  train_and_evaluate(spec) -> dict : 메트릭 + 특징중요도 (JSON 직렬화 가능)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List
from pydantic import BaseModel, Field

from shared.db.connection import get_connection


# ── 특징 레지스트리 ─────────────────────────────────────────
def _rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).rolling(n).mean()
    dn = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _z(s: pd.Series, n: int = 20) -> pd.Series:
    return (s - s.rolling(n).mean()) / s.rolling(n).std()


FEATURES: Dict[str, callable] = {
    # close 파생
    "ret_lag1": lambda df: df["ret"].shift(1),
    "ret_lag2": lambda df: df["ret"].shift(2),
    "ret_lag3": lambda df: df["ret"].shift(3),
    "ret_lag4": lambda df: df["ret"].shift(4),
    "ret_lag5": lambda df: df["ret"].shift(5),
    "ma5": lambda df: df["close"].rolling(5).mean() / df["close"] - 1,
    "ma10": lambda df: df["close"].rolling(10).mean() / df["close"] - 1,
    "ma20": lambda df: df["close"].rolling(20).mean() / df["close"] - 1,
    "vol5": lambda df: df["ret"].rolling(5).std(),
    "vol20": lambda df: df["ret"].rolling(20).std(),
    "rsi14": lambda df: _rsi(df["close"], 14),
    "close_z": lambda df: _z(df["close"], 20),
    # high/low/open 파생
    "hl_range": lambda df: (df["high"] - df["low"]) / df["close"],
    "co_ret": lambda df: (df["close"] - df["open"]) / df["open"],
    # volume 파생
    "volume_z": lambda df: _z(df["volume"], 20),
    "vchg": lambda df: df["volume"].pct_change().clip(-5, 5),
}

DEFAULT_FEATURES = ["ret_lag1", "ret_lag2", "ret_lag3", "ma5", "ma20", "vol5", "rsi14", "volume_z"]

# ── 모델 카탈로그 ───────────────────────────────────────────
MODELS = {
    "return": ["ridge", "random_forest", "gradient_boosting"],       # 회귀
    "direction": ["logistic", "random_forest", "gradient_boosting"],  # 분류
}


def _make_model(name: str, task: str, params: dict):
    from sklearn.linear_model import Ridge, LogisticRegression
    from sklearn.ensemble import (
        RandomForestRegressor, GradientBoostingRegressor,
        RandomForestClassifier, GradientBoostingClassifier,
    )
    p = dict(params or {})
    if task == "return":
        return {
            "ridge": lambda: Ridge(alpha=p.get("alpha", 1.0)),
            "random_forest": lambda: RandomForestRegressor(
                n_estimators=p.get("n_estimators", 120), max_depth=p.get("max_depth", 6),
                n_jobs=-1, random_state=0),
            "gradient_boosting": lambda: GradientBoostingRegressor(
                n_estimators=p.get("n_estimators", 150), max_depth=p.get("max_depth", 3),
                random_state=0),
        }[name]()
    else:  # direction (분류)
        return {
            "logistic": lambda: LogisticRegression(max_iter=1000, C=p.get("C", 1.0)),
            "random_forest": lambda: RandomForestClassifier(
                n_estimators=p.get("n_estimators", 120), max_depth=p.get("max_depth", 6),
                n_jobs=-1, random_state=0),
            "gradient_boosting": lambda: GradientBoostingClassifier(
                n_estimators=p.get("n_estimators", 150), max_depth=p.get("max_depth", 3),
                random_state=0),
        }[name]()


# ── 설정/결과 스키마 ────────────────────────────────────────
class PredictSpec(BaseModel):
    iscd: str = "005930"
    features: List[str] = Field(default_factory=lambda: list(DEFAULT_FEATURES))
    target: str = "return"        # return | direction
    horizon: int = 5              # 예측 지평(분)
    model: str = "ridge"
    params: dict = Field(default_factory=dict)
    test_size: float = 0.3
    limit: int = 0                # 0=전체, N=최근 N봉만 (빠른 실험용)
    save: bool = False            # True 시 학습 후 레지스트리에 영구 저장
    note: str = ""


# ── 데이터/특징 ─────────────────────────────────────────────
def load_minute(iscd: str, limit: int = 0) -> pd.DataFrame:
    q = ("SELECT ts, open_price, high_price, low_price, close_price, volume "
         "FROM stock_minute_chart WHERE stock_code=%s ORDER BY ts")
    if limit and limit > 0:
        q = ("SELECT * FROM (SELECT ts, open_price, high_price, low_price, close_price, volume "
             "FROM stock_minute_chart WHERE stock_code=%s ORDER BY ts DESC LIMIT %s) t ORDER BY ts")
    with get_connection() as c:
        with c.cursor() as cur:
            cur.execute(q, (iscd, limit) if (limit and limit > 0) else (iscd,))
            rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df


def build_xy(df: pd.DataFrame, spec: PredictSpec):
    df = df.copy()
    df["ret"] = df["close"].pct_change()
    unknown = [f for f in spec.features if f not in FEATURES]
    if unknown:
        raise ValueError(f"알 수 없는 특징: {unknown}. 사용 가능: {list(FEATURES)}")
    for f in spec.features:
        df[f] = FEATURES[f](df)
    fut = df["close"].shift(-spec.horizon) / df["close"] - 1
    if spec.target == "return":
        df["_y"] = fut
    else:
        df["_y"] = (fut > 0).astype(int)
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=spec.features + ["_y"])
    return df[spec.features].values, df["_y"].values


# ── 학습/평가 ───────────────────────────────────────────────
def train_and_evaluate(spec: PredictSpec) -> dict:
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import (
        mean_absolute_error, mean_squared_error, r2_score,
        accuracy_score, precision_score,
    )

    if spec.model not in MODELS.get(spec.target, []):
        raise ValueError(f"target={spec.target} 에 model={spec.model} 불가. 가능: {MODELS.get(spec.target)}")

    X, y = build_xy(load_minute(spec.iscd, spec.limit), spec)
    n = len(X)
    if n < 200:
        raise ValueError(f"표본 부족: {n} (최소 200). 데이터 적재 확인")
    split = int(n * (1 - spec.test_size))
    Xtr, Xte, ytr, yte = X[:split], X[split:], y[:split], y[split:]

    scaler = StandardScaler().fit(Xtr)
    Xtr_s, Xte_s = scaler.transform(Xtr), scaler.transform(Xte)

    model = _make_model(spec.model, spec.target, spec.params)
    model.fit(Xtr_s, ytr)
    pred = model.predict(Xte_s)

    if spec.target == "return":
        metrics = {
            "rmse_bp": round(float(np.sqrt(mean_squared_error(yte, pred))) * 1e4, 3),
            "mae_bp": round(float(mean_absolute_error(yte, pred)) * 1e4, 3),
            "dir_acc_pct": round(float(np.mean(np.sign(pred) == np.sign(yte))) * 100, 2),
            "r2": round(float(r2_score(yte, pred)), 4),
        }
    else:
        maj = max(float(np.mean(yte)), 1 - float(np.mean(yte))) * 100
        metrics = {
            "accuracy_pct": round(float(accuracy_score(yte, pred)) * 100, 2),
            "precision_pct": round(float(precision_score(yte, pred, zero_division=0)) * 100, 2),
            "majority_baseline_pct": round(maj, 2),
            "up_ratio_pct": round(float(np.mean(yte)) * 100, 2),
        }

    # 특징 중요도
    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
    elif hasattr(model, "coef_"):
        imp = np.abs(np.ravel(model.coef_))
    else:
        imp = np.zeros(len(spec.features))
    importance = sorted(
        ({"feature": f, "importance": round(float(v), 4)} for f, v in zip(spec.features, imp)),
        key=lambda d: d["importance"], reverse=True,
    )

    return {
        "spec": spec.model_dump(),
        "samples": {"total": n, "train": split, "test": n - split},
        "metrics": metrics,
        "feature_importance": importance,
    }


# ── 모델 영구 저장 / 로드 / 추론 ────────────────────────────
def train_and_save(spec: PredictSpec, note: str = "") -> dict:
    """평가(테스트 분할) 후, 전체 데이터로 재적합한 최종 모델을 레지스트리에 저장.

    저장 아티팩트는 전체 데이터로 학습(정보 최대 활용), 메트릭은 테스트셋 기준.
    반환: train_and_evaluate 결과 + model_id.
    """
    import io
    import joblib
    from sklearn.preprocessing import StandardScaler
    from shared.db.ml_model import save_model, create_table

    eval_res = train_and_evaluate(spec)   # 테스트셋 메트릭

    X, y = build_xy(load_minute(spec.iscd, spec.limit), spec)
    scaler = StandardScaler().fit(X)
    model = _make_model(spec.model, spec.target, spec.params)
    model.fit(scaler.transform(X), y)

    buf = io.BytesIO()
    joblib.dump(
        {"scaler": scaler, "model": model, "features": spec.features,
         "target": spec.target, "horizon": spec.horizon, "iscd": spec.iscd,
         "model_name": spec.model},
        buf, compress=3,
    )

    create_table()
    model_id = save_model(
        {"iscd": spec.iscd, "target": spec.target, "horizon": spec.horizon,
         "model_name": spec.model, "features": spec.features, "params": spec.params,
         "metrics": eval_res["metrics"], "samples": eval_res["samples"],
         "note": note or spec.note},
        buf.getvalue(),
    )
    return {"model_id": model_id, **eval_res}


def load_model(model_id: str):
    """레지스트리에서 (메타 row, {scaler,model,...}) 로드."""
    import io
    import joblib
    from shared.db.ml_model import get_model
    row = get_model(model_id)
    if not row:
        raise ValueError(f"model_id 없음: {model_id}")
    obj = joblib.load(io.BytesIO(row["artifact"]))
    return row, obj


def _latest_features(df: pd.DataFrame, features: List[str]):
    """최신 봉의 특징 벡터(예측용, 타깃 불필요)."""
    df = df.copy()
    df["ret"] = df["close"].pct_change()
    for f in features:
        df[f] = FEATURES[f](df)
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=features)
    if df.empty:
        raise ValueError("최신 특징 계산 불가(데이터 부족)")
    last = df.iloc[-1]
    return last[features].values.astype(float), last


def predict_latest(model_id: str) -> dict:
    """저장된 모델로 최신 봉 기준 다음 지평 예측(추론)."""
    row, obj = load_model(model_id)
    iscd, feats, target, horizon = obj["iscd"], obj["features"], obj["target"], obj["horizon"]
    df = load_minute(iscd, 400)   # 워밍업 충분한 최근 봉
    x, last = _latest_features(df, feats)
    xs = obj["scaler"].transform(x.reshape(1, -1))

    out: dict = {"model_id": model_id, "iscd": iscd, "target": target, "horizon": horizon,
                 "as_of": str(last["ts"]), "last_close": float(last["close"])}
    if target == "return":
        pred = float(obj["model"].predict(xs)[0])
        out["predicted_return_pct"] = round(pred * 100, 4)
        out["direction"] = "up" if pred > 0 else "down"
    else:
        cls = int(obj["model"].predict(xs)[0])
        out["predicted_direction"] = "up" if cls == 1 else "down"
        if hasattr(obj["model"], "predict_proba"):
            out["prob_up"] = round(float(obj["model"].predict_proba(xs)[0][1]), 4)
    return out
