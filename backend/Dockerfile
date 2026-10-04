# Сборка выполняется из корня репозитория:
# docker build -f backend/Dockerfile -t foodgram_backend .
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY data/ data/

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]
