@echo off
cd /d D:\AIProject\StockApp\taiwan_stock_app\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
