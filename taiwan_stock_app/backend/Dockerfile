FROM python:3.11-slim

WORKDIR /app

# 建立非 root 使用者（生產安全）
RUN adduser --disabled-password --gecos '' appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# 切換到非 root 使用者
USER appuser

# Expose port (Railway 動態指定)
EXPOSE ${PORT:-8000}

# Run application — 使用 gunicorn + uvicorn workers
CMD gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}
