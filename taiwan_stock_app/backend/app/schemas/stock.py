"""
Stock schemas
"""
from pydantic import BaseModel, field_serializer
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

    @field_serializer('current_price', 'change', 'change_percent', 'open', 'high', 'low')
    def serialize_decimal(self, v: Decimal) -> float:
        return float(v) if v is not None else 0.0


class StockHistory(BaseModel):
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    class Config:
        from_attributes = True

    @field_serializer('open', 'high', 'low', 'close')
    def serialize_decimal(self, v: Decimal) -> float:
        return float(v) if v is not None else 0.0
