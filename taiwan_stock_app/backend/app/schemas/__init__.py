"""
Pydantic schemas for request/response validation
"""
from .user import UserCreate, UserLogin, UserResponse, Token
from .stock import StockBase, StockDetail, StockPrice, StockHistory
from .watchlist import WatchlistItem, WatchlistAdd
from .ai import AISuggestion, AIChatRequest, AIChatResponse, ChatMessage
from .indicator import (
    IndicatorDataPoint,
    MACDDataPoint,
    BollingerDataPoint,
    KDDataPoint,
    RSIResponse,
    MACDResponse,
    BollingerResponse,
    KDResponse,
    AllIndicatorsResponse,
)
from .fundamental import (
    FundamentalResponse,
    FinancialStatementsResponse,
    DividendResponse,
    InstitutionalResponse,
    MarginResponse,
    ScreenCriteria,
    ScreenResultItem,
    ScreenResponse,
    PresetScreen,
)

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
    "IndicatorDataPoint",
    "MACDDataPoint",
    "BollingerDataPoint",
    "KDDataPoint",
    "RSIResponse",
    "MACDResponse",
    "BollingerResponse",
    "KDResponse",
    "AllIndicatorsResponse",
    "FundamentalResponse",
    "FinancialStatementsResponse",
    "DividendResponse",
    "InstitutionalResponse",
    "MarginResponse",
    "ScreenCriteria",
    "ScreenResultItem",
    "ScreenResponse",
    "PresetScreen",
]
