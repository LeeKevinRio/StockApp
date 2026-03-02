@echo off
chcp 65001 >nul
echo ========================================
echo   台股 AI 投資建議 APP - 完整啟動
echo ========================================
echo.

REM 檢查 Docker Desktop
echo [1/3] 檢查 Docker Desktop...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Desktop 未運行
    echo 請先啟動 Docker Desktop，然後重新執行此腳本
    pause
    exit /b 1
)
echo ✅ Docker Desktop 運行中
echo.

REM 啟動後端
echo [2/3] 啟動後端服務...
cd /d "%~dp0backend"
docker compose up -d
if %errorlevel% neq 0 (
    echo ❌ 後端啟動失敗
    pause
    exit /b 1
)
echo ✅ 後端服務已啟動
echo    - API: http://localhost:8000
echo    - 文檔: http://localhost:8000/docs
echo.

REM 等待後端就緒
echo 等待後端服務就緒...
ping 127.0.0.1 -n 10 >nul
echo.

REM 啟動前端
echo [3/3] 啟動前端應用...
set FLUTTER_PATH=%~dp0flutter\bin
set PATH=%FLUTTER_PATH%;%PATH%
cd /d "%~dp0frontend"
echo.
echo 正在編譯 Flutter Web，請稍候...
echo Chrome 瀏覽器將自動開啟應用
echo.
echo ========================================
echo   提示: 首次編譯可能需要 1-2 分鐘
echo   請勿關閉此視窗
echo ========================================
echo.

flutter run -d chrome --web-port 5000

echo.
echo ✅ 應用啟動中...
echo.
echo 測試帳號：
echo   Email: test@example.com
echo   密碼: test123456
echo.
echo 按任意鍵關閉此視窗（前端將繼續運行）
pause >nul
