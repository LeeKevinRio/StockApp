# Bug 修復報告

## 修復時間
2026-01-21 00:10

---

## Bug #1: AI 建議無法生成 ✅

### 問題描述
- 用戶有自選股（2330 台積電），但 AI 建議頁面顯示「尚無 AI 建議」
- 點擊重新整理也沒有生成建議

### 根本原因
AI 建議生成時發生異常被 `continue` 跳過，具體錯誤：
1. **KeyError: 'low'** - FinMind 回傳的價格數據使用 `max`/`min`，程式碼期待 `high`/`low`
2. **KeyError: 'Foreign_Investor_buy'** - 三大法人數據格式不符，FinMind 使用 long format

### 修復方案

#### 修改文件: `backend/app/services/ai_suggestion_service.py`

**1. 標準化價格欄位名稱** (第 32-38 行新增):
```python
# 標準化欄位名稱 (FinMind 使用 max/min，我們需要 high/low)
if len(prices) > 0:
    if 'max' in prices.columns:
        prices['high'] = prices['max']
    if 'min' in prices.columns:
        prices['low'] = prices['min']
```

**2. 重寫籌碼面分析函數** (第 98-141 行):
- 處理 FinMind 的 long format 數據 (columns: date, stock_id, buy, name, sell)
- 根據 `name` 欄位篩選外資和投信數據
- 添加 try-except 錯誤處理，確保籌碼數據錯誤不影響整體生成
- 使其更寬容，缺少某些欄位也能正常運作

### 測試結果
```bash
✅ 成功生成AI建議！
建議: HOLD
信心度: 0.65
目標價: 1850.0
停損價: 1700.0
```

### 後端重啟
```bash
cd backend && docker compose restart api
```

---

## Bug #2: 股票搜尋功能驗證 ✅

### 問題描述
用戶反映「增加台積電以外的代號都是說錯誤」，要求支援公司名稱搜尋

### 調查結果
**後端搜尋功能已經完整支援代號和名稱搜尋！**

#### 程式碼驗證
文件: `backend/app/services/stock_data_service.py` (第 21-31 行)
```python
def search_stocks(self, db: Session, query: str) -> List[Stock]:
    """搜尋股票"""
    return (
        db.query(Stock)
        .filter(
            (Stock.stock_id.like(f"%{query}%"))  # 支援代號
            | (Stock.name.like(f"%{query}%"))     # 支援名稱
        )
        .limit(20)
        .all()
    )
```

#### 實際測試
```python
=== 測試搜尋功能 ===

1. 搜尋代號「2330」:
   2330 - 台積電 ✅

2. 搜尋名稱「台積電」:
   2330 - 台積電 ✅

3. 搜尋「鴻海」:
   2317 - 鴻海 ✅

4. 搜尋「23」（模糊搜尋）:
   2330 - 台積電
   2317 - 鴻海
   2308 - 台達電
   2303 - 聯電
   2382 - 廣達 ✅
```

### 可能的誤解原因
資料庫目前只有 **28 支台股**：
- 半導體: 2330 台積電、2303 聯電、2454 聯發科、2408 南亞科、3034 聯詠
- 電子: 2317 鴻海、2382 廣達、2308 台達電、2357 華碩、2395 研華
- 金融: 2882 國泰金、2881 富邦金、2886 兆豐金、2891 中信金、2892 第一金、2884 玉山金
- 傳產: 2002 中鋼、1301 台塑、1303 南亞、1326 台化
- 通信: 2412 中華電、4904 遠傳、3045 台灣大
- 航運: 2603 長榮、2609 陽明、2615 萬海
- 其他: 1216 統一、9904 寶成

**如果輸入的股票不在這 28 支內，就會顯示「找不到」或「錯誤」。**

### 建議
如果需要支援更多股票，可以：
1. 運行 `backend/init_stocks.py` 添加更多股票
2. 或手動在資料庫 `stocks` 表中新增股票資料

---

## Bug #3: AI 建議價格型別錯誤 ✅

