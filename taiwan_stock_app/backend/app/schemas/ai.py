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


class TakeProfitTarget(BaseModel):
    """停利目標"""
    price: float
    probability: float  # 0.0 ~ 1.0
    description: str  # 保守/中性/積極


class AISuggestion(BaseModel):
    stock_id: str
    name: str
    suggestion: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 ~ 1.0 (對建議的信心度)
    bullish_probability: Optional[float] = None  # 0.0 ~ 1.0 (看漲機率，更直覺的指標)
    target_price: Optional[Decimal] = None
    stop_loss_price: Optional[Decimal] = None
    reasoning: str
    key_factors: List[dict]
    report_date: date

    # 高風險型經紀人新增欄位
    entry_price_min: Optional[Decimal] = None
    entry_price_max: Optional[Decimal] = None
    take_profit_targets: Optional[List[dict]] = None
    risk_level: Optional[str] = None  # HIGH, MEDIUM, LOW
    time_horizon: Optional[str] = None  # 短線/中線/長線
    predicted_change_percent: Optional[Decimal] = None

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }


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
