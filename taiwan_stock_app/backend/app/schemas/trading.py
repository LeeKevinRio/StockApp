"""
模擬交易 Schemas
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AccountResponse(BaseModel):
    id: int
    user_id: int
    initial_balance: float
    cash_balance: float
    total_value: float
    total_profit_loss: float
    total_profit_loss_percent: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    id: int
    stock_id: str
    stock_name: Optional[str] = None
    quantity: int
    avg_cost: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: float
    unrealized_pnl_percent: float

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    stock_id: str
    order_type: str  # BUY, SELL
    quantity: int
    price: float


class OrderResponse(BaseModel):
    id: int
    stock_id: str
    stock_name: Optional[str] = None
    order_type: str
    quantity: int
    price: float
    filled_quantity: int
    filled_price: Optional[float] = None
    status: str
    created_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccountSummary(BaseModel):
    account: AccountResponse
    positions: List[PositionResponse]
    recent_orders: List[OrderResponse]


class TradeResult(BaseModel):
    success: bool
    message: str
    order: Optional[OrderResponse] = None
