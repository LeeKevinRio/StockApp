"""
API Routers
"""
from .auth import router as auth_router
from .stocks import router as stocks_router
from .watchlist import router as watchlist_router
from .ai import router as ai_router
from .alerts import router as alerts_router
from .news import router as news_router
from .social import router as social_router
from .trading import router as trading_router
from .portfolio import router as portfolio_router
from .fundamental import router as fundamental_router
from .screener import router as screener_router
from .admin import router as admin_router
from .broker import router as broker_router
from .ai_config import router as ai_config_router
from .strategy_backtest import router as strategy_backtest_router
from .ai_discovery import router as ai_discovery_router

__all__ = [
    "auth_router",
    "stocks_router",
    "watchlist_router",
    "ai_router",
    "alerts_router",
    "news_router",
    "social_router",
    "trading_router",
    "portfolio_router",
    "fundamental_router",
    "screener_router",
    "admin_router",
    "broker_router",
    "ai_config_router",
    "strategy_backtest_router",
    "ai_discovery_router",
]
