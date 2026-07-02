# research/

로컬/Colab 전용 연구 코드. **배포 대상이 아니며** docker-compose에도 포함되지 않는다.

- `backtest/` — 전략 백테스트
- `rl_train/` — 강화학습 학습 스크립트

shared/ 의 데이터 접근(`shared.db`)과 시세 로직(`shared.services`)을 재사용할 수 있다.
루트에서 `python -m research.backtest...` 형태로 실행.
