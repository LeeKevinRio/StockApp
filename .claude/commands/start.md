---
name: start
description: 啟動前後端開發伺服器
---

# 啟動前後端開發伺服器

啟動 StockApp 的前端和後端開發伺服器。

## 步驟

1. **啟動後端** FastAPI (port 8000):
   - 進入 `taiwan_stock_app/backend/` 目錄
   - 執行 `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
   - 在背景執行，等待 5 秒確認啟動成功
   - 用 `curl -s http://localhost:8000/docs -o /dev/null -w "%{http_code}"` 驗證回傳 200

2. **啟動前端** Flutter Web (port 5000):
   - 進入 `taiwan_stock_app/frontend/` 目錄
   - 執行 `flutter run -d chrome --web-port 5000`
   - 在背景執行

3. **回報結果**:
   - 後端 API: http://localhost:8000
   - 後端文件: http://localhost:8000/docs
   - 前端應用: http://localhost:5000

## 重要規則
- 前端 port 固定 **5000**，後端 port 固定 **8000**，禁止變更
- 如果 port 被佔用，先嘗試 kill 佔用的 process，不要換 port
