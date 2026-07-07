"""가격 예측 CLI — 코어(research.predict.core)를 설정으로 호출.

컬럼/특징·모델·지평을 파라미터로 선택해 학습/평가한다.

예:
  python -m research.predict.run --list
  python -m research.predict.run --iscd 005930 --features ret_lag1 ma5 rsi14 volume_z --model random_forest --horizon 30
  python -m research.predict.run --iscd 005930 --target direction --model logistic
"""
import os
import sys
import json
import argparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from research.predict.core import (
    FEATURES, MODELS, DEFAULT_FEATURES, PredictSpec,
    train_and_evaluate, train_and_save, predict_latest,
)
from shared.db.ml_model import list_models


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="사용 가능한 특징/모델 출력")
    ap.add_argument("--iscd", default="005930")
    ap.add_argument("--features", nargs="+", default=list(DEFAULT_FEATURES),
                    help=f"특징 이름들 (기본: {DEFAULT_FEATURES})")
    ap.add_argument("--target", choices=["return", "direction"], default="return")
    ap.add_argument("--model", default="ridge")
    ap.add_argument("--horizon", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0, help="최근 N봉만(0=전체)")
    ap.add_argument("--save", action="store_true", help="학습 후 레지스트리에 저장")
    ap.add_argument("--note", default="", help="저장 메모")
    ap.add_argument("--list-saved", action="store_true", help="저장된 모델 목록")
    ap.add_argument("--predict", metavar="MODEL_ID", help="저장된 모델로 최신 예측")
    args = ap.parse_args()

    if args.list:
        print("사용 가능한 특징 (--features):")
        for f in FEATURES:
            print(f"  - {f}")
        print("\n사용 가능한 모델 (--model), target별:")
        for task, ms in MODELS.items():
            print(f"  {task}: {', '.join(ms)}")
        return

    if args.list_saved:
        rows = list_models(None)
        print(f"저장된 모델 {len(rows)}개:")
        for r in rows:
            m = r["metrics"]
            key = "dir_acc_pct" if "dir_acc_pct" in m else "accuracy_pct"
            print(f"  {r['model_id']}  {r['iscd']} {r['target']}/{r['model_name']} "
                  f"H{r['horizon']} · {key}={m.get(key)} · {r['created_at']}")
        return

    if args.predict:
        out = predict_latest(args.predict)
        print("예측 결과:")
        for k, v in out.items():
            print(f"  {k:<22} {v}")
        return

    spec = PredictSpec(
        iscd=args.iscd, features=args.features, target=args.target,
        model=args.model, horizon=args.horizon, limit=args.limit, note=args.note,
    )
    result = train_and_save(spec, args.note) if args.save else train_and_evaluate(spec)
    if args.save:
        print(f"저장 완료 · model_id = {result['model_id']}")

    s = result["samples"]
    print(f"\n종목 {spec.iscd} · target={spec.target} · model={spec.model} · 지평 {spec.horizon}분")
    print(f"특징({len(spec.features)}): {', '.join(spec.features)}")
    print(f"표본 {s['total']:,} (train {s['train']:,}/test {s['test']:,})")
    print("-" * 60)
    print("메트릭:")
    for k, v in result["metrics"].items():
        print(f"  {k:<24} {v}")
    print("특징 중요도 (상위):")
    for row in result["feature_importance"][:8]:
        print(f"  {row['feature']:<14} {row['importance']}")


if __name__ == "__main__":
    main()
