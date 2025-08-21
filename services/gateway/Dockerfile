FROM python:3.11-slim AS base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY gateway/ gateway/

RUN useradd --create-home appuser
USER appuser

RUN mkdir -p /home/appuser/uploads \
             /home/appuser/vector_data \
             /home/appuser/logs

ENV UPLOAD_DIR=/home/appuser/uploads \
    VECTOR_STORE_PATH=/home/appuser/vector_data \
    LOG_DIRECTORY=/home/appuser/logs \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s \
    --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/alive || exit 1

CMD ["uvicorn", "gateway.server:app", \
     "--host", "0.0.0.0", "--port", "8000"]
