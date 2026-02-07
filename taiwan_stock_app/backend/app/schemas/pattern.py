"""
Pattern Recognition Schemas
形態識別 API 響應模型
"""
from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum


class PatternType(str, Enum):
    """形態類型"""
    HEAD_SHOULDERS_TOP = "head_shoulders_top"
    HEAD_SHOULDERS_BOTTOM = "head_shoulders_bottom"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_TOP = "triple_top"
    TRIPLE_BOTTOM = "triple_bottom"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRIC_TRIANGLE = "symmetric_triangle"
    RISING_WEDGE = "rising_wedge"
    FALLING_WEDGE = "falling_wedge"
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    RECTANGLE = "rectangle"
    BREAKOUT_UP = "breakout_up"
    BREAKOUT_DOWN = "breakout_down"


class PatternSignal(str, Enum):
    """形態信號方向"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class PatternItem(BaseModel):
    """單個形態項目"""
    pattern_type: PatternType
    signal: PatternSignal
    confidence: float
    start_index: int
    end_index: int
    key_prices: Dict[str, float]
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    description: str
    is_confirmed: bool

    class Config:
        use_enum_values = True


class PatternResponse(BaseModel):
    """形態識別響應"""
    stock_id: str
    has_patterns: bool
    dominant_signal: Optional[PatternSignal] = None
    patterns: List[PatternItem]

    class Config:
        use_enum_values = True
