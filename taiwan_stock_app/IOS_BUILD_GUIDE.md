# iOS App Store 上架指南

## 前置需求

1. **Apple Developer Account** ($99/年)
   - 註冊：https://developer.apple.com/programs/

2. **Mac 電腦**（含 Xcode 15+）

3. **Flutter SDK** 已安裝在 Mac 上

## 步驟一：設定 Xcode 簽名

1. 用 Xcode 開啟 `frontend/ios/Runner.xcworkspace`
2. 選擇 **Runner** target
3. 在 **Signing & Capabilities** 中：
   - 勾選 **Automatically manage signing**
   - 選擇你的 **Team**（Apple Developer 帳號）
   - Bundle Identifier 已設為：`com.stockai.app`
4. 確認沒有簽名錯誤

## 步驟二：設定 App Store Connect

1. 登入 https://appstoreconnect.apple.com/
2. 建立新 App：
   - 名稱：`台股智慧助手`
   - Bundle ID：`com.stockai.app`
   - SKU：`stockai-app`
   - 主要語言：繁體中文
3. 填寫 App 資訊：
   - **類別**：財經
   - **年齡分級**：17+（因涉及金融投資）
   - **隱私權政策 URL**：`https://stockapp-production-0b90.up.railway.app/privacy`
   - **App 描述**（建議）：

```
台股智慧助手 — AI 驅動的台灣股票投資分析工具

主要功能：
- 台股/美股即時行情查詢
- AI 智慧分析每日投資建議
- 六維度技術/基本面綜合分析
- 投資組合損益追蹤
- K 線圖搭配多種技術指標
- 股價警示即時通知
- 交易日記記錄投資心得
- PTT/Reddit 社群情緒分析
- 策略回測引擎

免費版使用 Gemini Flash 模型
Pro 版使用 Gemini Pro 模型深度分析

重要聲明：本應用程式提供的所有資訊及 AI 分析結果僅供參考，不構成投資建議。投資涉及風險，請謹慎評估。
```

   - **關鍵字**：台股,股票,AI,投資,分析,美股,自選股,技術分析,投資組合

## 步驟三：截圖準備

需要以下尺寸的截圖（至少 3 張，建議 5-6 張）：
- iPhone 6.7" (1290 x 2796) — iPhone 15 Pro Max
- iPhone 6.5" (1284 x 2778) — iPhone 14 Pro Max
- iPad 12.9" (2048 x 2732) — 如果支援 iPad

建議截圖內容：
1. 首頁儀表板（市場概況）
2. AI 投資建議頁面
3. 個股 K 線圖技術分析
4. 投資組合管理
5. AI 聊天對話
6. 策略回測結果

## 步驟四：建置 iOS Release

```bash
cd taiwan_stock_app/frontend

# 安裝依賴
flutter pub get

# 建置 iOS Release（連接 Railway 後端）
flutter build ios --release \
  --dart-define=API_BASE_URL=https://stockapp-production-0b90.up.railway.app

# 或使用 Xcode 建置
open ios/Runner.xcworkspace
# 在 Xcode 中選擇 Product > Archive
```

## 步驟五：上傳到 App Store Connect

### 方法 A：使用 Xcode
1. Product > Archive
2. 等待 Archive 完成
3. Distribute App > App Store Connect
4. 選擇 Upload
5. 完成上傳

### 方法 B：使用命令列
```bash
# 建置 IPA
flutter build ipa --release \
  --dart-define=API_BASE_URL=https://stockapp-production-0b90.up.railway.app \
  --export-options-plist=ios/ExportOptions.plist

# 上傳（需先修改 ExportOptions.plist 中的 teamID）
xcrun altool --upload-app \
  --type ios \
  --file build/ios/ipa/台股智慧助手.ipa \
  --apiKey YOUR_API_KEY \
  --apiIssuer YOUR_ISSUER_ID
```

## 步驟六：提交審核

1. 在 App Store Connect 選擇已上傳的 Build
2. 填寫審核資訊：
   - **審核備註**：提供測試帳號（email + 密碼）供審核團隊使用
   - **聯絡資訊**：你的聯絡方式
3. 點擊 **Submit for Review**

## 審核注意事項

- Apple 審核通常需要 1-3 個工作天
- 金融類 App 可能需要額外說明：
  - 非專業投資顧問服務
  - AI 分析僅供參考
  - 用戶需自行承擔投資風險
- 確保帳號刪除功能正常運作（Apple 強制要求）
- 確保隱私權政策 URL 可公開存取

## Google Sign-In iOS 設定

如果要啟用 iOS 上的 Google 登入：
1. 到 Google Cloud Console
2. 建立 iOS OAuth 用戶端 ID
3. Bundle ID 填入 `com.stockai.app`
4. 下載 `GoogleService-Info.plist` 放到 `ios/Runner/`
5. 更新 Info.plist 中的 URL Scheme

## 常見問題

### Q: 審核被拒怎麼辦？
A: 查看 Resolution Center 的具體原因，針對性修改後重新提交。

### Q: 需要付費的 API Key 嗎？
A: Railway 後端已部署，需在 Railway 環境變數設定：
- `GOOGLE_API_KEY`（Gemini AI 必需）
- `GROQ_API_KEY`（AI fallback）
- `JWT_SECRET`（固定密鑰，避免重啟後用戶需重新登入）