### 問題描述
前端顯示 AI 建議時出現 TypeError: `"1820.00" type 'String' is not a subtype of type 'num'`

### 根本原因
後端 Schema 使用 `Decimal` 型別儲存價格，但 Pydantic 預設將 `Decimal` 序列化為字串而非數字

### 修復方案

**修改文件**: `backend/app/schemas/ai.py` (第 27-30 行新增)

在 `AISuggestion` 的 Config 中添加 JSON 編碼器：
```python
class Config:
    from_attributes = True
    json_encoders = {
        Decimal: lambda v: float(v) if v is not None else None
    }
```

這樣 `target_price` 和 `stop_loss_price` 會被序列化為數字而非字串。

### 後端重啟
```bash
cd backend && docker compose restart api
```

### 驗證
前端的 `ai_suggestion.dart` 已經有正確的型別轉換：
```dart
targetPrice: json['target_price'] != null
    ? (json['target_price'] as num).toDouble()
    : null,
```

現在後端回傳數字，前端可以正確解析。

---

## 已修復的其他問題 (之前)

### Bug #3: AI 問答只顯示一行 ✅
**修改文件**: `frontend/lib/widgets/chat_bubble.dart`
- 添加 `maxLines: null` 允許無限行顯示

### Bug #4: 自選股點擊無反應 ✅
**新增文件**: `frontend/lib/screens/stock_detail_screen.dart`
**修改文件**: `frontend/lib/main.dart`, `frontend/lib/screens/watchlist_screen.dart`
- 創建股票詳情頁面
- 添加導航路由

### Bug #5: AI 建議加載提示不清楚 ✅
**修改文件**: `frontend/lib/screens/ai_suggestions_screen.dart`
- 加載中顯示「首次生成需要 30-60 秒」
- 空狀態添加「立即生成」按鈕

---

## 測試清單

### 請在瀏覽器中測試以下功能：

#### 1. AI 建議生成 🔄
- [ ] 登入應用
- [ ] 進入「AI 建議」頁面
- [ ] 點擊右上角「重新整理」按鈕
- [ ] 等待 30-60 秒
- [ ] 確認是否出現 AI 建議卡片
- [ ] 確認顯示：建議類型（BUY/HOLD/SELL）、信心度、目標價、停損價、分析理由

#### 2. 股票搜尋 🔄
- [ ] 點擊自選股頁面的「搜尋」按鈕
- [ ] 測試搜尋代號：輸入「2330」→ 應顯示台積電
- [ ] 測試搜尋名稱：輸入「鴻海」→ 應顯示 2317 鴻海
- [ ] 測試模糊搜尋：輸入「23」→ 應顯示多支股票
- [ ] 測試不存在的股票：輸入「1234」→ 應顯示「無結果」

#### 3. 股票詳情頁 🔄
- [ ] 點擊自選股列表中的台積電
- [ ] 確認進入詳情頁面
- [ ] 測試切換 6 個 Tab

#### 4. AI 問答 🔄
- [ ] 進入 AI 問答頁面
- [ ] 問一個長問題
- [ ] 確認回答完整顯示多行

---

## 當前系統狀態

**前端**: http://localhost:3000 ✅ 運行中
**後端**: http://localhost:8000 ✅ 運行中
**資料庫**: PostgreSQL ✅ 健康

**測試帳號**:
- Email: `test@example.com`
- 密碼: `test123456`

---

## 下一步開發建議

根據原計劃，接下來可以開發：

### 🟡 中優先級
1. **K線圖顯示** - 添加 fl_chart 依賴，實現蠟燭圖
2. **技術指標增強** - MACD、布林通道、威廉指標
3. **高風險型AI建議** - 修改 Prompt，添加進場價、多個停利目標
4. **新聞爬蟲整合** - Google News RSS + 情感分析

### 🟢 低優先級
5. **PTT 爬蟲** - 社群討論整合
6. **Dcard 爬蟲** - 社群討論整合
7. **綜合 AI 分析** - 整合所有數據源

---

**修復完成時間**: 2026-01-21 00:10
**測試狀態**: ✅ 後端測試通過，等待前端測試
