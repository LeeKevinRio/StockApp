"""
User model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    display_name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # OAuth fields
    auth_provider = Column(String(20), default='local')  # 'local' or 'google'
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    avatar_url = Column(String(500), nullable=True)

    # Activity tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Subscription fields
    subscription_tier = Column(String(20), default='free')  # 'free' or 'pro'
    is_admin = Column(Boolean, default=False)

    # 用戶偏好設定
    daily_summary_enabled = Column(Boolean, default=False)  # 是否訂閱每日盤前摘要 Email
    risk_preference = Column(String(20), default='moderate')  # 風險偏好: conservative / moderate / aggressive
