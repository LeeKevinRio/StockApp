# 台股 AI 投資建議 APP 開發規格書

> **版本**：1.0  
> **目標**：提供完整開發規格，讓 Claude Code 能直接實作  
> **技術棧**：Flutter (前端) + Python FastAPI (後端) + PostgreSQL (資料庫)

---

## 一、專案概述

### 1.1 產品定位
一款台股投資輔助 APP，提供 AI 每日建議、自選股管理、AI 問答功能，協助用戶做出更好的投資決策。

### 1.2 MVP 核心功能
| 功能 | 優先級 | 說明 |
|------|:------:|------|
| 自選股管理 | P0 | 新增/刪除自選股、顯示即時報價與漲跌 |
| AI 每日建議 | P0 | 每日盤後分析自選股，給出買/賣/持有建議 |
| AI 問答 | P0 | 用戶可針對特定股票或市場提問，AI 回答 |

### 1.3 非功能性需求
- 支援 Android（MVP 階段）、iOS（後續）
- 資料更新延遲：報價 < 5 秒（使用 Fugle）、籌碼 < 當日盤後
- 同時在線用戶：MVP 階段 100 人

---

## 二、系統架構

### 2.1 整體架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flutter App (前端)                        │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  自選股    │  │ AI 每日   │  │  AI 問答  │  │  個股詳情  │    │
│  │  管理頁    │  │ 建議頁    │  │   頁面    │  │   頁面    │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST API / WebSocket
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (後端)                        │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  用戶管理  │  │ 股票數據  │  │ AI 建議   │  │ AI 問答   │    │
│  │  Service  │  │  Service  │  │  Service  │  │  Service  │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
│                          │                                      │
│  ┌───────────────────────┴───────────────────────────────┐     │
│  │              Data Fetcher Layer                        │     │
│  │   FinMind API  │  Fugle API  │  TWSE OpenAPI          │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │   users   │  │ watchlist │  │  stocks   │  │ ai_reports│    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 目錄結構

```
taiwan_stock_app/
├── frontend/                    # Flutter 前端
│   ├── lib/
│   │   ├── main.dart
│   │   ├── config/
│   │   │   └── app_config.dart
│   │   ├── models/
│   │   │   ├── stock.dart
│   │   │   ├── user.dart
│   │   │   ├── watchlist_item.dart
│   │   │   └── ai_suggestion.dart
│   │   ├── services/
│   │   │   ├── api_service.dart
│   │   │   ├── auth_service.dart
│   │   │   └── websocket_service.dart
│   │   ├── providers/
│   │   │   ├── watchlist_provider.dart
│   │   │   ├── stock_provider.dart
│   │   │   └── ai_provider.dart
│   │   ├── screens/
│   │   │   ├── home_screen.dart
│   │   │   ├── watchlist_screen.dart
│   │   │   ├── ai_suggestion_screen.dart
│   │   │   ├── ai_chat_screen.dart
│   │   │   └── stock_detail_screen.dart
│   │   ├── widgets/
│   │   │   ├── stock_card.dart
│   │   │   ├── suggestion_card.dart
│   │   │   ├── chat_bubble.dart
│   │   │   └── price_chart.dart
│   │   └── utils/
│   │       ├── formatters.dart
│   │       └── constants.dart
│   ├── pubspec.yaml
│   └── android/
│
├── backend/                     # FastAPI 後端
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── stock.py
│   │   │   ├── watchlist.py
│   │   │   └── ai_report.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── stock.py
│   │   │   ├── watchlist.py
│   │   │   └── ai.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── stocks.py
│   │   │   ├── watchlist.py
│   │   │   └── ai.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── stock_data_service.py
│   │   │   ├── ai_suggestion_service.py
│   │   │   └── ai_chat_service.py
│   │   ├── data_fetchers/
│   │   │   ├── __init__.py
│   │   │   ├── finmind_fetcher.py
│   │   │   ├── fugle_fetcher.py
│   │   │   └── twse_fetcher.py
│   │   └── tasks/
│   │       ├── __init__.py
│   │       └── daily_analysis.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/
│   └── api_examples.md
└── README.md
```

---

## 三、資料庫設計 (PostgreSQL)

### 3.1 ER Diagram

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│    users     │       │    watchlist     │       │    stocks    │
├──────────────┤       ├──────────────────┤       ├──────────────┤
│ id (PK)      │──┐    │ id (PK)          │    ┌──│ stock_id (PK)│
│ email        │  └───>│ user_id (FK)     │    │  │ name         │
│ password_hash│       │ stock_id (FK)    │<───┘  │ industry     │
│ created_at   │       │ added_at         │       │ market       │
│ updated_at   │       │ notes            │       │ updated_at   │
└──────────────┘       └──────────────────┘       └──────────────┘
                                                         │
       ┌─────────────────────────────────────────────────┤
       │                                                 │
       ▼                                                 ▼
┌──────────────────┐                          ┌──────────────────┐
│  stock_prices    │                          │   ai_reports     │
├──────────────────┤                          ├──────────────────┤
│ id (PK)          │                          │ id (PK)          │
│ stock_id (FK)    │                          │ stock_id (FK)    │
│ date             │                          │ user_id (FK)     │
│ open             │                          │ report_date      │
│ high             │                          │ suggestion       │
│ low              │                          │ confidence       │
│ close            │                          │ reasoning        │
│ volume           │                          │ key_factors      │
│ change_percent   │                          │ created_at       │
└──────────────────┘                          └──────────────────┘
```

### 3.2 SQL Schema

```sql
-- 用戶表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 股票基本資料表
CREATE TABLE stocks (
    stock_id VARCHAR(10) PRIMARY KEY,  -- e.g., '2330'
    name VARCHAR(100) NOT NULL,         -- e.g., '台積電'
    english_name VARCHAR(200),
    industry VARCHAR(100),              -- e.g., '半導體業'
    market VARCHAR(10) NOT NULL,        -- 'TWSE' or 'TPEx'
    listed_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 自選股表
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    stock_id VARCHAR(10) REFERENCES stocks(stock_id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    alert_price_high DECIMAL(10,2),     -- 價格警示上限
    alert_price_low DECIMAL(10,2),      -- 價格警示下限
    UNIQUE(user_id, stock_id)
);

-- 股價歷史表（用於 AI 分析）
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    stock_id VARCHAR(10) REFERENCES stocks(stock_id),
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    change_percent DECIMAL(6,2),
    UNIQUE(stock_id, date)
);

