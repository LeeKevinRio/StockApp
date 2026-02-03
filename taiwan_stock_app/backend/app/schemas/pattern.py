"""
Pattern Recognition Schemas
專業級高風險交易分析平台 - 形態識別數據模型
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class PatternDetail(BaseModel):
    """單一形態詳情"""
    type: str  # 形態類型
    signal: str  # bullish, bearish, neutral
    confidence: float  # 信心度 0-100
    description: str  # 形態描述
    target_price: Optional[float]  # 目標價
    stop_loss: Optional[float]  # 建議停損
    is_confirmed: bool  # 是否已確認突破
    key_prices: Dict[str, float]  # 關鍵價位


class PatternAnalysis(BaseModel):
    """形態分析結果"""
    stock_id: str
    name: str
    current_price: float
    has_patterns: bool
    dominant_signal: str  # bullish, bearish, neutral
    patterns_count: int
    bullish_count: int
    bearish_count: int
    bullish_score: float
    bearish_score: float
    summary: str
    top_patterns: List[PatternDetail]

    class Config:
        from_attributes = True
