# 每日盤前摘要服務 (Daily Summary Service) 設置指南

## 概述

`DailySummaryService` 是一個自動化服務，每日早上 8:00 AM (台灣時間) 發送盤前摘要郵件，內容包括：

- 🇺🇸 **美股收盤回顧** - S&P 500, Nasdaq, Dow, VIX
- 🌍 **國際新聞重點** - 精選 Top 5 新聞
- 🇹🇼 **台灣市場新聞** - 精選 Top 5 新聞
- 📊 **宏觀指標變化** - Fed 利率、公債殖利率、美元/台幣匯率
- 💬 **社群情緒概況** - PTT/Threads 看多看空比例
- 📅 **今日重點事件** - 財報、經濟數據公布
- 🤖 **AI 監控清單預警** - 強信號股票提示
- 🎨 **專業 HTML 郵件** - 行動裝置友善設計

---

## 環境變數配置

在 `.env` 或系統環境變數中設置以下配置：

```env
# SMTP 郵件伺服器配置
SMTP_HOST=smtp.gmail.com          # SMTP 伺服器地址
SMTP_PORT=587                      # SMTP 伺服器埠 (TLS: 587, SSL: 465)
SMTP_USER=your-email@gmail.com     # 郵件帳戶
SMTP_PASSWORD=your-app-password    # 應用程式密碼 (對於 Gmail，需要使用應用程式密碼而非帳戶密碼)

# 郵件配置
FROM_EMAIL=your-email@gmail.com    # 寄件者郵箱
TO_EMAIL=user1@example.com,user2@example.com  # 收件者 (支援逗號分隔多個郵箱)

# FRED API (經濟指標)
FRED_API_KEY=your-fred-api-key    # 可選，從 https://fred.stlouisfed.org/docs/api 獲得
```

### Gmail 配置步驟

如果使用 Gmail，請按以下步驟：

1. **啟用 2-Step Verification**
   - 進入 https://myaccount.google.com/security
   - 啟用「2-Step Verification」

2. **生成應用程式密碼**
   - 進入 https://myaccount.google.com/apppasswords
   - 選擇 "Mail" 和 "Windows Computer" (或相應平台)
   - 生成密碼，複製並粘貼到 `SMTP_PASSWORD`

3. **允許不安全的應用程式訪問** (如果上述方式不適用)
   - 進入 https://myaccount.google.com/lesssecureapps
   - 啟用「Allow less secure apps」

### 其他 SMTP 服務範例

#### Outlook/Office365
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
```

#### 騰訊企業郵
```env
SMTP_HOST=smtp.exmail.qq.com
SMTP_PORT=587
SMTP_USER=your-email@company.com
SMTP_PASSWORD=your-password
```

---

## 使用方法

### 1. 基本使用 - 生成並發送摘要

```python
from app.services.daily_summary_service import daily_summary_service
import asyncio

async def main():
    # 生成摘要數據
    summary_data = await daily_summary_service.generate_summary()

    # 發送郵件
    success = await daily_summary_service.send_email(summary_data)

    if success:
        print("摘要郵件發送成功！")
    else:
        print("發送失敗，請檢查配置")

# 執行
asyncio.run(main())
```

### 2. 定時任務 - 使用 APScheduler

在 FastAPI 應用啟動時設置定時任務：

```python
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import timezone
import asyncio
from app.services.daily_summary_service import daily_summary_service

app = FastAPI()

scheduler = BackgroundScheduler()

def scheduled_daily_summary():
    """定時任務包裝函數"""
    asyncio.run(daily_summary_service.schedule_daily_summary())

# 設置每天 8:00 AM 台灣時間 (UTC+8) 執行
tz = timezone(timedelta(hours=8))  # 台灣時區
scheduler.add_job(
    scheduled_daily_summary,
    CronTrigger(
        hour=8,
        minute=0,
        second=0,
        timezone=tz
    ),
    id='daily_summary',
    name='每日盤前摘要',
    misfire_grace_time=300  # 最多容許 5 分鐘遲到
)

@app.on_event("startup")
async def startup():
    scheduler.start()
    print("每日摘要排程已啟動")

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
    print("每日摘要排程已關閉")
```

### 3. 發送測試郵件

測試郵件配置是否正確：

```python
from app.services.daily_summary_service import daily_summary_service
import asyncio

async def main():
    # 發送測試郵件到默認收件人
    success = await daily_summary_service.send_test_email()

    # 或發送到特定郵箱
    # success = await daily_summary_service.send_test_email(to_email="test@example.com")

    if success:
        print("測試郵件發送成功！")

asyncio.run(main())
```

### 4. 手動調用定時任務

```python
from app.services.daily_summary_service import daily_summary_service
import asyncio

async def main():
    success = await daily_summary_service.schedule_daily_summary()
    print(f"任務執行結果: {'成功' if success else '失敗'}")

