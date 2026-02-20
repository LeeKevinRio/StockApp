"""
UserAIConfig Model — 用戶自訂 AI 配置（BYOK）
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime

from app.database import Base


class UserAIConfig(Base):
    """用戶 AI 配置（一對一）"""
    __tablename__ = "user_ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    provider = Column(String(20), nullable=False)  # gemini / openai / groq
    model = Column(String(60), nullable=False)
    encrypted_api_key = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
