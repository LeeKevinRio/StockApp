#!/bin/bash
# iOS Release 建置腳本
# 使用方式: ./scripts/build_ios.sh [API_URL]

set -e

API_URL="${1:-https://your-app.up.railway.app}"

echo "=== 台股智慧助手 iOS Release Build ==="
echo "API URL: $API_URL"

cd "$(dirname "$0")/../frontend"

# 清理舊 build
flutter clean

# 取得依賴
flutter pub get

# 建置 iOS Release（不含 codesign，CI/CD 或 Xcode 再簽名）
flutter build ios --release --no-codesign \
  --dart-define=API_BASE_URL="$API_URL"

echo ""
echo "=== Build 完成 ==="
echo "輸出位置: build/ios/iphoneos/Runner.app"
echo "下一步: 用 Xcode 開啟 ios/Runner.xcworkspace 進行簽名與上傳"
