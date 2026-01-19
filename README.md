# 台股 AI 投資建議 APP

一個結合 AI 技術的台股投資建議應用程式，提供個人化的股票分析與投資建議。

## 功能特色

- 🔐 使用者註冊與登入
- 📊 股票資訊查詢與即時價格
- ⭐ 自選股管理
- 🤖 AI 每日投資建議（基於 Google Gemini）
- 💬 AI 投資問答助手
- 📈 技術分析與基本面分析

## 技術架構

### 後端
- **框架**: FastAPI
- **資料庫**: PostgreSQL
- **AI 模型**: Google Gemini API
- **認證**: JWT Token
- **容器化**: Docker + Docker Compose

### 前端
- **框架**: Flutter
- **狀態管理**: Provider
- **平台**: Web, iOS, Android

## 前置需求

- Docker Desktop
- Flutter SDK (3.0+)
- Google Gemini API Key

## 快速開始

### 1. 克隆專案

```bash
git clone <repository-url>
cd StockApp/taiwan_stock_app
```

### 2. 設定後端

#### 配置環境變數

編輯 `backend/.env` 文件：

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/taiwan_stock

# API Keys
FINMIND_TOKEN=your_finmind_token_here
FUGLE_API_KEY=your_fugle_api_key_here
GOOGLE_API_KEY=your_google_gemini_api_key

# JWT Secret (使用以下命令生成)
# openssl rand -base64 32
JWT_SECRET=your_secure_jwt_secret

# AI Model
AI_MODEL=gemini-pro-latest
```

#### 取得 Google Gemini API Key

1. 前往 [Google AI Studio](https://aistudio.google.com/apikey)
2. 登入您的 Google 帳號
3. 點擊「Create API Key」
4. 複製 API Key 並貼到 `.env` 的 `GOOGLE_API_KEY`

#### 啟動後端服務

```bash
cd backend
docker compose up -d
```

後端 API 將運行在 `http://localhost:8000`

查看 API 文件：`http://localhost:8000/docs`

### 3. 設定前端

#### 安裝 Flutter 依賴

```bash
cd frontend
flutter pub get
```

#### 啟用 Web 支援（首次運行）

```bash
flutter create --platforms=web .
```

#### 啟動前端應用

```bash
# Web 版本
flutter run -d chrome

# 或指定端口
flutter run -d web-server --web-port 3000
```

## 專案結構

```
taiwan_stock_app/
├── backend/                    # 後端服務
│   ├── app/
│   │   ├── routers/           # API 路由
│   │   │   ├── auth.py        # 認證相關
│   │   │   ├── stocks.py      # 股票查詢
│   │   │   ├── watchlist.py   # 自選股管理
│   │   │   └── ai.py          # AI 建議與問答
│   │   ├── services/          # 業務邏輯
│   │   │   ├── ai_suggestion_service.py
│   │   │   └── ai_chat_service.py
│   │   ├── models.py          # 資料庫模型
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── database.py        # 資料庫連接
│   │   └── config.py          # 配置管理
│   ├── docker-compose.yml     # Docker 配置
│   ├── Dockerfile
│   ├── requirements.txt       # Python 依賴
│   └── .env                   # 環境變數
│
└── frontend/                   # Flutter 前端
    ├── lib/
    │   ├── screens/           # 頁面
    │   │   ├── login_screen.dart
    │   │   ├── home_screen.dart
    │   │   ├── watchlist_screen.dart
    │   │   └── ai_chat_screen.dart
    │   ├── providers/         # 狀態管理
    │   ├── services/          # API 服務
    │   ├── models/            # 資料模型
    │   └── main.dart
    └── pubspec.yaml           # Flutter 配置
```

## API 端點

### 認證
- `POST /api/auth/register` - 註冊新使用者
- `POST /api/auth/login` - 使用者登入
- `GET /api/auth/me` - 取得當前使用者資訊

### 股票
- `GET /api/stocks/search?q={keyword}` - 搜尋股票
- `GET /api/stocks/{stock_id}` - 取得股票詳細資訊
- `GET /api/stocks/{stock_id}/price` - 取得股票即時價格

### 自選股
- `GET /api/watchlist` - 取得自選股清單
- `POST /api/watchlist` - 新增股票到自選股
- `DELETE /api/watchlist/{stock_id}` - 移除自選股

