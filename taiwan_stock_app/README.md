# 台股 AI 投資建議 APP

一款整合 AI 技術的台股投資輔助應用，提供自選股管理、AI 每日建議與智能問答功能。

## 技術棧

- **前端**: Flutter (Dart)
- **後端**: Python FastAPI
- **資料庫**: PostgreSQL
- **AI**: OpenAI GPT-4o
- **數據源**: FinMind API, Fugle API

## 核心功能

### P0 功能 (MVP)

1. **自選股管理**
   - 新增/刪除自選股
   - 顯示即時報價與漲跌幅
   - 下拉刷新更新報價

2. **AI 每日建議**
   - 每日盤後分析自選股
   - 提供買/賣/持有建議
   - 包含信心度、目標價、停損價
   - 詳細分析理由與關鍵因素

3. **AI 問答**
   - 針對特定股票或市場提問
   - AI 根據即時數據回答
   - 保留對話歷史

## 專案結構

```
taiwan_stock_app/
├── backend/                 # FastAPI 後端
│   ├── app/
│   │   ├── main.py         # 主應用程式
│   │   ├── config.py       # 配置
│   │   ├── database.py     # 資料庫設定
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── routers/        # API 路由
│   │   ├── services/       # 業務邏輯
│   │   └── data_fetchers/  # 外部 API 整合
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── frontend/               # Flutter 前端
    ├── lib/
    │   ├── main.dart
    │   ├── config/         # 配置
    │   ├── models/         # 數據模型
    │   ├── services/       # API 服務
    │   ├── providers/      # 狀態管理
    │   ├── screens/        # 頁面
    │   └── widgets/        # UI 組件
    └── pubspec.yaml
```

## 快速開始

### 後端設定

1. **環境變數設定**

複製 `.env.example` 為 `.env` 並填入 API Keys:

```bash
cd backend
cp .env.example .env
```

編輯 `.env` 檔案:
```
DATABASE_URL=postgresql://user:password@localhost:5432/taiwan_stock
FINMIND_TOKEN=your_finmind_token
FUGLE_API_KEY=your_fugle_api_key
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_secret_key
```

2. **使用 Docker Compose 啟動**

```bash
docker-compose up -d
```

API 將在 http://localhost:8000 運行
API 文件: http://localhost:8000/docs

3. **本地開發 (不使用 Docker)**

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動服務
uvicorn app.main:app --reload
```

### 前端設定

1. **安裝依賴**

```bash
cd frontend
flutter pub get
```

2. **配置 API 端點**

編輯 `lib/config/app_config.dart`:
```dart
static const String apiBaseUrl = 'http://localhost:8000';
```

3. **運行應用**

```bash
flutter run
```

## API 端點

### 認證
- `POST /api/auth/register` - 用戶註冊
- `POST /api/auth/login` - 用戶登入
- `GET /api/auth/me` - 取得當前用戶資訊

### 股票
- `GET /api/stocks/search?q={keyword}` - 搜尋股票
- `GET /api/stocks/{stock_id}` - 取得股票詳情
- `GET /api/stocks/{stock_id}/price` - 取得即時報價
- `GET /api/stocks/{stock_id}/history` - 取得歷史 K 線

### 自選股
- `GET /api/watchlist` - 取得自選股列表
- `POST /api/watchlist` - 新增自選股
- `DELETE /api/watchlist/{stock_id}` - 刪除自選股

### AI
- `GET /api/ai/suggestions` - 取得 AI 每日建議（所有自選股）
- `GET /api/ai/suggestions/{stock_id}` - 取得單一股票 AI 建議
- `POST /api/ai/chat` - AI 問答
- `GET /api/ai/chat/history` - 取得對話歷史

## 資料來源

- **FinMind**: 歷史股價、籌碼資料、月營收
- **Fugle API**: 即時報價（建議，延遲 < 5 秒）
- **證交所 OpenAPI**: 備用即時報價（延遲 5-20 秒）

## 開發注意事項

### API Keys 申請

1. **FinMind**: https://finmindtrade.com/
   - 免費方案可用於個人開發
   - 需註冊並取得 Token

2. **Fugle API**: https://developer.fugle.tw/
   - 免費方案: 60 次/分鐘
   - 需註冊並取得 API Key

3. **OpenAI API**: https://platform.openai.com/
   - 需付費使用 GPT-4o
   - 可使用其他模型降低成本

### 風險提示

**重要**: 本應用提供的投資建議僅供參考，不構成任何投資決策依據。
- 投資涉及風險，股票價格可升可跌
- 過往表現不代表未來回報
- 用戶應根據自身財務狀況和投資目標審慎評估

## 授權與法規

- FinMind: 免費用戶可用於個人與學術用途
- Fugle API: 免費方案可用於個人開發
- 證交所資料: 公開資料可自由使用
- 遵循台灣《個人資料保護法》

## 後續擴充

### Phase 2
- 價格警示通知 (Push Notification)
- 技術指標圖表 (K 線、MA、RSI)
- 新聞整合

### Phase 3
- 社群情緒分析 (PTT 爬蟲 + NLP)
- 模擬交易功能
- 投資組合追蹤

## 聯絡方式

如有問題或建議，歡迎提出 Issue。

---

**版本**: 1.0.0
**最後更新**: 2026-01-19
