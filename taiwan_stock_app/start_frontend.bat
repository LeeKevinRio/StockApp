@echo off
echo ========================================
echo 台股 AI 投資建議 APP - 前端啟動
echo ========================================
echo.

cd /d "%~dp0frontend"

echo 正在啟動 Flutter Web...
echo.
flutter run -d chrome --web-port 5000

pause