### AI 功能
- `GET /api/ai/suggestions` - 取得所有自選股的 AI 建議
- `GET /api/ai/suggestions/{stock_id}` - 取得特定股票的 AI 建議
- `POST /api/ai/chat` - AI 問答
- `GET /api/ai/chat/history` - 取得對話歷史

## 使用說明

### 首次使用

1. **註冊帳號**
   - 開啟應用程式
   - 點擊「還沒有帳號？註冊」
   - 輸入 Email 和密碼

2. **新增自選股**
   - 使用搜尋功能找到股票
   - 點擊「加入自選股」

3. **查看 AI 建議**
   - 在首頁查看每日 AI 投資建議
   - 包含買賣建議、信心度、目標價等

4. **使用 AI 問答**
   - 點擊 AI 問答功能
   - 輸入投資相關問題
   - 獲得 AI 分析與建議

### 測試帳號

```
Email: test@example.com
Password: test123456
```

## 資料庫管理

### 查看資料庫

```bash
# 連接到 PostgreSQL
docker exec -it backend-db-1 psql -U user -d taiwan_stock

# 常用 SQL 指令
\dt                          # 列出所有資料表
SELECT * FROM users;         # 查看使用者
SELECT * FROM stocks;        # 查看股票資料
SELECT * FROM watchlist;     # 查看自選股
```

### 重置資料庫

```bash
cd backend
docker compose down -v
docker compose up -d
```

## 故障排除

### 後端無法啟動

1. 確認 Docker Desktop 正在運行
2. 檢查 `.env` 檔案是否正確配置
3. 查看日誌：
   ```bash
   docker logs backend-api-1
   ```

### AI 功能無法使用

1. 檢查 Google API Key 是否有效
2. 確認 API 配額未超過
3. 前往 [Google AI Studio](https://aistudio.google.com/apikey) 檢查配額

### 前端無法連接後端

1. 確認後端服務正在運行：`http://localhost:8000/health`
2. 檢查 `frontend/lib/config/app_config.dart` 的 API 位址
3. 清除 Flutter 快取：
   ```bash
   flutter clean
   flutter pub get
   ```

### CORS 錯誤

後端已配置允許所有來源（開發環境），如仍有問題：

1. 檢查 `backend/app/main.py` 的 CORS 設定
2. 確認使用正確的 Authorization header

## 開發說明

### 後端開發

```bash
# 安裝依賴
cd backend
pip install -r requirements.txt

# 本地開發模式（不使用 Docker）
uvicorn app.main:app --reload --port 8000
```

### 前端開發

```bash
cd frontend

# 安裝依賴
flutter pub get

# 執行測試
flutter test

# 建置 Web 版本
flutter build web

# 建置 Android APK
flutter build apk

# 建置 iOS（需要 Mac）
flutter build ios
```

### 新增股票資料

```bash
# 使用 Python 腳本新增測試股票
docker exec backend-api-1 python -c "
from app.database import SessionLocal
from app.models import Stock

db = SessionLocal()
stocks = [
    Stock(stock_id='2330', name='台積電', industry='半導體'),
    Stock(stock_id='2317', name='鴻海', industry='電子'),
]
db.add_all(stocks)
db.commit()
"
```

## 效能優化

- AI 建議會快取 24 小時（每日更新）
- 股票價格快取 1 分鐘
- 使用 PostgreSQL 索引優化查詢
- JWT Token 有效期 7 天

## 安全性

- 密碼使用 bcrypt 加密
- JWT Token 認證
- SQL Injection 防護（使用 SQLAlchemy ORM）
- CORS 設定（生產環境需調整）

## 授權

MIT License

## 聯絡方式

如有問題或建議，請開 Issue。

## 更新日誌

### v1.0.0 (2026-01-20)
- 初始版本發布
- 完成使用者認證系統
- 整合 Google Gemini AI
- 實作自選股管理
- 支援 AI 投資建議與問答

## 致謝

- [Google Gemini](https://ai.google.dev/) - AI 模型
- [FinMind](https://finmind.github.io/) - 台股資料來源
- [FastAPI](https://fastapi.tiangolo.com/) - 後端框架
- [Flutter](https://flutter.dev/) - 前端框架
