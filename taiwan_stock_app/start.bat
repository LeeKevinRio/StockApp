@echo off
echo ====================================
echo 台股 AI 投資建議 APP 啟動腳本
echo ====================================
echo.

REM 檢查 Docker 是否運行
echo [1/3] 檢查 Docker 狀態...
docker info >nul 2>&1
if errorlevel 1 (
    echo [錯誤] Docker 未運行，請先啟動 Docker Desktop
    pause
    exit /b 1
)
echo [成功] Docker 正在運行

REM 啟動後端服務
echo.
echo [2/3] 啟動後端服務...
cd backend
docker compose up -d
if errorlevel 1 (
    echo [錯誤] 後端啟動失敗
    pause
    exit /b 1
)
echo [成功] 後端服務已啟動

REM 等待後端啟動
echo 等待後端服務啟動 (10秒)...
timeout /t 10 /nobreak >nul

REM 啟動前端
echo.
echo [3/3] 啟動前端應用...
cd ..\frontend

REM 使用完整的 Flutter 路徑
set FLUTTER_PATH=D:\AIProject\StockApp\taiwan_stock_app\flutter\bin\flutter.bat

echo 正在啟動 Flutter Web 應用...
echo 應用將在 Chrome 瀏覽器開啟，請稍候...
echo.
start "" cmd /k "%FLUTTER_PATH% run -d chrome --web-port 3000"

echo.
echo ====================================
echo 啟動完成！
echo ====================================
echo.
echo 後端 API: http://localhost:8000
echo API 文件: http://localhost:8000/docs
echo 前端應用: http://localhost:3000
echo.
echo 測試帳號：
echo   Email: test@example.com
echo   密碼: test123456
echo.
echo 按任意鍵關閉此視窗...
pause >nul
