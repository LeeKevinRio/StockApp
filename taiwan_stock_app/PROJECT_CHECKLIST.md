# StockApp 專案檢查清單

## 環境配置檢查

### 後端 (.env)
```
位置: backend/.env
```

| 變數 | 說明 | 必填 |
|------|------|------|
| `DATABASE_URL` | 資料庫連線 | ✅ |
| `GOOGLE_API_KEY` | Gemini AI API | ✅ |
| `GROQ_API_KEY` | Groq AI (備援) | ✅ |
| `GOOGLE_CLIENT_ID` | Google OAuth | ✅ |
| `GOOGLE_CLIENT_SECRET` | Google OAuth | ⚠️ |
| `JWT_SECRET` | JWT 密鑰 | ✅ |
| `FINMIND_TOKEN` | FinMind API | ⚠️ |
| `FUGLE_API_KEY` | Fugle API | ⚠️ |

### 前端 (web/index.html)
```
位置: frontend/web/index.html
```

| 設定 | 說明 |
|------|------|
| `google-signin-client_id` | 必須與後端 GOOGLE_CLIENT_ID 一致 |

---

## 執行前檢查

### 1. 後端服務
```bash
# 檢查後端是否運行
curl http://localhost:8000/health

# 預期回應
{"status":"healthy"}
```

### 2. 前端服務
```bash
# 檢查 Flutter 是否運行
# 預期: Chrome 開啟 http://localhost:3000
```

### 3. 資料庫
```bash
# SQLite 資料庫位置
backend/stock_app.db
```

---

## 常見問題排查

### Google 登入失敗
1. 檢查 `GOOGLE_CLIENT_ID` 是否正確設定
2. 檢查 `frontend/web/index.html` 的 client_id 是否一致
3. 確認 Google Cloud Console 已設定:
   - 已授權的 JavaScript 來源: `http://localhost:3000`
   - 已授權的重新導向 URI: `http://localhost:3000`

### AI 建議失敗
1. 檢查 `GOOGLE_API_KEY` (Gemini)
2. 若 Gemini 配額用完，會自動切換到 Groq
3. 檢查 `GROQ_API_KEY`

### 股票資料載入慢
1. 檢查 `FINMIND_TOKEN`
2. 檢查 `FUGLE_API_KEY`

---

## 服務啟動指令

### 後端
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端
```bash
cd frontend
flutter run -d chrome --web-port=3000
```

---

## 目前專案狀態

### 已完成功能
- [x] 使用者註冊/登入 (支援任意帳號字串)
- [x] Google OAuth 登入
- [x] 自選股管理
- [x] 股票搜尋
- [x] AI 投資建議 (Gemini + Groq 備援)
- [x] 技術指標分析
- [x] K線圖表
- [x] 價格警報
- [x] AI 預測追蹤系統
- [x] 推播通知

### 待處理
- [ ] Google OAuth 403 錯誤修復中

---

## 更新日誌

### 2024-02-06
- 修改註冊/登入允許任意字串帳號
- 配置 Google OAuth Client ID
