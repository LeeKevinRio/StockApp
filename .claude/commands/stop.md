---
name: stop
description: 停止前後端開發伺服器
---

# 停止前後端開發伺服器

停止所有 StockApp 相關的開發伺服器。

## 步驟

1. 找到並終止佔用 port 8000 的後端 process
2. 找到並終止佔用 port 5000 的前端 process
3. 如果有 flutter 相關的 dart process 也一併終止

## 指令參考
- Windows: `netstat -ano | findstr :8000` 找 PID，然後 `taskkill /PID <pid> /F`
- 或直接: `taskkill /F /IM python.exe` + `taskkill /F /IM dart.exe`（注意可能影響其他 process）

## 回報結果
- 確認 port 8000 和 5000 都已釋放