asyncio.run(main())
```

---

## API 端點整合範例

在 FastAPI 路由中新增端點：

```python
from fastapi import APIRouter, HTTPException
from app.services.daily_summary_service import daily_summary_service

router = APIRouter(prefix="/api/summary", tags=["summary"])

@router.get("/test-email")
async def send_test_email(email: str = None):
    """發送測試郵件"""
    try:
        success = await daily_summary_service.send_test_email(to_email=email)
        return {
            "success": success,
            "message": "測試郵件已發送" if success else "發送失敗"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generate")
async def generate_summary():
    """生成摘要 (不發送)"""
    try:
        summary = await daily_summary_service.generate_summary()
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
async def send_summary():
    """生成並發送摘要"""
    try:
        summary = await daily_summary_service.generate_summary()
        success = await daily_summary_service.send_email(summary)
        return {
            "success": success,
            "message": "摘要已發送" if success else "發送失敗"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 錯誤處理

服務具有強大的錯誤容錯機制：

- **數據源失敗**: 如果某個數據源 (新聞、指標等) 失敗，郵件仍會以可用的數據發送
- **SMTP 配置不完整**: 會記錄警告並不發送郵件
- **網路超時**: 所有外部 API 呼叫都有超時設置和重試機制

檢查日誌以了解詳細錯誤：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app.services.daily_summary_service")
```

---

## 郵件內容結構

生成的 HTML 郵件包含以下部分：

| 部分 | 內容 | 來源 |
|------|------|------|
| 美股收盤回顧 | S&P 500, Nasdaq, Dow, VIX | USStockFetcher |
| 國際新聞 | Top 5 | enhanced_news_fetcher |
| 台灣新聞 | Top 5 | enhanced_news_fetcher |
| 宏觀指標 | Fed 利率、公債殖利率、美元/台幣 | FREDFetcher + USStockFetcher |
| 社群情緒 | 看多/看空比例、平均情緒值 | TaiwanSocialFetcher + EnhancedSentimentAnalyzer |
| 重點事件 | 財報、經濟公布 | CalendarService |
| AI 警報 | 強信號股票 | PredictionTracker |

---

## 常見問題

### Q: 為什麼收不到郵件？

**A:** 檢查以下項目：

1. 確認 `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` 都正確設置
2. 對於 Gmail，需要使用應用程式密碼而非帳戶密碼
3. 檢查防火牆是否允許 SMTP 埠出站
4. 查看日誌中的錯誤信息
5. 嘗試發送測試郵件: `await daily_summary_service.send_test_email()`

### Q: 如何修改發送時間？

**A:** 修改 APScheduler 配置中的 `hour` 和 `minute`：

```python
# 改為每天 6:00 AM
CronTrigger(
    hour=6,
    minute=0,
    second=0,
    timezone=tz
)
```

### Q: 如何隱藏某些部分的郵件內容？

**A:** 修改 `generate_summary()` 返回的數據，將不需要的部分設為空：

```python
summary_data["international_news"] = []  # 隱藏國際新聞
```

### Q: 可以自定義郵件樣式嗎？

**A:** 可以，修改 `_build_html_email()` 方法中的 CSS 部分。所有顏色和字體都是可配置的。

---

## 監控與日誌

服務使用 Python 標準 `logging` 模組，重要事件包括：

```
[INFO] 開始生成每日摘要...
[INFO] 每日摘要數據生成完成
[INFO] 每日摘要郵件已發送至 user@example.com
[ERROR] 發送郵件失敗: [錯誤詳情]
[WARNING] 無法取得 S&P 500 數據: [原因]
```

在應用的日誌配置中啟用 `daily_summary_service` 的日誌：

```python
logging.getLogger("app.services.daily_summary_service").setLevel(logging.DEBUG)
```

---

## 技術細節

- **編程語言**: Python 3.8+
- **非同步框架**: asyncio
- **郵件協議**: SMTP with STARTTLS
- **HTML 渲染**: 支援所有現代郵件客戶端 (Outlook, Gmail, Apple Mail 等)
- **字符編碼**: UTF-8 (支持繁體中文、表情符號)
- **錯誤恢復**: 單一數據源失敗時，郵件仍會以部分數據發送

---

## 免責聲明

本服務僅供參考，投資有風險。生成的摘要包含：

- 來自第三方的市場數據 (可能延遲或不準確)
- AI 情緒分析 (基於文本分析，可能不精確)
- 新聞標題摘要 (可能遺漏重要細節)

**投資前請進行充分調查與評估。過去表現不代表未來結果。**

---

## 支持與回報

如有問題或建議，請：

1. 檢查日誌中的錯誤信息
2. 驗證環境變數配置
3. 參考本指南的常見問題部分
4. 提交 Issue 至專案倉庫

