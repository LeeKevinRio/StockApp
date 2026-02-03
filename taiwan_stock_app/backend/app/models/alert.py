"""
價格警示模型
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class PriceAlert(Base):
    """價格警示"""
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False, index=True)

    # 警示類型: 'ABOVE' (高於), 'BELOW' (低於), 'PERCENT_UP' (漲幅), 'PERCENT_DOWN' (跌幅)
    alert_type = Column(String(20), nullable=False)

    # 目標價格 (用於 ABOVE/BELOW)
    target_price = Column(Numeric(10, 2))

    # 百分比閾值 (用於 PERCENT_UP/PERCENT_DOWN)
    percent_threshold = Column(Numeric(5, 2))

    # 狀態
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime(timezone=True))
    triggered_price = Column(Numeric(10, 2))  # 觸發時的價格

    # 通知方式
    notify_push = Column(Boolean, default=True)  # 推送通知
    notify_email = Column(Boolean, default=False)  # 郵件通知

    # 備註
    notes = Column(String(500))

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯
    user = relationship("User", backref="price_alerts")
    stock = relationship("Stock", backref="price_alerts")

    def __repr__(self):
        return f"<PriceAlert {self.stock_id} {self.alert_type} {self.target_price}>"