-- 籌碼資料表
CREATE TABLE stock_chips (
    id SERIAL PRIMARY KEY,
    stock_id VARCHAR(10) REFERENCES stocks(stock_id),
    date DATE NOT NULL,
    foreign_buy BIGINT,           -- 外資買賣超
    investment_trust_buy BIGINT,  -- 投信買賣超
    dealer_buy BIGINT,            -- 自營商買賣超
    margin_balance BIGINT,        -- 融資餘額
    short_balance BIGINT,         -- 融券餘額
    UNIQUE(stock_id, date)
);

-- AI 分析報告表
CREATE TABLE ai_reports (
    id SERIAL PRIMARY KEY,
    stock_id VARCHAR(10) REFERENCES stocks(stock_id),
    user_id INTEGER REFERENCES users(id),
    report_date DATE NOT NULL,
    suggestion VARCHAR(10) NOT NULL,  -- 'BUY', 'SELL', 'HOLD'
    confidence DECIMAL(3,2),          -- 0.00 ~ 1.00
    target_price DECIMAL(10,2),
    stop_loss_price DECIMAL(10,2),
    reasoning TEXT NOT NULL,
    key_factors JSONB,                -- 關鍵因素 JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, user_id, report_date)
);

-- AI 對話歷史表
CREATE TABLE ai_chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    stock_id VARCHAR(10) REFERENCES stocks(stock_id),  -- 可為 NULL（一般市場問題）
    role VARCHAR(10) NOT NULL,        -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 建立索引
CREATE INDEX idx_stock_prices_stock_date ON stock_prices(stock_id, date DESC);
CREATE INDEX idx_stock_chips_stock_date ON stock_chips(stock_id, date DESC);
CREATE INDEX idx_ai_reports_stock_date ON ai_reports(stock_id, report_date DESC);
CREATE INDEX idx_watchlist_user ON watchlist(user_id);
CREATE INDEX idx_chat_history_user ON ai_chat_history(user_id, created_at DESC);
```

---

## 四、API 設計

### 4.1 API 端點總覽

| Method | Endpoint | 說明 |
|--------|----------|------|
| POST | `/api/auth/register` | 用戶註冊 |
| POST | `/api/auth/login` | 用戶登入 |
| GET | `/api/stocks/search?q={keyword}` | 搜尋股票 |
| GET | `/api/stocks/{stock_id}` | 取得股票詳情 |
| GET | `/api/stocks/{stock_id}/price` | 取得即時報價 |
| GET | `/api/stocks/{stock_id}/history` | 取得歷史K線 |
| GET | `/api/watchlist` | 取得自選股列表 |
| POST | `/api/watchlist` | 新增自選股 |
| DELETE | `/api/watchlist/{stock_id}` | 刪除自選股 |
| GET | `/api/ai/suggestions` | 取得 AI 每日建議（所有自選股）|
| GET | `/api/ai/suggestions/{stock_id}` | 取得單一股票 AI 建議 |
| POST | `/api/ai/chat` | AI 問答 |
| GET | `/api/ai/chat/history` | 取得對話歷史 |

### 4.2 API Schema 定義

```python
# schemas/stock.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class StockBase(BaseModel):
    stock_id: str
    name: str
    market: str  # 'TWSE' or 'TPEx'

class StockDetail(StockBase):
    english_name: Optional[str]
    industry: Optional[str]
    listed_date: Optional[date]

class StockPrice(BaseModel):
    stock_id: str
    name: str
    current_price: Decimal
    change: Decimal
    change_percent: Decimal
    open: Decimal
    high: Decimal
    low: Decimal
    volume: int
    updated_at: datetime

class StockHistory(BaseModel):
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

# schemas/watchlist.py
class WatchlistItem(BaseModel):
    stock_id: str
    name: str
    current_price: Decimal
    change_percent: Decimal
    added_at: datetime
    notes: Optional[str]

class WatchlistAdd(BaseModel):
    stock_id: str
    notes: Optional[str] = None

# schemas/ai.py
class AISuggestion(BaseModel):
    stock_id: str
    name: str
    suggestion: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 ~ 1.0
    target_price: Optional[Decimal]
    stop_loss_price: Optional[Decimal]
    reasoning: str
    key_factors: List[dict]
    report_date: date

class AIChatRequest(BaseModel):
    message: str
    stock_id: Optional[str] = None  # 若指定則針對該股票回答

class AIChatResponse(BaseModel):
    response: str
    related_stocks: List[str]  # 回答中提到的相關股票
    sources: List[str]  # 資料來源
```

### 4.3 API 回應範例

**GET /api/ai/suggestions/2330**
```json
{
  "stock_id": "2330",
  "name": "台積電",
  "suggestion": "HOLD",
  "confidence": 0.72,
  "target_price": 980.00,
  "stop_loss_price": 880.00,
  "reasoning": "台積電近期股價已反映AI需求利多，短期技術面呈現高檔整理格局。外資連續5日買超，但融資餘額同步增加，籌碼面中性偏多。建議持有觀望，等待季報公布後再評估加碼時機。",
  "key_factors": [
    {
      "category": "技術面",
      "factor": "KD指標高檔鈍化",
      "impact": "neutral"
    },
    {
      "category": "籌碼面", 
      "factor": "外資連5日買超共12,453張",
      "impact": "positive"
    },
    {
      "category": "籌碼面",
      "factor": "融資餘額增加2.3%",
      "impact": "negative"
    },
    {
      "category": "基本面",
      "factor": "Q1營收年增15%",
      "impact": "positive"
    }
  ],
  "report_date": "2025-01-19"
}
```

**POST /api/ai/chat**

Request:
```json
{
  "message": "台積電最近外資動向如何？適合現在買嗎？",
  "stock_id": "2330"
}
```

Response:
```json
{
  "response": "根據最新籌碼資料，台積電(2330)近5個交易日外資累計買超約12,453張，呈現持續買進態度。\n\n從技術面來看，目前股價在季線之上，短期均線多頭排列，但KD指標已來到80以上高檔區，短線可能面臨回檔壓力。\n\n建議策略：\n1. 若為長期投資，可考慮分批布局\n2. 若為短線操作，建議等待回檔至950元附近再進場\n3. 停損點建議設在900元以下\n\n請注意：以上分析僅供參考，投資有風險，請審慎評估。",
  "related_stocks": ["2330"],
  "sources": ["FinMind籌碼資料", "證交所三大法人買賣超"]
}
```

---

## 五、外部 API 整合實作

### 5.1 FinMind API 整合

```python
# data_fetchers/finmind_fetcher.py
import requests
from typing import Optional, List, Dict
from datetime import date, timedelta
import pandas as pd

