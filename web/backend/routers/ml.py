"""ML 라우터 — 설정 주도 가격예측 학습(비동기 잡).

프론트/CLI가 특징·모델·지평을 골라 학습을 제출하고 결과를 폴링한다.
학습 코어는 research.predict.core 공용.
"""
from fastapi import APIRouter, HTTPException

from typing import Optional

from research.predict.core import FEATURES, MODELS, DEFAULT_FEATURES, PredictSpec, predict_latest
from shared.db.ml_model import list_models, delete_model
from web.backend import ml_jobs

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/features")
def list_features():
    """선택 가능한 특징 카탈로그 + 기본 선택."""
    return {"features": list(FEATURES.keys()), "default": list(DEFAULT_FEATURES)}


@router.get("/models")
def list_models():
    """target별 사용 가능한 모델."""
    return MODELS


@router.post("/train")
def train(spec: PredictSpec):
    """학습 제출 → job_id 즉시 반환(비동기)."""
    if spec.model not in MODELS.get(spec.target, []):
        raise HTTPException(400, f"target={spec.target}에 model={spec.model} 불가. 가능: {MODELS.get(spec.target)}")
    unknown = [f for f in spec.features if f not in FEATURES]
    if unknown:
        raise HTTPException(400, f"알 수 없는 특징: {unknown}")
    jid = ml_jobs.submit(spec)
    return {"job_id": jid, "status": "pending"}


@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    """잡 상태/결과 폴링."""
    j = ml_jobs.get(job_id)
    if not j:
        raise HTTPException(404, "job not found")
    return j


# ── 모델 레지스트리 ─────────────────────────────────────────
@router.get("/models/saved")
def saved_models(iscd: Optional[str] = None, limit: int = 50):
    """저장된 모델 목록(아티팩트 제외)."""
    return list_models(iscd, limit)


@router.post("/models/{model_id}/predict")
def model_predict(model_id: str):
    """저장된 모델로 최신 봉 기준 예측(추론)."""
    try:
        return predict_latest(model_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/models/{model_id}")
def model_delete(model_id: str):
    if not delete_model(model_id):
        raise HTTPException(404, "model not found")
    return {"deleted": model_id}
