#!/bin/bash

# Quant Miner 배포 스크립트
# 사용법: ./deploy.sh

echo ">>> [1/3] Git Pull (최신 코드 가져오기)..."
git pull origin main

echo ">>> [2/3] Docker Compose 빌드 및 실행 (db, api, backend)..."
# 특정 서비스만 실행하도록 설정 (필요 시 전체 실행은 'up -d --build'로 수정)
sudo docker compose up -d --build db api backend

echo ">>> [3/3] 실행 상태 확인..."
sudo docker compose ps

echo ">>> 배포 완료!"
echo "로그 확인: sudo docker compose logs -f backend"