class FinMindFetcher:
    BASE_URL = "https://api.finmindtrade.com/api/v4/data"
    
    def __init__(self, token: str):
        self.token = token
    
    def _request(self, dataset: str, params: dict) -> pd.DataFrame:
        """統一請求方法"""
        params.update({
            "dataset": dataset,
            "token": self.token
        })
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data["status"] != 200:
            raise Exception(f"FinMind API Error: {data.get('msg', 'Unknown error')}")
        return pd.DataFrame(data["data"])
    
    def get_stock_price(
        self, 
        stock_id: str, 
        start_date: str, 
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        取得股票歷史價格
        
        Args:
            stock_id: 股票代碼，如 '2330'
            start_date: 開始日期，格式 'YYYY-MM-DD'
            end_date: 結束日期，格式 'YYYY-MM-DD'
        
        Returns:
            DataFrame with columns: date, stock_id, open, high, low, close, volume
        """
        params = {
            "data_id": stock_id,
            "start_date": start_date,
        }
        if end_date:
            params["end_date"] = end_date
        return self._request("TaiwanStockPrice", params)
    
    def get_institutional_investors(
        self, 
        stock_id: str, 
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        取得三大法人買賣超
        
        Returns:
            DataFrame with columns: date, stock_id, Foreign_Investor_buy/sell,
                                    Investment_Trust_buy/sell, Dealer_buy/sell
        """
        params = {
            "data_id": stock_id,
            "start_date": start_date,
        }
        if end_date:
            params["end_date"] = end_date
        return self._request("TaiwanStockInstitutionalInvestorsBuySell", params)
    
    def get_margin_trading(
        self, 
        stock_id: str, 
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        取得融資融券資料
        
        Returns:
            DataFrame with columns: date, stock_id, 
                                    MarginPurchaseBuy, MarginPurchaseSell, MarginPurchaseBalance,
                                    ShortSaleBuy, ShortSaleSell, ShortSaleBalance
        """
        params = {
            "data_id": stock_id,
            "start_date": start_date,
        }
        if end_date:
            params["end_date"] = end_date
        return self._request("TaiwanStockMarginPurchaseShortSale", params)
    
    def get_monthly_revenue(
        self, 
        stock_id: str, 
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        取得月營收資料
        
        Returns:
            DataFrame with columns: date, stock_id, revenue, revenue_month, revenue_year
        """
        params = {
            "data_id": stock_id,
            "start_date": start_date,
        }
        if end_date:
            params["end_date"] = end_date
        return self._request("TaiwanStockMonthRevenue", params)
    
    def get_stock_list(self) -> pd.DataFrame:
        """
        取得所有上市櫃股票清單
        
        Returns:
            DataFrame with columns: stock_id, stock_name, industry_category, market_type
        """
        return self._request("TaiwanStockInfo", {})


# 使用範例
if __name__ == "__main__":
    fetcher = FinMindFetcher(token="your_finmind_token")
    
    # 取得台積電近30天股價
    prices = fetcher.get_stock_price(
        stock_id="2330",
        start_date="2025-01-01",
        end_date="2025-01-19"
    )
    print(prices.tail())
    
    # 取得三大法人買賣超
    institutions = fetcher.get_institutional_investors(
        stock_id="2330",
        start_date="2025-01-01"
    )
    print(institutions.tail())
```

### 5.2 Fugle API 整合（即時報價）

```python
# data_fetchers/fugle_fetcher.py
import requests
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import websockets
import json

class FugleFetcher:
    """
    Fugle API 整合 - 即時報價
    文件: https://developer.fugle.tw/docs/data/intro/
    
    免費方案限制:
    - REST API: 60 次/分鐘
    - WebSocket: 5 個訂閱
    """
    
    REST_BASE_URL = "https://api.fugle.tw/marketdata/v1.0/stock"
    WS_URL = "wss://api.fugle.tw/marketdata/v1.0/stock/streaming"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-API-KEY": api_key}
    
    def get_realtime_quote(self, stock_id: str) -> Dict:
        """
        取得即時報價
        
        Args:
            stock_id: 股票代碼，如 '2330'
        
        Returns:
            {
                "stock_id": "2330",
                "name": "台積電",
                "price": 950.0,
                "change": 5.0,
                "change_percent": 0.53,
                "open": 948.0,
                "high": 955.0,
                "low": 946.0,
                "volume": 12345678,
                "updated_at": "2025-01-19T13:30:00+08:00"
            }
        """
        url = f"{self.REST_BASE_URL}/intraday/quote/{stock_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        
        return {
            "stock_id": stock_id,
            "name": data.get("name", ""),
            "price": data.get("lastPrice", 0),
            "change": data.get("change", 0),
            "change_percent": data.get("changePercent", 0),
            "open": data.get("openPrice", 0),
            "high": data.get("highPrice", 0),
            "low": data.get("lowPrice", 0),
            "volume": data.get("totalVolume", 0),
            "updated_at": data.get("lastUpdated", "")
        }
    
    def get_realtime_quotes_batch(self, stock_ids: List[str]) -> List[Dict]:
        """批量取得即時報價（注意 60次/分鐘限制）"""
        results = []
        for stock_id in stock_ids:
            try:
                quote = self.get_realtime_quote(stock_id)
                results.append(quote)
            except Exception as e:
                results.append({"stock_id": stock_id, "error": str(e)})
        return results
    
    async def subscribe_realtime(
        self, 
        stock_ids: List[str], 
        callback
    ):
        """
        WebSocket 訂閱即時報價（最多5檔）
        
        Args:
            stock_ids: 股票代碼列表，最多5個
            callback: 收到報價時的回調函數
        """
        if len(stock_ids) > 5:
            raise ValueError("免費方案最多訂閱5檔股票")
        
        uri = f"{self.WS_URL}?apiToken={self.api_key}"
        
        async with websockets.connect(uri) as websocket:
            # 訂閱
            for stock_id in stock_ids:
                subscribe_msg = {
                    "event": "subscribe",
                    "data": {
                        "channel": "quote",
                        "symbol": stock_id
                    }
                }
                await websocket.send(json.dumps(subscribe_msg))
            
            # 接收訊息
            async for message in websocket:
                data = json.loads(message)
                await callback(data)


# 使用範例
if __name__ == "__main__":
    fetcher = FugleFetcher(api_key="your_fugle_api_key")
    
    # REST API 取得即時報價
    quote = fetcher.get_realtime_quote("2330")
    print(quote)
    
    # WebSocket 訂閱（非同步）
    async def on_quote(data):
        print(f"Received: {data}")
    
    # asyncio.run(fetcher.subscribe_realtime(["2330", "2317"], on_quote))
```

### 5.3 證交所 OpenAPI 整合

```python
# data_fetchers/twse_fetcher.py
import requests
from typing import Dict, List, Optional
from datetime import datetime, date
import time

class TWSEFetcher:
    """
    證交所 OpenAPI 整合
    
    注意事項:
    - 每5秒最多3次請求，否則會被暫時封鎖
    - 即時行情約有5-20秒延遲
    """
    
    REALTIME_URL = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    DAILY_URL = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"
    INSTITUTIONAL_URL = "https://www.twse.com.tw/rwd/zh/fund/T86"
    
    def __init__(self):
        self.last_request_time = 0
        self.request_interval = 2  # 每次請求間隔2秒
    
    def _rate_limit(self):
        """簡單的請求頻率控制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()
    
    def get_realtime_price(self, stock_ids: List[str]) -> List[Dict]:
        """
        取得即時報價（證交所 MIS API）
        
        Args:
            stock_ids: 股票代碼列表
        
        注意: 有5-20秒延遲，建議用 Fugle API 取代
        """
        self._rate_limit()
        
        # 格式: tse_2330.tw|tse_2317.tw
        ex_ch = "|".join([f"tse_{sid}.tw" for sid in stock_ids])
        
        response = requests.get(
            self.REALTIME_URL,
            params={"ex_ch": ex_ch, "json": "1", "_": int(time.time() * 1000)}
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("msgArray", []):
            results.append({
                "stock_id": item.get("c", ""),
                "name": item.get("n", ""),
                "price": float(item.get("z", 0) or 0),
                "open": float(item.get("o", 0) or 0),
                "high": float(item.get("h", 0) or 0),
                "low": float(item.get("l", 0) or 0),
                "volume": int(item.get("v", 0) or 0),
                "yesterday_close": float(item.get("y", 0) or 0),
            })
        return results
    
    def get_daily_trading(self, stock_id: str, year: int, month: int) -> List[Dict]:
        """
        取得個股月成交資訊
        
        Args:
            stock_id: 股票代碼
            year: 民國年，如 114
            month: 月份，如 1
        """
        self._rate_limit()
        
        date_str = f"{year}{month:02d}01"
        response = requests.get(
            self.DAILY_URL,
            params={
                "date": date_str,
                "stockNo": stock_id,
                "response": "json"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        for row in data.get("data", []):
            # row: [日期, 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, 漲跌價差, 成交筆數]
            results.append({
                "date": row[0],
                "volume": int(row[1].replace(",", "")),
                "open": float(row[3].replace(",", "")),
                "high": float(row[4].replace(",", "")),
                "low": float(row[5].replace(",", "")),
                "close": float(row[6].replace(",", "")),
            })
        return results
    
    def get_institutional_daily(self, date_str: str) -> List[Dict]:
        """
        取得三大法人買賣超日報
        
        Args:
            date_str: 日期，格式 YYYYMMDD，如 '20250119'
        """
        self._rate_limit()
        
        response = requests.get(
            self.INSTITUTIONAL_URL,
            params={"date": date_str, "response": "json"}
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        for row in data.get("data", []):
            # row: [證券代號, 證券名稱, 外資買, 外資賣, 外資淨買, 投信買, 投信賣, 投信淨買, ...]
            results.append({
                "stock_id": row[0],
                "name": row[1],
                "foreign_buy": int(row[2].replace(",", "")),
                "foreign_sell": int(row[3].replace(",", "")),
                "foreign_net": int(row[4].replace(",", "")),
                "trust_buy": int(row[5].replace(",", "")),
                "trust_sell": int(row[6].replace(",", "")),
                "trust_net": int(row[7].replace(",", "")),
            })
        return results
```

---

## 六、AI 服務設計

### 6.1 AI 每日建議服務

```python
# services/ai_suggestion_service.py
from typing import List, Dict, Optional
from datetime import date, timedelta
from openai import OpenAI
import json

from app.data_fetchers.finmind_fetcher import FinMindFetcher
from app.models.ai_report import AIReport
from app.database import get_db

class AISuggestionService:
    """
    AI 每日建議服務
    
    分析流程:
    1. 收集股票數據（價格、籌碼、基本面）
    2. 計算技術指標
    3. 組合成 Prompt
    4. 呼叫 LLM 生成建議
    5. 解析並儲存結果
    """
    
    def __init__(
        self,
        finmind_token: str,
        openai_api_key: str,
        model: str = "gpt-4o"  # 或使用 Claude API
    ):
        self.finmind = FinMindFetcher(finmind_token)
        self.llm = OpenAI(api_key=openai_api_key)
        self.model = model
    
    def collect_stock_data(self, stock_id: str, days: int = 60) -> Dict:
        """收集股票分析所需的所有數據"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        # 取得各類數據
        prices = self.finmind.get_stock_price(stock_id, start_str, end_str)
        institutions = self.finmind.get_institutional_investors(stock_id, start_str, end_str)
        margins = self.finmind.get_margin_trading(stock_id, start_str, end_str)
        
        # 計算技術指標
        technical = self._calculate_technical_indicators(prices)
        
        # 計算籌碼面指標
        chip_analysis = self._analyze_chip_data(institutions, margins)
        
        return {
            "stock_id": stock_id,
            "latest_price": float(prices.iloc[-1]["close"]) if len(prices) > 0 else 0,
            "price_change_5d": self._calculate_change(prices, 5),
            "price_change_20d": self._calculate_change(prices, 20),
            "technical": technical,
            "chip": chip_analysis,
            "prices_summary": prices.tail(10).to_dict("records") if len(prices) > 0 else []
        }
    
    def _calculate_technical_indicators(self, prices) -> Dict:
        """計算技術指標"""
        if len(prices) < 20:
            return {}
        
        close = prices["close"].astype(float)
        
        # MA
        ma5 = close.rolling(5).mean().iloc[-1]
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        
        # RSI (14日)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        # KD (9日)
        low_9 = prices["low"].astype(float).rolling(9).min()
        high_9 = prices["high"].astype(float).rolling(9).max()
        rsv = (close - low_9) / (high_9 - low_9) * 100
        k = rsv.ewm(com=2, adjust=False).mean().iloc[-1]
        d = rsv.ewm(com=2, adjust=False).mean().ewm(com=2, adjust=False).mean().iloc[-1]
        
        current_price = close.iloc[-1]
        
        return {
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "ma20": round(ma20, 2),
            "rsi_14": round(rsi, 2),
            "k": round(k, 2),
            "d": round(d, 2),
            "price_vs_ma5": "above" if current_price > ma5 else "below",
            "price_vs_ma20": "above" if current_price > ma20 else "below",
            "ma_trend": "bullish" if ma5 > ma10 > ma20 else "bearish" if ma5 < ma10 < ma20 else "neutral"
        }
    
    def _analyze_chip_data(self, institutions, margins) -> Dict:
        """分析籌碼面數據"""
        if len(institutions) < 5 or len(margins) < 5:
            return {}
        
        # 近5日外資買賣超
        recent_inst = institutions.tail(5)
        foreign_net_5d = recent_inst["Foreign_Investor_buy"].sum() - recent_inst["Foreign_Investor_sell"].sum()
        trust_net_5d = recent_inst["Investment_Trust_buy"].sum() - recent_inst["Investment_Trust_sell"].sum()
        
        # 融資融券變化
        recent_margin = margins.tail(5)
        margin_change = float(recent_margin.iloc[-1]["MarginPurchaseBalance"]) - float(recent_margin.iloc[0]["MarginPurchaseBalance"])
        short_change = float(recent_margin.iloc[-1]["ShortSaleBalance"]) - float(recent_margin.iloc[0]["ShortSaleBalance"])
        
        return {
            "foreign_net_5d": int(foreign_net_5d),
            "trust_net_5d": int(trust_net_5d),
            "foreign_trend": "buying" if foreign_net_5d > 0 else "selling",
            "margin_change_5d": int(margin_change),
            "short_change_5d": int(short_change),
            "margin_trend": "increasing" if margin_change > 0 else "decreasing"
        }
    
    def _calculate_change(self, prices, days: int) -> float:
        """計算N日漲跌幅"""
        if len(prices) < days + 1:
            return 0
        current = float(prices.iloc[-1]["close"])
        past = float(prices.iloc[-days-1]["close"])
        return round((current - past) / past * 100, 2)
    
    def generate_suggestion(self, stock_id: str, stock_name: str) -> Dict:
        """生成 AI 投資建議"""
        # 收集數據
        data = self.collect_stock_data(stock_id)
        
        # 組合 Prompt
        prompt = self._build_prompt(stock_id, stock_name, data)
        
        # 呼叫 LLM
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": """你是一位專業的台股分析師。請根據提供的股票數據，給出客觀的投資建議。

你的回應必須是有效的 JSON 格式，包含以下欄位：
- suggestion: "BUY" | "SELL" | "HOLD"
- confidence: 0.0 到 1.0 之間的數字，表示建議的信心程度
- target_price: 目標價（數字）
- stop_loss_price: 停損價（數字）
- reasoning: 詳細的分析理由（字串，100-200字）
- key_factors: 關鍵因素陣列，每個元素包含 category, factor, impact

重要提醒：
1. 投資建議僅供參考，不構成投資決策依據
2. 請保持客觀中立，不要過度樂觀或悲觀
3. reasoning 中請具體說明數據支持的觀點"""
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # 解析結果
        result = json.loads(response.choices[0].message.content)
        result["stock_id"] = stock_id
        result["name"] = stock_name
        result["report_date"] = date.today().isoformat()
        
        return result
    
    def _build_prompt(self, stock_id: str, stock_name: str, data: Dict) -> str:
        """組合分析 Prompt"""
        return f"""請分析以下股票並給出投資建議：

## 股票資訊
- 代碼：{stock_id}
- 名稱：{stock_name}
- 最新收盤價：{data['latest_price']}

## 價格變化
- 近5日漲跌幅：{data['price_change_5d']}%
- 近20日漲跌幅：{data['price_change_20d']}%

## 技術指標
{json.dumps(data['technical'], ensure_ascii=False, indent=2)}

## 籌碼面分析
{json.dumps(data['chip'], ensure_ascii=False, indent=2)}

## 近10日價格數據
{json.dumps(data['prices_summary'], ensure_ascii=False, indent=2)}

請根據以上數據，給出你的投資建議（JSON格式）。"""
```

### 6.2 AI 問答服務

```python
# services/ai_chat_service.py
from typing import List, Dict, Optional
from datetime import date, timedelta
from openai import OpenAI
import json

from app.data_fetchers.finmind_fetcher import FinMindFetcher
from app.models.ai_chat import AIChatHistory
from app.database import get_db

class AIChatService:
    """
    AI 問答服務
    
    功能:
    1. 回答股票相關問題
    2. 支援針對特定股票的問答
    3. 可引用即時數據回答
    """
    
    SYSTEM_PROMPT = """你是一位專業的台股投資顧問 AI 助手。你可以：

1. 回答關於台股投資的各種問題
2. 分析特定股票的技術面、籌碼面、基本面
3. 解釋投資概念和術語
4. 提供市場趨勢分析

重要原則：
- 所有投資建議僅供參考，不構成投資決策依據
- 回答時引用具體數據，說明數據來源
- 保持客觀中立，提醒投資風險
- 如果不確定或沒有相關數據，誠實告知

當用戶詢問特定股票時，你會收到該股票的最新數據，請根據數據提供分析。"""

    def __init__(
        self,
        finmind_token: str,
        openai_api_key: str,
        model: str = "gpt-4o"
    ):
        self.finmind = FinMindFetcher(finmind_token)
        self.llm = OpenAI(api_key=openai_api_key)
        self.model = model
    
    def chat(
        self,
        user_message: str,
        stock_id: Optional[str] = None,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        處理用戶問答
        
        Args:
            user_message: 用戶訊息
            stock_id: 指定股票代碼（可選）
            chat_history: 對話歷史（可選）
        
        Returns:
            {
                "response": "AI 回答",
                "related_stocks": ["2330"],
                "sources": ["FinMind籌碼資料"]
            }
        """
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        
        # 加入對話歷史
        if chat_history:
            for msg in chat_history[-10:]:  # 最多保留10輪對話
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # 如果指定股票，取得即時數據
        stock_context = ""
        sources = []
        if stock_id:
            try:
                stock_data = self._get_stock_context(stock_id)
                stock_context = f"\n\n## 股票 {stock_id} 的最新數據\n{stock_data}"
                sources.append("FinMind 股票數據")
                sources.append("證交所三大法人買賣超")
            except Exception as e:
                stock_context = f"\n\n（無法取得股票 {stock_id} 的數據：{str(e)}）"
        
        # 組合用戶訊息
        full_message = user_message + stock_context
        messages.append({"role": "user", "content": full_message})
        
        # 呼叫 LLM
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        # 提取相關股票代碼
        related_stocks = self._extract_stock_ids(ai_response)
        if stock_id and stock_id not in related_stocks:
            related_stocks.insert(0, stock_id)
        
        return {
            "response": ai_response,
            "related_stocks": related_stocks,
            "sources": sources
        }
    
    def _get_stock_context(self, stock_id: str) -> str:
        """取得股票即時數據作為上下文"""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        start_str = start_date.strftime("%Y-%m-%d")
        
        # 取得價格
        prices = self.finmind.get_stock_price(stock_id, start_str)
        latest = prices.iloc[-1] if len(prices) > 0 else None
        
        # 取得籌碼
        institutions = self.finmind.get_institutional_investors(stock_id, start_str)
        
        context = f"""
- 最新收盤價：{latest['close'] if latest is not None else 'N/A'}
- 成交量：{latest['Trading_Volume'] if latest is not None else 'N/A'}
- 近5日外資買賣超：{institutions.tail(5)['Foreign_Investor_buy'].sum() - institutions.tail(5)['Foreign_Investor_sell'].sum() if len(institutions) >= 5 else 'N/A'}
- 近5日投信買賣超：{institutions.tail(5)['Investment_Trust_buy'].sum() - institutions.tail(5)['Investment_Trust_sell'].sum() if len(institutions) >= 5 else 'N/A'}
"""
        return context
    
    def _extract_stock_ids(self, text: str) -> List[str]:
        """從文字中提取股票代碼"""
        import re
        # 匹配 4 位數字的股票代碼
        pattern = r'\b(\d{4})\b'
        matches = re.findall(pattern, text)
        # 過濾可能不是股票代碼的數字（如年份）
        valid_ids = [m for m in matches if 1000 <= int(m) <= 9999 and int(m) not in range(1900, 2100)]
        return list(set(valid_ids))[:5]  # 最多返回5個
```

---

## 七、Flutter 前端實作

### 7.1 核心 Model 類別

```dart
// models/stock.dart
class Stock {
  final String stockId;
  final String name;
  final String market;
  final String? industry;

  Stock({
    required this.stockId,
    required this.name,
    required this.market,
    this.industry,
  });

  factory Stock.fromJson(Map<String, dynamic> json) {
    return Stock(
      stockId: json['stock_id'],
      name: json['name'],
      market: json['market'],
      industry: json['industry'],
    );
  }
}

class StockPrice {
  final String stockId;
  final String name;
  final double currentPrice;
  final double change;
  final double changePercent;
  final double open;
  final double high;
  final double low;
  final int volume;
  final DateTime updatedAt;

  StockPrice({
    required this.stockId,
    required this.name,
    required this.currentPrice,
    required this.change,
    required this.changePercent,
    required this.open,
    required this.high,
    required this.low,
    required this.volume,
    required this.updatedAt,
  });

  factory StockPrice.fromJson(Map<String, dynamic> json) {
    return StockPrice(
      stockId: json['stock_id'],
      name: json['name'],
      currentPrice: (json['current_price'] as num).toDouble(),
      change: (json['change'] as num).toDouble(),
      changePercent: (json['change_percent'] as num).toDouble(),
      open: (json['open'] as num).toDouble(),
      high: (json['high'] as num).toDouble(),
      low: (json['low'] as num).toDouble(),
      volume: json['volume'],
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  bool get isUp => change > 0;
  bool get isDown => change < 0;
}

// models/ai_suggestion.dart
class AISuggestion {
  final String stockId;
  final String name;
  final String suggestion; // 'BUY', 'SELL', 'HOLD'
  final double confidence;
  final double? targetPrice;
  final double? stopLossPrice;
  final String reasoning;
  final List<KeyFactor> keyFactors;
  final DateTime reportDate;

  AISuggestion({
    required this.stockId,
    required this.name,
    required this.suggestion,
    required this.confidence,
    this.targetPrice,
    this.stopLossPrice,
    required this.reasoning,
    required this.keyFactors,
    required this.reportDate,
  });

  factory AISuggestion.fromJson(Map<String, dynamic> json) {
    return AISuggestion(
      stockId: json['stock_id'],
      name: json['name'],
      suggestion: json['suggestion'],
      confidence: (json['confidence'] as num).toDouble(),
      targetPrice: json['target_price']?.toDouble(),
      stopLossPrice: json['stop_loss_price']?.toDouble(),
      reasoning: json['reasoning'],
      keyFactors: (json['key_factors'] as List)
          .map((e) => KeyFactor.fromJson(e))
          .toList(),
      reportDate: DateTime.parse(json['report_date']),
    );
  }

  Color get suggestionColor {
    switch (suggestion) {
      case 'BUY':
        return Colors.red;
      case 'SELL':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  String get suggestionText {
    switch (suggestion) {
      case 'BUY':
        return '建議買進';
      case 'SELL':
        return '建議賣出';
      default:
        return '建議持有';
    }
  }
}

class KeyFactor {
  final String category;
  final String factor;
  final String impact; // 'positive', 'negative', 'neutral'

  KeyFactor({
    required this.category,
    required this.factor,
    required this.impact,
  });

  factory KeyFactor.fromJson(Map<String, dynamic> json) {
    return KeyFactor(
      category: json['category'],
      factor: json['factor'],
      impact: json['impact'],
    );
  }

  Color get impactColor {
    switch (impact) {
      case 'positive':
        return Colors.red;
      case 'negative':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  IconData get impactIcon {
    switch (impact) {
      case 'positive':
        return Icons.arrow_upward;
      case 'negative':
        return Icons.arrow_downward;
      default:
        return Icons.remove;
    }
  }
}
```

### 7.2 API Service

```dart
// services/api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../models/stock.dart';
import '../models/ai_suggestion.dart';

class ApiService {
  final String baseUrl;
  String? _authToken;

  ApiService({String? baseUrl}) : baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  void setAuthToken(String token) {
    _authToken = token;
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_authToken != null) 'Authorization': 'Bearer $_authToken',
      };

  // ==================== 認證相關 ====================

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> register(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 股票相關 ====================

  Future<List<Stock>> searchStocks(String query) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/search?q=$query'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => Stock.fromJson(e)).toList();
  }

  Future<StockPrice> getStockPrice(String stockId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/stocks/$stockId/price'),
      headers: _headers,
    );
    _checkResponse(response);
    return StockPrice.fromJson(jsonDecode(response.body));
  }

  // ==================== 自選股相關 ====================

  Future<List<StockPrice>> getWatchlist() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/watchlist'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => StockPrice.fromJson(e)).toList();
  }

  Future<void> addToWatchlist(String stockId, {String? notes}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/watchlist'),
      headers: _headers,
      body: jsonEncode({'stock_id': stockId, 'notes': notes}),
    );
    _checkResponse(response);
  }

  Future<void> removeFromWatchlist(String stockId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/watchlist/$stockId'),
      headers: _headers,
    );
    _checkResponse(response);
  }

  // ==================== AI 相關 ====================

  Future<List<AISuggestion>> getAISuggestions() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/ai/suggestions'),
      headers: _headers,
    );
    _checkResponse(response);
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((e) => AISuggestion.fromJson(e)).toList();
  }

  Future<AISuggestion> getStockSuggestion(String stockId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/ai/suggestions/$stockId'),
      headers: _headers,
    );
    _checkResponse(response);
    return AISuggestion.fromJson(jsonDecode(response.body));
  }

  Future<Map<String, dynamic>> chat(String message, {String? stockId}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/ai/chat'),
      headers: _headers,
      body: jsonEncode({
        'message': message,
        if (stockId != null) 'stock_id': stockId,
      }),
    );
    _checkResponse(response);
    return jsonDecode(response.body);
  }

  // ==================== 錯誤處理 ====================

  void _checkResponse(http.Response response) {
    if (response.statusCode >= 400) {
      final body = jsonDecode(response.body);
      throw ApiException(
        statusCode: response.statusCode,
        message: body['detail'] ?? 'Unknown error',
      );
    }
  }
}

