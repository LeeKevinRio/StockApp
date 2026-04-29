# 每日盤前摘要郵件服務 - 檔案索引與快速參考

## 📁 新增檔案結構

```
StockApp/
├── DAILY_SUMMARY_SETUP.md                          [完整設置指南 - 355 行]
├── DAILY_SUMMARY_INDEX.md                          [本檔案]
└── taiwan_stock_app/backend/app/
    ├── services/
    │   ├── daily_summary_service.py               [核心服務 - 985 行] ⭐
    │   └── __init__.py                            [已更新，新增匯入]
    └── config/
        └── scheduler_config.py                     [APScheduler 配置 - 259 行]
```

## 🎯 DailySummaryService 類別速查表

### 初始化
```python
from app.services.daily_summary_service import daily_summary_service

# 或建立新實例
from app.services.daily_summary_service import DailySummaryService
service = DailySummaryService()
```

### 核心方法

| 方法 | 說明 | 回傳值 | 備註 |
|------|------|--------|------|
| `generate_summary()` | 生成完整摘要 | `Dict` | **非同步**，耗時 5-15 秒 |
| `send_email(data)` | 發送摘要郵件 | `bool` | **非同步**，需要 SMTP 配置 |
| `schedule_daily_summary()` | 一鍵生成+發送 | `bool` | **非同步**，適合定時任務 |
| `send_test_email(email?)` | 發送測試郵件 | `bool` | **非同步**，驗證 SMTP 配置 |

### 內部方法 (可選了解)

| 方法 | 用途 |
|------|------|
| `_get_us_market_summary()` | 美股數據 (S&P 500, Nasdaq, Dow, VIX) |
| `_get_international_news()` | 國際新聞 Top 5 |
| `_get_taiwan_news()` | 台灣新聞 Top 5 |
| `_get_macro_indicators()` | 宏觀指標 (Fed, 公債, 匯率) |
| `_get_social_sentiment()` | 社群情緒 (PTT/Threads) |
| `_get_key_events()` | 今日重點事件 |
| `_get_ai_watchlist_alerts()` | AI 預測警報 |
| `_build_html_email(data)` | 構建 HTML 郵件 |

## ⚙️ SchedulerConfig 快速參考

### 快速初始化 (推薦)
```python
from fastapi import FastAPI
from app.config.scheduler_config import initialize_scheduler

app = FastAPI()
initialize_scheduler(app)  # 完成！
```

### 進階配置
```python
from app.config.scheduler_config import initialize_scheduler

app = FastAPI()

# 自訂執行時間
initialize_scheduler(
    app,
    enable_daily_summary=True,
    daily_summary_hour=7,        # 7:00 AM
    daily_summary_minute=30      # 7:30 AM
)
```

### 排程管理器 (SchedulerManager)
```python
from app.config.scheduler_config import SchedulerManager

# 取得單例
scheduler_mgr = SchedulerManager.get_instance()

# 操作
scheduler_mgr.start()                    # 啟動
scheduler_mgr.stop()                     # 停止
scheduler_mgr.add_daily_summary()        # 新增任務
scheduler_mgr.get_jobs()                 # 查看任務列表
scheduler_mgr.remove_job('daily_summary')  # 移除任務
```

## 🔐 環境變數配置速記

**必須設置**:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
TO_EMAIL=recipient@example.com
```

**可選**:
```bash
FRED_API_KEY=your-key  # FRED 經濟指標 API
```

## 📧 郵件內容預覽

每封郵件包含以下部分 (按順序):

### 1️⃣ 標題區域 (Header)
- 標題: "📈 每日盤前摘要"
- 日期: "2026 年 03 月 22 日"
- 設計: 紫色漸層背景

### 2️⃣ 美股收盤回顧
```
S&P 500        5,341.20    +35.80 (+0.68%) 🟢
Nasdaq         16,875.35   +125.45 (+0.75%) 🟢
道瓊指數 (Dow) ...]
波動率 (VIX)   ...]
```

### 3️⃣ 國際新聞重點 (Top 5)
```
1. [標題]
   📅 發布時間
2. [標題]
   ...
```

### 4️⃣ 台灣市場新聞 (Top 5)
```
1. [標題]
   📅 發布時間
...
```

### 5️⃣ 宏觀指標變化
| 指標 | 最新數值 | 變化 |
|------|---------|------|
| 聯邦基金利率 | 5.50% | 0.00 |
| 10年殖利率 | 4.15% | +0.02 |
| 美元/台幣 | 31.45 | -0.05 |

### 6️⃣ 社群情緒概況
```
看多 12 篇  看空 8 篇
████████████░░░░  60% : 40%
平均情緒值: 0.15 (-1.0 ~ +1.0)
```

### 7️⃣ 今日重點事件
```
🕐 20:30   美國首次申請失業救濟數據
           影響力: 高
