"""
Industry Trend Analysis Schemas
"""
from pydantic import BaseModel
from typing import List, Optional


class BullishIndustry(BaseModel):
    """看漲產業"""
    industry: str
    probability: float  # 0.0 ~ 1.0
    reasoning: str
    key_factors: List[str]
    representative_stocks: List[str]
    risk_factors: List[str]


class BearishIndustry(BaseModel):
    """看跌產業"""
    industry: str
    probability: float  # 0.0 ~ 1.0
    reasoning: str
    key_factors: List[str]
    representative_stocks: List[str]
    avoid_reasons: List[str]


class NeutralIndustry(BaseModel):
    """中性產業"""
    industry: str
    reasoning: str


class IndustryTrendAnalysis(BaseModel):
    """產業趨勢分析結果"""
    analysis_date: str
    market_overview: str
    bullish_industries: List[BullishIndustry]
    bearish_industries: List[BearishIndustry]
    neutral_industries: Optional[List[NeutralIndustry]] = []
    investment_suggestions: str
    disclaimer: str

    class Config:
        from_attributes = True
