"""
API Routers
"""
from .auth import router as auth_router
from .stocks import router as stocks_router
from .watchlist import router as watchlist_router
from .ai import router as ai_router

__all__ = ["auth_router", "stocks_router", "watchlist_router", "ai_router"]
