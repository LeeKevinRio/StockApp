"""
價格警示 Schema
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PriceAlertCreate(BaseModel):
    """建立價格警示"""
    stock_id: str
    alert_type: str  # 'ABOVE', 'BELOW', 'PERCENT_UP', 'PERCENT_DOWN'
    target_price: Optional[Decimal] = None
    percent_threshold: Optional[Decimal] = None
    notify_push: bool = True
    notify_email: bool = False
    notes: Optional[str] = None


class PriceAlertUpdate(BaseModel):
    """更新價格警示"""
    target_price: Optional[Decimal] = None
    percent_threshold: Optional[Decimal] = None
    is_active: Optional[bool] = None
    notify_push: Optional[bool] = None
    notify_email: Optional[bool] = None
    notes: Optional[str] = None


class PriceAlertResponse(BaseModel):
    """價格警示回應"""
    id: int
    stock_id: str
    stock_name: Optional[str] = None
    alert_type: str
    target_price: Optional[Decimal] = None
    percent_threshold: Optional[Decimal] = None
    is_active: bool
    is_triggered: bool
    triggered_at: Optional[datetime] = None
    triggered_price: Optional[Decimal] = None
    notify_push: bool
    notify_email: bool
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertTriggerInfo(BaseModel):
    """警示觸發資訊"""
    alert_id: int
    stock_id: str
    stock_name: str
    alert_type: str
    target_price: Optional[Decimal] = None
    current_price: Decimal
    triggered_at: datetime
    message: str
