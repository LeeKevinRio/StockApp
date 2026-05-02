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
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import OperationalError, DBAPIError

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
    )
    _routers_available = True
    print("=== Core routers imported OK ===", flush=True)
except Exception as e:
    _routers_available = False
    print(f"=== FATAL: Core router import failed: {e} ===", flush=True)
    import traceback
    traceback.print_exc()

# 次要核心路由：獨立 import，失敗不影響主要功能
predictions_router = None
market_overview_router = None
calendar_router = None
trading_diary_router = None
strategy_backtest_router = None
ai_discovery_router = None

try:
    from app.routers.predictions import router as predictions_router
    print("=== predictions_router imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: predictions_router import failed: {e} ===", flush=True)

try:
    from app.routers.market_overview import router as market_overview_router
    print("=== market_overview_router imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: market_overview_router import failed: {e} ===", flush=True)

try:
    from app.routers.calendar import router as calendar_router
    print("=== calendar_router imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: calendar_router import failed: {e} ===", flush=True)

try:
    from app.routers.trading_diary import router as trading_diary_router
    print("=== trading_diary_router imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: trading_diary_router import failed: {e} ===", flush=True)

try:
    from app.routers.strategy_backtest import router as strategy_backtest_router
    print("=== strategy_backtest_router imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: strategy_backtest_router import failed: {e} ===", flush=True)

try:
    from app.routers.ai_discovery import router as ai_discovery_router
    print("=== ai_discovery_router imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: ai_discovery_router import failed: {e} ===", flush=True)

# 新功能路由：獨立 import，失敗不影響核心功能
crypto_router = None
daily_summary_router = None
macro_router = None
portfolio_recommendation_router = None

try:
    from app.routers.crypto import router as crypto_router
    print("=== crypto_router imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: crypto_router import failed: {e} ===", flush=True)

try:
    from app.routers.daily_summary import router as daily_summary_router
    print("=== daily_summary_router imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: daily_summary_router import failed: {e} ===", flush=True)

try:
    from app.routers.macro import router as macro_router
    print("=== macro_router imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: macro_router import failed: {e} ===", flush=True)

try:
    from app.routers.portfolio_recommendation import router as portfolio_recommendation_router
    print("=== portfolio_recommendation_router imported OK ===", flush=True)
except Exception as e:
    print(f"=== WARNING: portfolio_recommendation_router import failed: {e} ===", flush=True)

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


# --- DB 不可用：統一回 503，避免前端拿到 500 卻不知道是 DB 問題 ---
@app.exception_handler(OperationalError)
@app.exception_handler(DBAPIError)
def _db_unavailable_handler(request: Request, exc: Exception):
    logger.error(f"Database unavailable: {exc}")
    return JSONResponse(
        status_code=503,
        content={"detail": "資料庫暫時無法連線，請稍後再試", "error_type": "db_unavailable"},
    )

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

# 非核心路由：僅在成功 import 時註冊（失敗不影響核心功能）
for _name, _router in [
    ("predictions", predictions_router),
    ("market_overview", market_overview_router),
    ("calendar", calendar_router),
    ("trading_diary", trading_diary_router),
    ("strategy_backtest", strategy_backtest_router),
    ("ai_discovery", ai_discovery_router),
    ("crypto", crypto_router),
    ("daily_summary", daily_summary_router),
    ("macro", macro_router),
    ("portfolio_recommendation", portfolio_recommendation_router),
]:
    if _router is not None:
        app.include_router(_router)
        print(f"=== {_name}_router registered OK ===", flush=True)


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
                    conn.execute(text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_summary_enabled BOOLEAN DEFAULT FALSE"
                    ))
                    conn.execute(text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS risk_preference VARCHAR(20) DEFAULT 'moderate'"
                    ))
                    conn.commit()
            except Exception as mig_e:
                logger.warning(f"Migration skipped: {mig_e}")
        except Exception as e:
            logger.error(f"Database table creation failed (app will still start): {e}")
            print(f"=== WARNING: create_tables failed: {e} ===", flush=True)
    else:
        print("=== Skipping create_tables (DB not available) ===", flush=True)

    # JWT secret 預載入：失敗也沒關係，第一個 request 會 lazy load。
    # 故意放在 create_tables 的 try 之外，即使 tables 建立失敗也會試。
    try:
        from app.auth_secret import preload_jwt_secret
        ok = preload_jwt_secret()
        print(f"=== JWT secret preload: {'OK' if ok else 'WILL_RETRY_ON_REQUEST'} ===", flush=True)
    except Exception as jwt_e:
        print(f"=== JWT secret preload error (will retry on first request): {jwt_e} ===", flush=True)

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
