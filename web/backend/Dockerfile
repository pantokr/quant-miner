# 빌드 컨텍스트 = 저장소 루트 (docker-compose에서 지정)
FROM python:3.12-slim

WORKDIR /app

COPY web/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY web/__init__.py ./web/__init__.py
COPY web/backend/ ./web/backend/

EXPOSE 8000

CMD ["uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
