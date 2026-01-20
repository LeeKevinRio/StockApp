@echo off
echo ====================================
echo 台股 AI 投資建議 APP 停止腳本
echo ====================================
echo.

echo [1/2] 停止後端服務...
cd backend
docker compose down
if errorlevel 1 (
    echo [警告] 後端停止時發生錯誤
) else (
    echo [成功] 後端服務已停止
)

echo.
echo [2/2] 關閉 Flutter 進程...
taskkill /F /IM dart.exe 2>nul
taskkill /F /IM flutter.bat 2>nul
echo [完成] Flutter 進程已關閉

echo.
echo ====================================
echo 所有服務已停止
echo ====================================
echo.
pause
