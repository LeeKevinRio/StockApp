@echo off
chcp 65001 >nul
cls
echo ========================================
echo   台股 AI 投資建議 APP - 快速啟動
echo ========================================
echo.

cd /d "%~dp0frontend"

echo 正在清理快取...
call flutter clean >nul 2>&1

echo 正在取得依賴...
call flutter pub get

echo.
echo 正在啟動 Flutter Web (Debug 模式)...
echo 請等待編譯完成，Chrome 會自動開啟
echo.

flutter run -d chrome --web-renderer html --web-port 5000

pause
