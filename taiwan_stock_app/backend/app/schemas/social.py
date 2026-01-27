"""
社群情緒 Schemas
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date


class SocialPostResponse(BaseModel):
    id: int
    platform: str
    board: Optional[str] = None
    title: str
    content: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    mentioned_stocks: Optional[List[str]] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    push_count: int = 0
    boo_count: int = 0
    comment_count: int = 0
    posted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StockSentimentResponse(BaseModel):
    stock_id: str
    date: date
    mention_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    sentiment_score: Optional[float] = None
    heat_level: Optional[str] = None

    class Config:
        from_attributes = True


class HotStockResponse(BaseModel):
    stock_id: str
    stock_name: Optional[str] = None
    mention_count: int
    sentiment_score: Optional[float] = None
    sentiment: str  # positive, negative, neutral
    sample_posts: List[SocialPostResponse]


class SocialAnalysisResponse(BaseModel):
    stock_id: str
    total_mentions: int
    sentiment_summary: dict
    recent_posts: List[SocialPostResponse]
    sentiment_trend: List[StockSentimentResponse]
