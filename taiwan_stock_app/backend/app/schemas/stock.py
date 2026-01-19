"""
Stock schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class StockBase(BaseModel):
    stock_id: str
    name: str
    market: str  # 'TWSE' or 'TPEx'


class StockDetail(StockBase):
    english_name: Optional[str] = None
    industry: Optional[str] = None
    listed_date: Optional[date] = None

    class Config:
        from_attributes = True


class StockPrice(BaseModel):
    stock_id: str
    name: str
    current_price: Decimal
    change: Decimal
    change_percent: Decimal
    open: Decimal
    high: Decimal
    low: Decimal
    volume: int
    updated_at: datetime


class StockHistory(BaseModel):
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    class Config:
        from_attributes = True
