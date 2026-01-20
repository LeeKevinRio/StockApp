@echo off
chcp 65001 >nul
cls
echo ========================================
echo   台股 AI 投資建議 APP - 前端啟動
echo ========================================
echo.

set FLUTTER_PATH=D:\AIProject\StockApp\taiwan_stock_app\flutter\bin
set PATH=%FLUTTER_PATH%;%PATH%

cd /d "%~dp0frontend"

echo 正在啟動 Flutter Web...
echo 編譯完成後 Chrome 會自動開啟應用
echo.
echo 提示：首次啟動可能需要 1-2 分鐘編譯
echo.

flutter run -d chrome --web-port 3000

echo.
echo Flutter 已結束
pause
