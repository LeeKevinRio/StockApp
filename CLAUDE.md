# Claude Code 操作規則

## Git 自動化
- **每次修改程式碼後**，必須自動執行 `git add` + `git commit` + `git push`
- Commit 訊息使用繁體中文，格式：`<type>: <簡短描述>`
  - `feat:` 新功能
  - `fix:` 修復 bug
  - `refactor:` 重構
  - `style:` 樣式調整
  - `docs:` 文件更新
  - `chore:` 雜項維護
- Push 至 `origin` 的當前分支

## 程式碼規範
- 註解與使用者溝通使用繁體中文
- 修改前先讀取檔案，理解現有程式碼再做變更
- 不做超出需求範圍的額外修改

## 上架意識提醒
- 每次修改完成後，簡短提醒目前專案距離 App Store 上架還有哪些**最關鍵的差距**（1-3 點即可）
- 完整審查流程請參考：`prompts/appstore-audit.md`

## 固定 Port（禁止修改）
- **前端 Flutter Web**：`5000`（所有啟動腳本、skill 皆固定此 port）
- **後端 FastAPI**：`8000`
- 修改程式碼時**嚴禁變更**上述 port，除非用戶明確要求

## 專案資訊
- 遠端倉庫：https://github.com/LeeKevinRio/StockApp
- 主分支：main
- 技術架構：Flutter (前端) + FastAPI (後端) + PostgreSQL (資料庫)
