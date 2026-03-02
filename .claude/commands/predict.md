---
name: predict
description: 觸發 AI 預測
argument-hint: "[--all]"
---

# 觸發 AI 預測

為所有自選股生成 AI 預測。

## 使用方式
- `/predict` — 只補齊今天缺少的預測（增量模式）
- `/predict --all` — 強制重新生成全部預測

## 步驟

1. 進入 `taiwan_stock_app/backend/` 目錄
2. 根據參數決定執行模式：
   - 無參數或未帶 `--all`：執行 `python trigger_predictions.py`
   - 帶 `--all`：執行 `python trigger_predictions.py --all`
3. 等待執行完成（可能需要數分鐘，取決於自選股數量）
4. 回報結果統計（成功/跳過/失敗數量）

## 注意事項
- 每 3 支股票會暫停 2 秒以避免 API 速率限制
- 如果 Gemini 配額用完會自動 fallback 到 Groq
- base_price 無效的股票會自動跳過
