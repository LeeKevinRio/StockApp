"""
Alert Schemas
專業級高風險交易分析平台 - 告警數據模型
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class AlertType(str, Enum):
    """告警類型"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    CHANGE_PERCENT_ABOVE = "change_percent_above"
    CHANGE_PERCENT_BELOW = "change_percent_below"
    VOLUME_ABOVE = "volume_above"
    SIGNAL_BUY = "signal_buy"
    SIGNAL_SELL = "signal_sell"
    PATTERN_BREAKOUT = "pattern_breakout"
    SUPPORT_BREAK = "support_break"
    RESISTANCE_BREAK = "resistance_break"


class AlertStatus(str, Enum):
    """告警狀態"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AlertCreate(BaseModel):
    """創建告警請求"""
    stock_id: str
    stock_name: str
    alert_type: AlertType
    condition_value: float
    message: Optional[str] = None
    expires_days: int = 30


class AlertResponse(BaseModel):
    """告警響應"""
    id: str
    user_id: int
    stock_id: str
    stock_name: str
    alert_type: str
    condition_value: float
    message: str
    status: str
    created_at: str
    triggered_at: Optional[str] = None
    expires_at: Optional[str] = None

    class Config:
        from_attributes = True


class AlertNotificationResponse(BaseModel):
    """告警通知響應"""
    alert_id: str
    user_id: int
    stock_id: str
    stock_name: str
    alert_type: str
    message: str
    current_value: float
    condition_value: float
    triggered_at: str

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """告警列表響應"""
    alerts: List[AlertResponse]
    total: int


class NotificationListResponse(BaseModel):
    """通知列表響應"""
    notifications: List[AlertNotificationResponse]
    total: int


class WebSocketMessage(BaseModel):
    """WebSocket 消息格式"""
    type: str
    data: dict
    timestamp: str


class SubscriptionRequest(BaseModel):
    """訂閱請求"""
    action: str  # subscribe, unsubscribe
    stock_id: Optional[str] = None
    broadcast: bool = False
