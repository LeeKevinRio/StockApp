# 快速啟動指南

## 完成進度: 約 95%

已完成的功能模組:
- ✅ Backend 完整架構 (FastAPI + PostgreSQL)
- ✅ 資料庫 Models & Schemas
- ✅ 外部 API 整合 (FinMind, Fugle, TWSE)
- ✅ AI Services (投資建議 & 問答)
- ✅ 完整的 REST API 端點
- ✅ JWT 認證系統
- ✅ Flutter 前端框架
- ✅ 狀態管理 (Provider)
- ✅ 核心頁面 (登入、自選股、AI問答)
- ✅ Docker 部署配置

未包含的 5% (可自行擴充):
- 股票資料初始化腳本 (需匯入台股清單)
- AI 每日建議頁面 (UI 已有框架，需整合)
- 詳細的錯誤處理與日誌
- 單元測試
- 部分 UI 優化與動畫

## 立即啟動

### 1. 後端啟動 (3 分鐘)

```bash
# 進入後端目錄
cd backend

# 複製環境變數範例
cp .env.example .env

# 編輯 .env 填入你的 API Keys
# 至少需要: OPENAI_API_KEY 和 JWT_SECRET

# 使用 Docker 啟動 (推薦)
docker-compose up -d

# 檢查服務狀態
curl http://localhost:8000/health

# 查看 API 文件
# 瀏覽器開啟: http://localhost:8000/docs
```

### 2. 前端啟動 (2 分鐘)

```bash
# 進入前端目錄
cd frontend

# 安裝依賴
flutter pub get

# 運行應用 (選擇裝置)
flutter run

# 或指定裝置
flutter run -d chrome        # 網頁版
flutter run -d windows       # Windows 桌面
flutter run -d android       # Android 模擬器
```

### 3. 初次使用流程

1. **註冊帳號**
   - 開啟 APP 後點選「註冊」
   - 輸入 Email 和密碼
   - 成功後自動登入

2. **新增自選股**
   - 點選右上角 「+」 圖示
   - 輸入股票代碼 (例如: 2330)
   - 注意: 需先在資料庫中有該股票資料

3. **體驗 AI 問答**
   - 點選底部「AI 問答」頁籤
   - 輸入問題，例如:
     - "最近台股走勢如何?"
     - "什麼是技術分析?"

## 資料庫初始化

後端首次啟動會自動建立資料表，但需要手動匯入股票清單:

### 方法 1: 使用 FinMind API 匯入

```python
# 在 backend 目錄下執行
python -c "
from app.data_fetchers import FinMindFetcher
from app.database import SessionLocal
from app.models import Stock
import os

finmind = FinMindFetcher(os.getenv('FINMIND_TOKEN'))
stocks_df = finmind.get_stock_list()

db = SessionLocal()
for _, row in stocks_df.iterrows():
    stock = Stock(
        stock_id=row['stock_id'],
        name=row['stock_name'],
        market=row['market_type'],
        industry=row.get('industry_category', '')
    )
    db.add(stock)
db.commit()
print('股票清單匯入完成!')
"
```

### 方法 2: 手動新增測試股票

使用 API 文件 (http://localhost:8000/docs) 直接在 PostgreSQL 插入:

```sql
INSERT INTO stocks (stock_id, name, market, industry) VALUES
('2330', '台積電', 'TWSE', '半導體業'),
('2317', '鴻海', 'TWSE', '電腦及週邊設備業'),
('2454', '聯發科', 'TWSE', '半導體業');
```

## 開發提示

### Backend 開發

```bash
# 本地開發 (不用 Docker)
pip install -r requirements.txt
uvicorn app.main:app --reload

# 查看日誌
docker-compose logs -f api

# 進入資料庫
docker-compose exec db psql -U user -d taiwan_stock
```

### Frontend 開發

```bash
# 熱重載開發
flutter run

# 生成 APK
flutter build apk

# 程式碼格式化
flutter format lib/

# 分析程式碼
flutter analyze
```

## 常見問題

### Q: 無法連接到後端 API

A: 檢查以下項目:
1. 後端是否正常運行: `curl http://localhost:8000/health`
2. 前端 API 配置是否正確 (lib/config/app_config.dart)
3. 如果用模擬器，改為 `http://10.0.2.2:8000` (Android)

### Q: AI 回應錯誤或很慢

A: 確認:
1. OPENAI_API_KEY 是否正確設定
2. 帳戶餘額是否足夠
3. 可考慮改用 gpt-4o-mini 降低成本

### Q: 找不到股票

A: 需先執行資料庫初始化，匯入股票清單 (見上方說明)

## 下一步

1. **擴充功能**
   - 實作 AI 每日建議頁面
   - 新增股票詳情頁 (K線圖、技術指標)
   - 加入價格警示功能

2. **優化體驗**
   - 加入載入動畫
   - 優化錯誤提示
   - 支援深色模式

3. **部署上線**
   - 使用雲端資料庫 (AWS RDS, Google Cloud SQL)
   - 部署後端到雲端 (Heroku, Railway, Fly.io)
   - 發布 APP 到 Google Play Store

## 技術支援

如遇到問題:
1. 檢查 Docker logs: `docker-compose logs`
2. 查看 FastAPI 自動文件: http://localhost:8000/docs
3. 參考 README.md 的詳細說明

---

祝你開發順利! 🚀
