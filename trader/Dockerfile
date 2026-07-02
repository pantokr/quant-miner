# 빌드 컨텍스트 = 저장소 루트 (docker-compose에서 지정)
FROM python:3.12-slim

WORKDIR /app

COPY trader/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY trader/ ./trader/

CMD ["python", "-m", "trader.main", "--loop"]
