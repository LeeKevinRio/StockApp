"""
AI schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal


class KeyFactor(BaseModel):
    category: str
    factor: str
    impact: str  # 'positive', 'negative', 'neutral'


class AISuggestion(BaseModel):
    stock_id: str
    name: str
    suggestion: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 ~ 1.0
    target_price: Optional[Decimal] = None
    stop_loss_price: Optional[Decimal] = None
    reasoning: str
    key_factors: List[dict]
    report_date: date

    class Config:
        from_attributes = True


class AIChatRequest(BaseModel):
    message: str
    stock_id: Optional[str] = None  # 若指定則針對該股票回答


class AIChatResponse(BaseModel):
    response: str
    related_stocks: List[str]  # 回答中提到的相關股票
    sources: List[str]  # 資料來源


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    sources: Optional[List[str]] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
