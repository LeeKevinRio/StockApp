"""
Pydantic schemas for request/response validation
"""
from .user import UserCreate, UserLogin, UserResponse, Token
from .stock import StockBase, StockDetail, StockPrice, StockHistory
from .watchlist import WatchlistItem, WatchlistAdd
from .ai import AISuggestion, AIChatRequest, AIChatResponse, ChatMessage

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "StockBase",
    "StockDetail",
    "StockPrice",
    "StockHistory",
    "WatchlistItem",
    "WatchlistAdd",
    "AISuggestion",
    "AIChatRequest",
    "AIChatResponse",
    "ChatMessage",
]
