# research/

가격예측 ML 연구/학습 코드.

- `predict/` — 설정 주도 가격예측 학습·추론 코어. `research.predict.core`는
  web/backend(ml 라우터·`ml_jobs`)에서 재사용되므로 **배포 경로에 포함**된다.

shared/ 의 데이터 접근(`shared.db`)과 시세 로직(`shared.services`)을 재사용한다.
CLI 실행은 `python -m research.predict.run ...` 형태.
