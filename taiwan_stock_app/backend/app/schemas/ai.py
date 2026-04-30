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


class NextDayPrediction(BaseModel):
    """隔天漲跌預測"""
    direction: str  # 'UP' or 'DOWN'
    probability: float  # 0.55 ~ 0.95
    predicted_change_percent: float  # 預測漲跌幅 %
    price_range_low: Optional[float] = None  # 預測最低價
    price_range_high: Optional[float] = None  # 預測最高價
    reasoning: str  # 預測依據說明


class AISuggestion(BaseModel):
    stock_id: str
    name: str
    suggestion: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 ~ 1.0 (對建議的信心度)
    bullish_probability: Optional[float] = None  # 0.0 ~ 1.0 (看漲機率，更直覺的指標)
    current_price: Optional[Decimal] = None  # 最新收盤價
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

    # 隔天漲跌預測
    next_day_prediction: Optional[dict] = None  # NextDayPrediction 格式

    # 個股歷史準確率（信任徽章用，僅 n_records >= 3 才提供）
    historical_accuracy: Optional[dict] = None

    # AI 提供者：'Gemini' / 'Groq' / 'Mock' / 自定義 BYOK 名稱
    # 前端可在 Mock 時顯示提示，避免使用者誤以為是真 AI 結果
    ai_provider: Optional[str] = None

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
