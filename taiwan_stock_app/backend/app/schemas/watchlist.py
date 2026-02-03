"""
Watchlist schemas - 支援台股(TW)與美股(US)
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class WatchlistAdd(BaseModel):
    stock_id: str
    notes: Optional[str] = None
    market: Optional[str] = "TW"  # 'TW' or 'US'


class WatchlistItem(BaseModel):
    stock_id: str
    name: str
    current_price: float
    change_percent: float
    added_at: Optional[datetime] = None
    notes: Optional[str] = None
    market_region: Optional[str] = "TW"  # 'TW' or 'US'
    currency: Optional[str] = "TWD"  # 'TWD' or 'USD'

    class Config:
        from_attributes = True
