@echo off
set FLUTTER_PATH=D:\AIProject\StockApp\taiwan_stock_app\flutter\bin
set PATH=%FLUTTER_PATH%;%PATH%

cd /d D:\AIProject\StockApp\taiwan_stock_app\frontend

echo 測試 Flutter 是否可用...
flutter --version

echo.
echo 檢查 Flutter 配置...
flutter doctor

echo.
echo 檢查依賴...
flutter pub get

pause
