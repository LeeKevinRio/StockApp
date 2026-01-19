"""
Watchlist schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class WatchlistAdd(BaseModel):
    stock_id: str
    notes: Optional[str] = None


class WatchlistItem(BaseModel):
    stock_id: str
    name: str
    current_price: Decimal
    change_percent: Decimal
    added_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True
