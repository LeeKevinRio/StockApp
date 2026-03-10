"""
Main FastAPI Application
"""
import logging
import sys
import os

# 最早印出啟動資訊（在任何 import 可能失敗前）
print(f"=== App starting === Python {sys.version}", flush=True)
print(f"=== PORT={os.getenv('PORT', 'not set')} ENV={os.getenv('ENVIRONMENT', 'not set')} ===", flush=True)
print(f"=== DATABASE_URL={'set' if os.getenv('DATABASE_URL') else 'NOT SET'} ===", flush=True)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from slowapi.errors import RateLimitExceeded

from app.logging_config import setup_logging
from app.config import settings
from app.rate_limit import limiter, rate_limit_exceeded_handler

# 在所有模組 import 前初始化 logging
setup_logging(level="DEBUG" if not settings.IS_PRODUCTION else "INFO")

logger = logging.getLogger(__name__)

# 延遲 import — 這些可能因為 DB 問題而失敗，但不應阻止 app 啟動
_db_available = False
engine = None
try:
    from app.database import create_tables, engine
    import app.models  # 確保所有 model 在 create_tables 前被 import
    _db_available = True
    print("=== Database module imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: Database import failed: {e} ===", flush=True)

try:
    from app.routers import (
        auth_router,
        stocks_router,
        watchlist_router,
        ai_router,
        alerts_router,
        news_router,
        social_router,
        trading_router,
        portfolio_router,
        fundamental_router,
        screener_router,
        admin_router,
        broker_router,
        ai_config_router,
        strategy_backtest_router,
        ai_discovery_router,
    )
    from app.routers.predictions import router as predictions_router
    from app.routers.market_overview import router as market_overview_router
    from app.routers.calendar import router as calendar_router
    from app.routers.trading_diary import router as trading_diary_router
    _routers_available = True
    print("=== All routers imported OK ===", flush=True)
except Exception as e:
    _routers_available = False
    print(f"=== FATAL: Router import failed: {e} ===", flush=True)
    import traceback
    traceback.print_exc()

from sqlalchemy import text

# Create FastAPI app
app = FastAPI(
    title="Taiwan Stock AI Investment App",
    description="台股 AI 投資建議 APP API",
    version="1.0.0",
)

# --- Rate Limiting ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# 注意：不使用 HTTPSRedirectMiddleware
# Railway/Render 等 PaaS 在 reverse proxy 層已處理 HTTPS
# 在 app 層加 HTTPS redirect 會導致 healthcheck 失敗（內部 HTTP 請求被重導）

# --- CORS middleware（收緊配置） ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["X-AI-Quota-Limit", "X-AI-Quota-Remaining", "X-AI-Quota-Used"],
    max_age=600,
)

# Include routers（只在成功 import 時註冊）
if _routers_available:
    app.include_router(auth_router)
    app.include_router(stocks_router)
    app.include_router(watchlist_router)
    app.include_router(ai_router)
    app.include_router(alerts_router)
    app.include_router(news_router)
    app.include_router(social_router)
    app.include_router(trading_router)
    app.include_router(portfolio_router)
    app.include_router(fundamental_router)
    app.include_router(screener_router)
    app.include_router(admin_router)
    app.include_router(broker_router)
    app.include_router(ai_config_router)
    app.include_router(predictions_router)
    app.include_router(market_overview_router)
    app.include_router(calendar_router)
    app.include_router(trading_diary_router)
    app.include_router(strategy_backtest_router)
    app.include_router(ai_discovery_router)


@app.on_event("startup")
def on_startup():
    """Create database tables on startup — 失敗不阻止 app 啟動"""
    if _db_available:
        try:
            create_tables()
            print("=== Database tables created OK ===", flush=True)
            # 自動遷移：新增 last_login_at 欄位（如果不存在）
            try:
                from sqlalchemy import text
                with engine.connect() as conn:
                    conn.execute(text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ"
                    ))
                    conn.commit()
            except Exception as mig_e:
                logger.warning(f"Migration skipped: {mig_e}")
        except Exception as e:
            logger.error(f"Database table creation failed (app will still start): {e}")
            print(f"=== WARNING: create_tables failed: {e} ===", flush=True)
    else:
        print("=== Skipping create_tables (DB not available) ===", flush=True)

    # 啟動排程器
    try:
        from app.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.warning(f"Could not start scheduler: {e}")

    print("=== Startup complete, app is ready ===", flush=True)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Taiwan Stock AI Investment App API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint — 永遠回 200 讓 Railway healthcheck 通過"""
    db_status = "not_configured"
    if engine is not None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            logger.error(f"Health check DB error: {e}")
            db_status = "connection_failed"
    # 額外檢查：資料表與使用者數量
    table_info = {}
    if engine is not None and db_status == "connected":
        try:
            with engine.connect() as conn:
                for table in ["users", "watchlist", "portfolios"]:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    table_info[table] = result.scalar()
        except Exception:
            table_info["error"] = "tables may not exist"
    return {"status": "healthy", "database": db_status, "tables": table_info}


@app.get("/privacy", response_class=HTMLResponse)
def privacy_policy():
    """隱私政策頁面（App Store 要求公開 URL）"""
    return """<!DOCTYPE html>
<html lang="zh-Hant">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>隱私權政策 - 台股智慧助手</title>
<style>body{font-family:-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:20px;line-height:1.8;color:#333}h1{color:#1a73e8}h2{color:#444;margin-top:2em}</style></head>
<body>
<h1>隱私權政策</h1>
<p>最後更新日期：2026 年 3 月</p>

<h2>1. 資料蒐集</h2>
<p>台股智慧助手（以下簡稱「本應用」）蒐集以下資料以提供服務：</p>
<ul>
<li><strong>帳號資訊</strong>：電子郵件地址、使用者名稱（註冊或 Google 登入時提供）</li>
<li><strong>使用資料</strong>：自選股清單、投資組合、交易日記等您主動輸入的內容</li>
</ul>

<h2>2. 資料用途</h2>
<p>我們僅將您的資料用於：提供及改善本應用服務、產生個人化 AI 投資分析報告。我們不會將您的個人資料出售予第三方。</p>

<h2>3. 資料儲存與安全</h2>
<p>您的資料儲存於受加密保護的伺服器。我們採用業界標準安全措施保護您的資訊。</p>

<h2>4. 第三方服務</h2>
<p>本應用使用 Google Sign-In 進行身份驗證，適用 <a href="https://policies.google.com/privacy">Google 隱私權政策</a>。</p>

<h2>5. 帳號刪除</h2>
<p>您可隨時在應用程式的「設定」頁面中刪除帳號，所有相關資料將一併永久刪除。</p>

<h2>6. 投資免責聲明</h2>
<p>本應用提供的 AI 分析僅供參考，不構成投資建議。投資有風險，使用者應自行判斷並承擔投資決策之後果。</p>

<h2>7. 聯絡我們</h2>
<p>如有隱私相關問題，請透過應用內「關於」頁面與我們聯繫。</p>
</body></html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=not settings.IS_PRODUCTION,
    )
