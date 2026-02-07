"""
Prediction Record Model - 追蹤 AI 預測準確度
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class PredictionRecord(Base):
    """AI 預測記錄表 - 用於追蹤預測準確度"""
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(100))
    market_region = Column(String(5), default="TW")  # TW or US

    # 預測日期（做出預測的日期）
    prediction_date = Column(Date, nullable=False, index=True)
    # 目標日期（預測的目標日期，即隔天）
    target_date = Column(Date, nullable=False, index=True)

    # 預測內容
    predicted_direction = Column(String(10))  # UP or DOWN
    predicted_change_percent = Column(Numeric(6, 2))  # 預測漲跌幅 %
    predicted_probability = Column(Numeric(4, 2))  # 預測機率
    predicted_price_low = Column(Numeric(12, 2))  # 預測最低價
    predicted_price_high = Column(Numeric(12, 2))  # 預測最高價
    prediction_reasoning = Column(Text)  # 預測依據

    # 預測時的收盤價（用於計算）
    base_close_price = Column(Numeric(12, 2))

    # 實際結果（收盤後更新）
    actual_close_price = Column(Numeric(12, 2))
    actual_change_percent = Column(Numeric(6, 2))  # 實際漲跌幅 %
    actual_direction = Column(String(10))  # UP or DOWN
    actual_high = Column(Numeric(12, 2))
    actual_low = Column(Numeric(12, 2))

    # 評估結果
    direction_correct = Column(Boolean)  # 方向是否正確
    within_range = Column(Boolean)  # 收盤價是否在預測區間內
    error_percent = Column(Numeric(6, 2))  # 預測誤差 %

    # AI 提供者
    ai_provider = Column(String(20))  # Gemini, Groq, Mock

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
