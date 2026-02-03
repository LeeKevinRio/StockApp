"""
Chip Analysis Schemas
專業級高風險交易分析平台 - 籌碼分析數據模型
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class DailyFlow(BaseModel):
    """每日法人買賣超"""
    date: str
    foreign_net: int
    trust_net: int
    dealer_net: int
    total_net: int


class DailyMargin(BaseModel):
    """每日融資融券"""
    date: str
    margin_balance: int
    margin_change: int
    short_balance: int


class InstitutionalSummary(BaseModel):
    """法人統計摘要"""
    foreign_5d_net: int
    foreign_10d_net: int
    foreign_20d_net: int
    trust_5d_net: int
    trust_10d_net: int
    dealer_5d_net: int
    total_5d_net: int
    total_10d_net: int


class MarginSummary(BaseModel):
    """融資融券摘要"""
    current_balance: int
    current_utilization: float
    short_balance: int
    short_ratio: float
    margin_5d_change: int
    margin_trend: str


class ChipMomentum(BaseModel):
    """籌碼動能"""
    momentum_score: float
    momentum_direction: str
    foreign_momentum: float
    trust_momentum: float
    margin_momentum: float
    signals: List[str]
    recommendation: str


class ChipOverall(BaseModel):
    """籌碼綜合評估"""
    score: float
    direction: str
    direction_cn: str
    suggestion: str
    strengths: List[str]
    weaknesses: List[str]
    warnings: List[str]


class ChipAnalysis(BaseModel):
    """完整籌碼分析"""
    stock_id: str
    name: str
    current_price: float
    analysis_days: int
    institutional: Optional[InstitutionalSummary] = None
    margin: Optional[MarginSummary] = None
    momentum: ChipMomentum
    overall: ChipOverall
    daily_flows: List[DailyFlow] = []
    daily_margin: List[DailyMargin] = []

    class Config:
        from_attributes = True
