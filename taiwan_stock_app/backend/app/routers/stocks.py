"""
Stocks router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import pandas as pd

from app.database import get_db
from app.models import User, Stock
from app.schemas import (
    StockDetail, StockPrice, StockHistory,
    RSIResponse, MACDResponse, BollingerResponse, KDResponse,
    AllIndicatorsResponse, IndicatorDataPoint, MACDDataPoint,
    BollingerDataPoint, KDDataPoint
)
from app.services import StockDataService
from app.services.technical_indicators import TechnicalIndicators
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/stocks", tags=["stocks"])
stock_service = StockDataService()


@router.get("/search", response_model=List[StockDetail])
def search_stocks(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """搜尋股票"""
    stocks = stock_service.search_stocks(db, q)
    return stocks


@router.get("/{stock_id}", response_model=StockDetail)
def get_stock_detail(
    stock_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得股票詳情"""
    stock = stock_service.get_stock(db, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@router.get("/{stock_id}/price", response_model=StockPrice)
def get_stock_price(
    stock_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得即時報價"""
    price_data = stock_service.get_realtime_price(stock_id)
    if not price_data:
        raise HTTPException(status_code=404, detail="Price data not available")

    # Get stock name
    stock = stock_service.get_stock(db, stock_id)
    if stock:
        price_data["name"] = stock.name

    return price_data


@router.get("/{stock_id}/history", response_model=List[StockHistory])
def get_stock_history(
    stock_id: str,
    days: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得歷史K線"""
    history = stock_service.get_history(db, stock_id, days)
    return history


def _get_history_dataframe(stock_id: str, db: Session, days: int = 120) -> pd.DataFrame:
    """取得歷史數據並轉換為 DataFrame"""
    history = stock_service.get_history(db, stock_id, days)
    if not history:
        return pd.DataFrame()

    df = pd.DataFrame([{
        'date': h['date'],
        'open': float(h['open']),
        'high': float(h['high']),
        'low': float(h['low']),
        'close': float(h['close']),
        'volume': int(h['volume']),
    } for h in history])

    df = df.sort_values('date').reset_index(drop=True)
    return df


@router.get("/{stock_id}/indicators/rsi", response_model=RSIResponse)
def get_rsi(
    stock_id: str,
    period: int = 14,
    days: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得 RSI 指標數據"""
    df = _get_history_dataframe(stock_id, db, days + 30)
    if df.empty:
        raise HTTPException(status_code=404, detail="No history data")

    rsi = TechnicalIndicators.calculate_rsi(df['close'], period)

    data = []
    for i in range(len(df)):
        if i >= len(df) - days:
            val = rsi.iloc[i]
            data.append(IndicatorDataPoint(
                date=df['date'].iloc[i],
                value=float(val) if pd.notna(val) else None
            ))

    return RSIResponse(stock_id=stock_id, period=period, data=data)


@router.get("/{stock_id}/indicators/macd", response_model=MACDResponse)
def get_macd(
    stock_id: str,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
    days: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得 MACD 指標數據"""
    df = _get_history_dataframe(stock_id, db, days + 50)
    if df.empty:
        raise HTTPException(status_code=404, detail="No history data")

    macd_data = TechnicalIndicators.calculate_macd(df['close'], fast, slow, signal_period)

    data = []
    for i in range(len(df)):
        if i >= len(df) - days:
            data.append(MACDDataPoint(
                date=df['date'].iloc[i],
                macd=float(macd_data['macd'].iloc[i]) if pd.notna(macd_data['macd'].iloc[i]) else None,
                signal=float(macd_data['signal'].iloc[i]) if pd.notna(macd_data['signal'].iloc[i]) else None,
                histogram=float(macd_data['histogram'].iloc[i]) if pd.notna(macd_data['histogram'].iloc[i]) else None,
            ))

    return MACDResponse(
        stock_id=stock_id,
        fast=fast,
        slow=slow,
        signal_period=signal_period,
        data=data
    )


@router.get("/{stock_id}/indicators/bollinger", response_model=BollingerResponse)
def get_bollinger(
    stock_id: str,
    period: int = 20,
    std_dev: float = 2.0,
    days: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得布林通道數據"""
    df = _get_history_dataframe(stock_id, db, days + 30)
    if df.empty:
        raise HTTPException(status_code=404, detail="No history data")

    bb_data = TechnicalIndicators.calculate_bollinger_bands(df['close'], period, std_dev)

    data = []
    for i in range(len(df)):
        if i >= len(df) - days:
            data.append(BollingerDataPoint(
                date=df['date'].iloc[i],
                upper=float(bb_data['upper'].iloc[i]) if pd.notna(bb_data['upper'].iloc[i]) else None,
                middle=float(bb_data['middle'].iloc[i]) if pd.notna(bb_data['middle'].iloc[i]) else None,
                lower=float(bb_data['lower'].iloc[i]) if pd.notna(bb_data['lower'].iloc[i]) else None,
                close=float(df['close'].iloc[i]),
            ))

    return BollingerResponse(
        stock_id=stock_id,
        period=period,
        std_dev=std_dev,
        data=data
    )


@router.get("/{stock_id}/indicators/kd", response_model=KDResponse)
def get_kd(
    stock_id: str,
    period: int = 9,
    days: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得 KD 指標數據"""
    df = _get_history_dataframe(stock_id, db, days + 30)
    if df.empty:
        raise HTTPException(status_code=404, detail="No history data")

    kd_data = TechnicalIndicators.calculate_kd(df['high'], df['low'], df['close'], period)

    data = []
    for i in range(len(df)):
        if i >= len(df) - days:
            data.append(KDDataPoint(
                date=df['date'].iloc[i],
                k=float(kd_data['k'].iloc[i]) if pd.notna(kd_data['k'].iloc[i]) else None,
                d=float(kd_data['d'].iloc[i]) if pd.notna(kd_data['d'].iloc[i]) else None,
            ))

    return KDResponse(stock_id=stock_id, period=period, data=data)


@router.get("/{stock_id}/indicators/all", response_model=AllIndicatorsResponse)
def get_all_indicators(
    stock_id: str,
    days: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得所有技術指標數據"""
    df = _get_history_dataframe(stock_id, db, days + 50)
    if df.empty:
        raise HTTPException(status_code=404, detail="No history data")

    # 計算所有指標
    rsi = TechnicalIndicators.calculate_rsi(df['close'], 14)
    macd_data = TechnicalIndicators.calculate_macd(df['close'])
    bb_data = TechnicalIndicators.calculate_bollinger_bands(df['close'])
    kd_data = TechnicalIndicators.calculate_kd(df['high'], df['low'], df['close'])

    # 組裝響應
    rsi_list = []
    macd_list = []
    bb_list = []
    kd_list = []

    for i in range(len(df)):
        if i >= len(df) - days:
            d = df['date'].iloc[i]

            rsi_list.append(IndicatorDataPoint(
                date=d,
                value=float(rsi.iloc[i]) if pd.notna(rsi.iloc[i]) else None
            ))

            macd_list.append(MACDDataPoint(
                date=d,
                macd=float(macd_data['macd'].iloc[i]) if pd.notna(macd_data['macd'].iloc[i]) else None,
                signal=float(macd_data['signal'].iloc[i]) if pd.notna(macd_data['signal'].iloc[i]) else None,
                histogram=float(macd_data['histogram'].iloc[i]) if pd.notna(macd_data['histogram'].iloc[i]) else None,
            ))

            bb_list.append(BollingerDataPoint(
                date=d,
                upper=float(bb_data['upper'].iloc[i]) if pd.notna(bb_data['upper'].iloc[i]) else None,
                middle=float(bb_data['middle'].iloc[i]) if pd.notna(bb_data['middle'].iloc[i]) else None,
                lower=float(bb_data['lower'].iloc[i]) if pd.notna(bb_data['lower'].iloc[i]) else None,
                close=float(df['close'].iloc[i]),
            ))

            kd_list.append(KDDataPoint(
                date=d,
                k=float(kd_data['k'].iloc[i]) if pd.notna(kd_data['k'].iloc[i]) else None,
                d=float(kd_data['d'].iloc[i]) if pd.notna(kd_data['d'].iloc[i]) else None,
            ))

    # 取得最新指標值
    latest = TechnicalIndicators.get_latest_indicators(df)

    return AllIndicatorsResponse(
        stock_id=stock_id,
        latest=latest,
        rsi=rsi_list,
        macd=macd_list,
        bollinger=bb_list,
        kd=kd_list
    )
