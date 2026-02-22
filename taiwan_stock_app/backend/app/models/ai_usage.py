"""
AIUsageDaily Model — 每用戶每日 AI 呼叫次數追蹤
"""

from sqlalchemy import Column, Integer, Date, ForeignKey, UniqueConstraint
from app.database import Base


class AIUsageDaily(Base):
    """每用戶每天一筆，記錄 AI 呼叫次數"""
    __tablename__ = "ai_usage_daily"
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_user_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    usage_date = Column(Date, nullable=False, index=True)
    call_count = Column(Integer, nullable=False, default=0)
