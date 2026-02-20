"""
Broker Account Models — 券商帳戶連動
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from datetime import datetime

from app.database import Base


class BrokerAccount(Base):
    """券商帳戶"""
    __tablename__ = "broker_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    broker_type = Column(String(50), nullable=False, default="firstrade")
    encrypted_credentials = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending_2fa / active / error
    account_number = Column(String(50), nullable=True)
    last_synced = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BrokerPosition(Base):
    """券商持倉"""
    __tablename__ = "broker_positions"

    id = Column(Integer, primary_key=True, index=True)
    broker_account_id = Column(Integer, ForeignKey("broker_accounts.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, default=0)
    avg_cost = Column(Float, default=0)
    market_value = Column(Float, default=0)
    unrealized_pnl = Column(Float, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
