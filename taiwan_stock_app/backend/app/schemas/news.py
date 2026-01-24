"""
新聞 Schemas
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class NewsBase(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    published_at: Optional[datetime] = None


class NewsResponse(NewsBase):
    id: Optional[int] = None
    stock_id: Optional[str] = None
    fetched_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    stock_id: Optional[str] = None
    total: int
    news: List[NewsResponse]


class MarketNewsResponse(BaseModel):
    total: int
    news: List[NewsResponse]
