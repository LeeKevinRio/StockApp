#!/bin/bash
# Web Release 建置腳本
# 使用方式: ./scripts/build_web.sh [API_URL]

set -e

API_URL="${1:-https://your-app.up.railway.app}"
GOOGLE_CLIENT_ID="${2:-${GOOGLE_CLIENT_ID:-}}"

echo "=== 台股智慧助手 Web Release Build ==="
echo "API URL: $API_URL"
echo "Google Client ID: ${GOOGLE_CLIENT_ID:+(set)}"

cd "$(dirname "$0")/../frontend"

# 清理舊 build
flutter clean

# 取得依賴
flutter pub get

# 建置 Web Release
flutter build web --release \
  --dart-define=API_BASE_URL="$API_URL" \
  --dart-define=GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID"

echo ""
echo "=== Build 完成 ==="
echo "輸出位置: build/web/"
echo "可直接部署至任何靜態檔案伺服器"
