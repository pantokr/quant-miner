# 빌드 컨텍스트 = 저장소 루트 (docker-compose에서 지정)
FROM python:3.12-slim

WORKDIR /app

COPY collector/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY collector/ ./collector/

# 기본은 단발 실행. 루프 실행은 compose command로 --loop 지정.
CMD ["python", "-m", "collector.main", "--loop"]
