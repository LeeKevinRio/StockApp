"""
技術指標 Schemas
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class IndicatorDataPoint(BaseModel):
    """單一指標數據點"""
    date: date
    value: Optional[float] = None
    close: Optional[float] = None  # 收盤價，用於圖表顯示


class MACDDataPoint(BaseModel):
    """MACD 數據點"""
    date: date
    macd: Optional[float] = None
    signal: Optional[float] = None
    histogram: Optional[float] = None
    close: Optional[float] = None  # 收盤價，用於圖表顯示


class BollingerDataPoint(BaseModel):
    """布林通道數據點"""
    date: date
    upper: Optional[float] = None
    middle: Optional[float] = None
    lower: Optional[float] = None
    close: Optional[float] = None


class KDDataPoint(BaseModel):
    """KD 指標數據點"""
    date: date
    k: Optional[float] = None
    d: Optional[float] = None
    close: Optional[float] = None  # 收盤價，用於圖表顯示


class RSIResponse(BaseModel):
    """RSI 響應"""
    stock_id: str
    period: int
    data: List[IndicatorDataPoint]


class MACDResponse(BaseModel):
    """MACD 響應"""
    stock_id: str
    fast: int
    slow: int
    signal_period: int
    data: List[MACDDataPoint]


class BollingerResponse(BaseModel):
    """布林通道響應"""
    stock_id: str
    period: int
    std_dev: float
    data: List[BollingerDataPoint]


class KDResponse(BaseModel):
    """KD 響應"""
    stock_id: str
    period: int
    data: List[KDDataPoint]


class AllIndicatorsResponse(BaseModel):
    """所有指標響應"""
    stock_id: str
    latest: dict
    rsi: List[IndicatorDataPoint]
    macd: List[MACDDataPoint]
    bollinger: List[BollingerDataPoint]
    kd: List[KDDataPoint]
