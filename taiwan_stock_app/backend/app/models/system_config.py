"""
System config model — 用來持久化 server 端的設定值。

主要用途：
- 持久化 JWT_SECRET，避免每次後端重啟都自動生成新 secret 把所有使用者踢出去
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    key = Column(String(100), primary_key=True)
    value = Column(String, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