class ApiException implements Exception {
  final int statusCode;
  final String message;

  ApiException({required this.statusCode, required this.message});

  @override
  String toString() => 'ApiException: $statusCode - $message';
}
```

### 7.3 自選股畫面

```dart
// screens/watchlist_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/watchlist_provider.dart';
import '../widgets/stock_card.dart';

class WatchlistScreen extends StatefulWidget {
  const WatchlistScreen({super.key});

  @override
  State<WatchlistScreen> createState() => _WatchlistScreenState();
}

class _WatchlistScreenState extends State<WatchlistScreen> {
  @override
  void initState() {
    super.initState();
    // 載入自選股
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<WatchlistProvider>().loadWatchlist();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('自選股'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showAddStockDialog(context),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<WatchlistProvider>().refresh(),
          ),
        ],
      ),
      body: Consumer<WatchlistProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('錯誤：${provider.error}'),
                  ElevatedButton(
                    onPressed: () => provider.loadWatchlist(),
                    child: const Text('重試'),
                  ),
                ],
              ),
            );
          }

          if (provider.stocks.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.star_border, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('尚無自選股'),
                  Text('點擊右上角 + 新增股票', style: TextStyle(color: Colors.grey)),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => provider.refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: provider.stocks.length,
              itemBuilder: (context, index) {
                final stock = provider.stocks[index];
                return StockCard(
                  stock: stock,
                  onTap: () => _navigateToDetail(context, stock.stockId),
                  onDelete: () => _confirmDelete(context, stock.stockId),
                );
              },
            ),
          );
        },
      ),
    );
  }

  void _showAddStockDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => const AddStockBottomSheet(),
    );
  }

  void _navigateToDetail(BuildContext context, String stockId) {
    Navigator.pushNamed(context, '/stock/$stockId');
  }

  void _confirmDelete(BuildContext context, String stockId) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('確認刪除'),
        content: const Text('確定要從自選股移除嗎？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () {
              context.read<WatchlistProvider>().removeStock(stockId);
              Navigator.pop(context);
            },
            child: const Text('刪除', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}

