#!/bin/bash
#
# Quant Miner 배포 스크립트 (서버에서 실행)
#
#   ./deploy.sh              최신 코드로 재빌드·재기동
#   ./deploy.sh --fresh      컨테이너를 내렸다가 새로 올림 (설정/네트워크 꼬였을 때)
#   ./deploy.sh --clean      --fresh + 이미지 캐시 무시하고 처음부터 빌드
#   ./deploy.sh --no-pull    git pull 없이 현재 코드로만 재기동
#   ./deploy.sh --master     기동 후 종목 마스터 적재까지 수행
#
# db 볼륨(pgdata)은 어떤 옵션에서도 건드리지 않는다 — 데이터는 보존된다.
#
set -euo pipefail

cd "$(dirname "$0")"

FRESH=0; CLEAN=0; PULL=1; MASTER=0
for arg in "$@"; do
  case "$arg" in
    --fresh)   FRESH=1 ;;
    --clean)   FRESH=1; CLEAN=1 ;;
    --no-pull) PULL=0 ;;
    --master)  MASTER=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "알 수 없는 옵션: $arg"; exit 1 ;;
  esac
done

# docker 권한 — 사용자가 docker 그룹에 없으면 sudo로 붙는다
if docker info >/dev/null 2>&1; then
  DC="docker compose"
else
  DC="sudo docker compose"
fi

SERVICES="db api backend"

step() { echo; echo ">>> $*"; }

if [ "$PULL" = "1" ]; then
  step "[1] 최신 코드 가져오기"
  git pull --ff-only
else
  step "[1] git pull 생략 (--no-pull)"
fi
echo "    현재 커밋: $(git rev-parse --short HEAD) $(git log -1 --pretty=%s)"

if [ ! -f .env ]; then
  echo "!!! .env 가 없습니다. KIS 키/DB 설정이 필요합니다." >&2
  exit 1
fi

if [ "$FRESH" = "1" ]; then
  step "[2] 기존 컨테이너 정리 (볼륨은 유지)"
  $DC down --remove-orphans
fi

step "[3] 빌드 및 기동"
if [ "$CLEAN" = "1" ]; then
  $DC build --no-cache $SERVICES
fi
$DC up -d --build $SERVICES

step "[4] 헬스 체크"
ok=0
for i in $(seq 1 30); do
  if curl -fsS -m 3 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    ok=1; break
  fi
  sleep 2
done

if [ "$ok" = "1" ]; then
  echo "    backend  : OK (http://127.0.0.1:8000/health)"
  # 이번 배포로 들어간 라우트가 실제로 살아 있는지 확인
  if curl -fsS -m 5 "http://127.0.0.1:8000/stock/search?q=삼성" >/dev/null 2>&1; then
    echo "    종목검색 : OK"
  else
    echo "    종목검색 : 응답 없음 — stock_master 미적재일 수 있습니다 (./deploy.sh --master)"
  fi
else
  echo "!!! backend 헬스 체크 실패 — 로그를 확인하세요" >&2
  $DC logs --tail 40 backend >&2 || true
  exit 1
fi

if [ "$MASTER" = "1" ]; then
  step "[5] 종목 마스터 적재"
  $DC exec -T api python scripts/load_stock_master.py
fi

step "상태"
$DC ps

echo
echo ">>> 배포 완료 ($(git rev-parse --short HEAD))"
echo "    로그: $DC logs -f backend"
