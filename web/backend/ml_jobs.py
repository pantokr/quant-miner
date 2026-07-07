"""ML 학습 비동기 잡 매니저 (인메모리 프로토타입).

학습은 무겁고 오래 걸리므로 백그라운드 스레드로 실행하고, 요청은 job_id만 즉시 반환한다.
상태/결과는 폴링(GET /ml/jobs/{id})으로 확인.

주의(프로토타입): 잡 저장소가 인메모리(단일 프로세스)라 재시작하면 사라진다.
실전에서는 Redis/DB 잡 저장소 + 워커(Celery/RQ) 또는 별도 ml 서비스로 승격 권장.
"""
import uuid
import threading
from datetime import datetime, timezone
from typing import Dict, Optional

from research.predict.core import train_and_evaluate, train_and_save, PredictSpec

_JOBS: Dict[str, dict] = {}
_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def submit(spec: PredictSpec) -> str:
    jid = uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[jid] = {
            "id": jid, "status": "pending", "spec": spec.model_dump(),
            "result": None, "error": None,
            "created_at": _now(), "finished_at": None,
        }
    threading.Thread(target=_run, args=(jid, spec), daemon=True).start()
    return jid


def _run(jid: str, spec: PredictSpec) -> None:
    with _LOCK:
        _JOBS[jid]["status"] = "running"
    try:
        res = train_and_save(spec, spec.note) if spec.save else train_and_evaluate(spec)
        with _LOCK:
            _JOBS[jid]["status"] = "done"
            _JOBS[jid]["result"] = res
    except Exception as e:
        with _LOCK:
            _JOBS[jid]["status"] = "error"
            _JOBS[jid]["error"] = str(e)
    finally:
        with _LOCK:
            _JOBS[jid]["finished_at"] = _now()


def get(jid: str) -> Optional[dict]:
    with _LOCK:
        return _JOBS.get(jid)