...
```

### 8️⃣ AI 監控清單預警
```
1. AAPL - 黃金交叉突破
   信心度: 85.0%
...
```

### 9️⃣ 免責聲明
```
📌 重要免責聲明
投資有風險，本內容僅供參考，不構成投資建議。
過去表現不代表未來結果。
```

## 🚀 常用代碼片段

### 方式 1: 直接調用
```python
import asyncio
from app.services.daily_summary_service import daily_summary_service

async def main():
    # 生成摘要
    data = await daily_summary_service.generate_summary()
    
    # 發送郵件
    success = await daily_summary_service.send_email(data)
    
    print("成功" if success else "失敗")

asyncio.run(main())
```

### 方式 2: 一鍵執行 (推薦)
```python
import asyncio
from app.services.daily_summary_service import daily_summary_service

asyncio.run(daily_summary_service.schedule_daily_summary())
```

### 方式 3: 測試郵件配置
```python
import asyncio
from app.services.daily_summary_service import daily_summary_service

# 到預設信箱
asyncio.run(daily_summary_service.send_test_email())

# 或指定信箱
asyncio.run(daily_summary_service.send_test_email("test@example.com"))
```

### 方式 4: FastAPI 路由
```python
from fastapi import APIRouter
from app.services.daily_summary_service import daily_summary_service

router = APIRouter()

@router.get("/api/summary/test-email")
async def test_email():
    success = await daily_summary_service.send_test_email()
    return {"success": success}

@router.post("/api/summary/send")
async def send_summary():
    summary = await daily_summary_service.generate_summary()
    success = await daily_summary_service.send_email(summary)
    return {"success": success}
```

### 方式 5: APScheduler 自動排程
```python
from fastapi import FastAPI
from app.config.scheduler_config import initialize_scheduler

app = FastAPI()

# 一行即可啟用每日 8:00 AM 摘要
initialize_scheduler(app)
```

## 🐛 故障排除快速指南

### 問題: 無法發送郵件
**檢查清單**:
1. ✅ `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` 已設置
2. ✅ 使用 Gmail 時使用應用程式密碼 (非帳戶密碼)
3. ✅ 防火牆允許 SMTP 埠 (587 或 465) 出站
4. ✅ 執行測試: `await daily_summary_service.send_test_email()`
5. 📋 查看應用日誌: `logging.getLogger("app.services.daily_summary_service")`

### 問題: 郵件內容不完整
**原因**: 某個數據源失敗
**解決**: 檢查日誌中的警告訊息，數據源失敗時郵件仍會部分發送

### 問題: 排程任務未執行
**檢查清單**:
1. ✅ `initialize_scheduler(app)` 已在應用啟動時調用
2. ✅ 應用確實在執行 (日誌顯示 "APScheduler 已啟動")
3. ✅ 檢查伺服器時區設置
4. ✅ 查看排程任務: `GET /jobs` (如有實現 debug 端點)

## 📚 文檔導航

| 文件 | 用途 | 適合對象 |
|------|------|---------|
| **DAILY_SUMMARY_SETUP.md** | 完整設置與使用指南 | 開發人員、運維人員 |
| **DAILY_SUMMARY_INDEX.md** | 快速參考 (本檔) | 所有人 |
| **daily_summary_service.py** | 程式碼實作 | 進階開發者 |
| **scheduler_config.py** | 排程配置 | 進階開發者 |

## 🔗 相關服務

本服務整合的其他服務:

- `USStockFetcher` - 美股行情資料
- `EnhancedNewsFetcher` - 國際與台灣新聞
- `FREDFetcher` - 美國聯邦準備經濟數據
- `EnhancedSentimentAnalyzer` - 文本情緒分析
- `TaiwanSocialFetcher` - PTT 爬蟲
- `CalendarService` - 事件日曆
- `PredictionTracker` - AI 預測追蹤

## 📞 支援資源

1. 檢查 **DAILY_SUMMARY_SETUP.md** 的常見問題 (FAQ) 部分
2. 查看應用日誌: `DEBUG` 級別會輸出詳細資訊
3. 發送測試郵件驗證配置
4. 查看 Git 提交記錄了解實現細節

## ✅ 驗收清單

使用此清單驗證服務是否正確設置:

- [ ] 環境變數已設置 (SMTP_HOST, SMTP_USER 等)
- [ ] `initialize_scheduler(app)` 已在 FastAPI 應用中調用
- [ ] 測試郵件已成功發送
- [ ] 應用日誌顯示 "APScheduler 已啟動"
- [ ] 日誌中無錯誤訊息
- [ ] 每天 8:00 AM (台灣時間) 收到摘要郵件
- [ ] 郵件內容包含所有 8 個部分 (標題、美股、新聞等)

---

**版本**: 1.0  
**最後更新**: 2026-03-22  
**狀態**: ✅ 正式版

