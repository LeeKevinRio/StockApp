FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴（cryptography、aiohttp 等 C 擴展需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 建立非 root 使用者（生產安全）
RUN adduser --disabled-password --gecos '' appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# 切換到非 root 使用者
USER appuser

EXPOSE 8000

# 使用 uvicorn 直接啟動（比 gunicorn 更簡單、省記憶體）
# 錯誤會直接輸出到 stdout/stderr
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]