// widgets/stock_card.dart
class StockCard extends StatelessWidget {
  final StockPrice stock;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const StockCard({
    super.key,
    required this.stock,
    required this.onTap,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final priceColor = stock.isUp
        ? Colors.red
        : stock.isDown
            ? Colors.green
            : Colors.grey;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // 股票代碼與名稱
              Expanded(
                flex: 2,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      stock.stockId,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    Text(
                      stock.name,
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
              // 股價
              Expanded(
                flex: 2,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      stock.currentPrice.toStringAsFixed(2),
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                        color: priceColor,
                      ),
                    ),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Icon(
                          stock.isUp
                              ? Icons.arrow_drop_up
                              : stock.isDown
                                  ? Icons.arrow_drop_down
                                  : Icons.remove,
                          color: priceColor,
                          size: 20,
                        ),
                        Text(
                          '${stock.changePercent.toStringAsFixed(2)}%',
                          style: TextStyle(color: priceColor),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              // 刪除按鈕
              IconButton(
                icon: const Icon(Icons.delete_outline, color: Colors.grey),
                onPressed: onDelete,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### 7.4 AI 問答畫面

```dart
// screens/ai_chat_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/ai_provider.dart';
import '../widgets/chat_bubble.dart';

class AIChatScreen extends StatefulWidget {
  final String? stockId;  // 可選，若指定則針對該股票問答

  const AIChatScreen({super.key, this.stockId});

  @override
  State<AIChatScreen> createState() => _AIChatScreenState();
}

class _AIChatScreenState extends State<AIChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    // 載入對話歷史
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AIProvider>().loadChatHistory(stockId: widget.stockId);
    });
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.stockId != null ? 'AI 問答 - ${widget.stockId}' : 'AI 問答'),
      ),
      body: Column(
        children: [
          // 對話區域
          Expanded(
            child: Consumer<AIProvider>(
              builder: (context, provider, child) {
                if (provider.messages.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey[400]),
                        const SizedBox(height: 16),
                        const Text('有什麼投資問題想問我嗎？'),
                        const SizedBox(height: 8),
                        Text(
                          '例如：台積電最近外資動向如何？',
                          style: TextStyle(color: Colors.grey[600], fontSize: 14),
                        ),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: provider.messages.length,
                  itemBuilder: (context, index) {
                    final message = provider.messages[index];
                    return ChatBubble(
                      message: message.content,
                      isUser: message.role == 'user',
                      sources: message.sources,
                    );
                  },
                );
              },
            ),
          ),

          // 輸入區域
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withOpacity(0.2),
                  blurRadius: 4,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      decoration: InputDecoration(
                        hintText: '輸入你的問題...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                          borderSide: BorderSide.none,
                        ),
                        filled: true,
                        fillColor: Colors.grey[100],
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                      ),
                      maxLines: null,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Consumer<AIProvider>(
                    builder: (context, provider, child) {
                      return IconButton(
                        icon: provider.isLoading
                            ? const SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.send),
                        onPressed: provider.isLoading ? null : _sendMessage,
                        color: Theme.of(context).primaryColor,
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _sendMessage() {
    final message = _messageController.text.trim();
    if (message.isEmpty) return;

    context.read<AIProvider>().sendMessage(
      message,
      stockId: widget.stockId,
    );

    _messageController.clear();

    // 滾動到底部
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }
}

// widgets/chat_bubble.dart
class ChatBubble extends StatelessWidget {
  final String message;
  final bool isUser;
  final List<String>? sources;

  const ChatBubble({
    super.key,
    required this.message,
    required this.isUser,
    this.sources,
  });

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        decoration: BoxDecoration(
          color: isUser ? Theme.of(context).primaryColor : Colors.grey[200],
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomRight: isUser ? const Radius.circular(4) : null,
            bottomLeft: !isUser ? const Radius.circular(4) : null,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message,
              style: TextStyle(
                color: isUser ? Colors.white : Colors.black87,
              ),
            ),
            if (sources != null && sources!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                '資料來源：${sources!.join(', ')}',
                style: TextStyle(
                  fontSize: 12,
                  color: isUser ? Colors.white70 : Colors.grey[600],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

---

## 八、開發與部署

### 8.1 環境變數設定

```bash
# backend/.env
DATABASE_URL=postgresql://user:password@localhost:5432/taiwan_stock
FINMIND_TOKEN=your_finmind_token
FUGLE_API_KEY=your_fugle_api_key
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_jwt_secret_key
```

```dart
// frontend/lib/config/app_config.dart
class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
  
  static const bool isProduction = bool.fromEnvironment('dart.vm.product');
}
```

### 8.2 Docker Compose

```yaml
# backend/docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: taiwan_stock
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/taiwan_stock
      - FINMIND_TOKEN=${FINMIND_TOKEN}
      - FUGLE_API_KEY=${FUGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - db

  scheduler:
    build: .
    command: python -m app.tasks.scheduler
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/taiwan_stock
      - FINMIND_TOKEN=${FINMIND_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db

volumes:
  postgres_data:
```

### 8.3 Backend requirements.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
pydantic==2.5.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
requests==2.31.0
pandas==2.2.0
openai==1.10.0
websockets==12.0
apscheduler==3.10.4
python-dotenv==1.0.0
```

### 8.4 Flutter pubspec.yaml

```yaml
name: taiwan_stock_app
description: 台股 AI 投資建議 APP

publish_to: 'none'

version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  
  # 狀態管理
  provider: ^6.1.1
  
  # 網路請求
  http: ^1.2.0
  web_socket_channel: ^2.4.0
  
  # 本地儲存
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
  
  # UI 元件
  fl_chart: ^0.66.0
  intl: ^0.19.0
  
  # 工具
  logger: ^2.0.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.1

flutter:
  uses-material-design: true
```

---

## 九、風險提示與法規遵循

### 9.1 投資風險提示

在 APP 中必須顯示的免責聲明：

```
本 APP 提供的投資建議僅供參考，不構成任何投資決策依據。
投資涉及風險，股票價格可升可跌，過往表現不代表未來回報。
用戶應根據自身財務狀況和投資目標，審慎評估後再做決定。
本 APP 不對任何因使用建議而產生的損失承擔責任。
```

### 9.2 資料使用授權

- **FinMind**：免費用戶可用於個人與學術用途，商業使用需聯繫授權
- **Fugle API**：免費方案可用於個人開發，商業應用需申請付費方案
- **證交所/櫃買資料**：公開資料可自由使用，但即時行情需遵守交易所規範
- **MOPS 資料**：屬政府公開資料，可自由使用

### 9.3 個資保護

遵循台灣《個人資料保護法》：
- 明確告知用戶收集哪些資料、用途為何
- 提供用戶刪除帳號與資料的功能
- 敏感資料（如投資偏好）需加密儲存
- 不得將用戶資料販售或分享給第三方

---

## 十、後續擴充功能建議

### Phase 2（MVP 完成後）
- [ ] 價格警示通知（Push Notification）
- [ ] 技術指標圖表（K線、MA、RSI）
- [ ] 新聞整合（RSS feeds）

### Phase 3
- [ ] 社群情緒分析（PTT 爬蟲 + NLP）
- [ ] 模擬交易功能
- [ ] 投資組合追蹤

### Phase 4
- [ ] 進階 AI 策略回測
- [ ] 選股篩選器
- [ ] 法說會提醒

---

*文件版本：1.0 | 最後更新：2025-01-19*
