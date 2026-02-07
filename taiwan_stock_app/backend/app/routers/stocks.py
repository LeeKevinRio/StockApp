"""
Stocks router - 支援台股(TW)與美股(US)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd

from app.database import get_db
from app.models import User, Stock
from app.schemas import (
    StockDetail, StockPrice, StockHistory,
    RSIResponse, MACDResponse, BollingerResponse, KDResponse,
    AllIndicatorsResponse, IndicatorDataPoint, MACDDataPoint,
    BollingerDataPoint, KDDataPoint,
    PatternResponse, PatternItem, PatternType, PatternSignal,
)
from app.services import StockDataService
from app.services.technical_indicators import TechnicalIndicators
from app.services.pattern_recognition import PatternRecognitionService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/stocks", tags=["stocks"])
stock_service = StockDataService()
pattern_service = PatternRecognitionService()


@router.get("/search")
def search_stocks(
    q: str,
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    搜尋股票

    Args:
        q: 搜尋關鍵字
        market: 市場 - "TW"(台股) 或 "US"(美股)
    """
    stocks = stock_service.search_stocks(db, q, market=market)

    # For US stocks, return the dict list directly
    if market == "US":
        return stocks

    # For TW stocks, convert to response format
    return [
        {
            "stock_id": s.stock_id,
            "name": s.name,
            "english_name": s.english_name,
            "industry": s.industry,
            "market": s.market,
            "market_region": getattr(s, 'market_region', 'TW'),
        }
        for s in stocks
    ]


@router.get("/debug/us-test")
def debug_us_stock_test():
    """
    Debug endpoint to test US stock fetcher (no auth required)
    """
    from app.data_fetchers.us_stock_fetcher import USStockFetcher
    fetcher = USStockFetcher()

    result = {
        "yfinance_available": False,
        "search_result": None,
        "quote_result": None,
        "error": None
    }

    try:
        import yfinance as yf
        result["yfinance_available"] = True
        result["yfinance_version"] = yf.__version__
    except ImportError as e:
        result["error"] = f"yfinance import error: {str(e)}"
        return result

    try:
        # Test search
        search_results = fetcher.search_stocks("AAPL")
        result["search_result"] = search_results[:3] if search_results else []
    except Exception as e:
        result["search_error"] = str(e)

    try:
        # Test quote
        quote = fetcher.get_realtime_quote("AAPL")
        result["quote_result"] = quote
    except Exception as e:
        result["quote_error"] = str(e)

    return result


@router.get("/{stock_id}")
def get_stock_detail(
    stock_id: str,
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得股票詳情

    Args:
        stock_id: 股票代碼
        market: 市場 - "TW"(台股) 或 "US"(美股)
    """
    stock = stock_service.get_stock(db, stock_id, market=market)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@router.get("/{stock_id}/price")
def get_stock_price(
    stock_id: str,
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得即時報價

    Args:
        stock_id: 股票代碼
        market: 市場 - "TW"(台股) 或 "US"(美股)
    """
    price_data = stock_service.get_realtime_price(stock_id, market=market)
    if not price_data:
        raise HTTPException(status_code=404, detail="Price data not available")

    # Get stock name if not present
    if not price_data.get("name"):
        stock = stock_service.get_stock(db, stock_id, market=market)
        if stock:
            price_data["name"] = stock.get("name", "") if isinstance(stock, dict) else stock.name

    return price_data


@router.get("/{stock_id}/history")
def get_stock_history(
    stock_id: str,
    days: int = 60,
    period: str = "day",
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得歷史K線

    Args:
        stock_id: 股票代碼
        days: 返回筆數
        period: 週期 - "day"(日K), "week"(週K), "month"(月K)
        market: 市場 - "TW"(台股) 或 "US"(美股)
    """
    if period not in ["day", "week", "month"]:
        period = "day"
    history = stock_service.get_history(db, stock_id, days, period=period, market=market)
    return history


@router.get("/{stock_id}/news")
def get_stock_news(
    stock_id: str,
    market: str = Query("TW", description="Market region: TW or US"),
    limit: int = Query(10, description="Number of news items"),
    current_user: User = Depends(get_current_user),
):
    """
    取得股票新聞

    Args:
        stock_id: 股票代碼
        market: 市場 - "TW"(台股) 或 "US"(美股)
        limit: 新聞數量
    """
    news = stock_service.get_news(stock_id, market=market, limit=limit)
    return news


def _get_history_dataframe(stock_id: str, db: Session, days: int = 120, market: str = "TW") -> pd.DataFrame:
    """取得歷史數據並轉換為 DataFrame"""
    history = stock_service.get_history(db, stock_id, days, market=market)
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
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得 RSI 指標數據"""
    df = _get_history_dataframe(stock_id, db, days + 30, market=market)
    if df.empty:
        raise HTTPException(status_code=404, detail="No history data")

    rsi = TechnicalIndicators.calculate_rsi(df['close'], period)

    data = []
    for i in range(len(df)):
        if i >= len(df) - days:
            val = rsi.iloc[i]
            data.append(IndicatorDataPoint(
                date=df['date'].iloc[i],
                value=float(val) if pd.notna(val) else None,
                close=float(df['close'].iloc[i])
            ))

    return RSIResponse(stock_id=stock_id, period=period, data=data)


@router.get("/{stock_id}/indicators/macd", response_model=MACDResponse)
def get_macd(
    stock_id: str,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
    days: int = 60,
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得 MACD 指標數據"""
    df = _get_history_dataframe(stock_id, db, days + 50, market=market)
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
                close=float(df['close'].iloc[i])
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
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得布林通道數據"""
    df = _get_history_dataframe(stock_id, db, days + 30, market=market)
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
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得 KD 指標數據"""
    df = _get_history_dataframe(stock_id, db, days + 30, market=market)
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
                close=float(df['close'].iloc[i])
            ))

    return KDResponse(stock_id=stock_id, period=period, data=data)


@router.get("/{stock_id}/indicators/all", response_model=AllIndicatorsResponse)
def get_all_indicators(
    stock_id: str,
    days: int = 60,
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得所有技術指標數據"""
    df = _get_history_dataframe(stock_id, db, days + 50, market=market)
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
            close_price = float(df['close'].iloc[i])

            rsi_list.append(IndicatorDataPoint(
                date=d,
                value=float(rsi.iloc[i]) if pd.notna(rsi.iloc[i]) else None,
                close=close_price
            ))

            macd_list.append(MACDDataPoint(
                date=d,
                macd=float(macd_data['macd'].iloc[i]) if pd.notna(macd_data['macd'].iloc[i]) else None,
                signal=float(macd_data['signal'].iloc[i]) if pd.notna(macd_data['signal'].iloc[i]) else None,
                histogram=float(macd_data['histogram'].iloc[i]) if pd.notna(macd_data['histogram'].iloc[i]) else None,
                close=close_price
            ))

            bb_list.append(BollingerDataPoint(
                date=d,
                upper=float(bb_data['upper'].iloc[i]) if pd.notna(bb_data['upper'].iloc[i]) else None,
                middle=float(bb_data['middle'].iloc[i]) if pd.notna(bb_data['middle'].iloc[i]) else None,
                lower=float(bb_data['lower'].iloc[i]) if pd.notna(bb_data['lower'].iloc[i]) else None,
                close=close_price,
            ))

            kd_list.append(KDDataPoint(
                date=d,
                k=float(kd_data['k'].iloc[i]) if pd.notna(kd_data['k'].iloc[i]) else None,
                d=float(kd_data['d'].iloc[i]) if pd.notna(kd_data['d'].iloc[i]) else None,
                close=close_price
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


@router.get("/{stock_id}/patterns", response_model=PatternResponse)
def get_stock_patterns(
    stock_id: str,
    lookback: int = Query(60, description="回顧天數"),
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得股票形態識別結果

    識別常見的技術分析形態包括：
    - 頭肩頂/頭肩底 (Head and Shoulders)
    - 雙頂/雙底 (Double Top/Bottom)
    - 三角形整理 (Triangles)
    - 楔形 (Wedges)
    - 旗形 (Flags)
    - 突破信號 (Breakouts)

    Args:
        stock_id: 股票代碼
        lookback: 回顧天數（預設60天）
        market: 市場 - "TW"(台股) 或 "US"(美股)
    """
    # 取得歷史數據
    df = _get_history_dataframe(stock_id, db, lookback + 30, market=market)
    if df.empty:
        raise HTTPException(status_code=404, detail="No history data")

    # 執行形態識別
    detected_patterns = pattern_service.detect_all_patterns(df, lookback=lookback)

    # 轉換為響應格式
    patterns = []
    for p in detected_patterns:
        patterns.append(PatternItem(
            pattern_type=p.pattern_type.value,
            signal=p.signal.value,
            confidence=p.confidence,
            start_index=p.start_index,
            end_index=p.end_index,
            key_prices=p.key_prices,
            target_price=p.target_price,
            stop_loss=p.stop_loss,
            description=p.description,
            is_confirmed=p.is_confirmed,
        ))

    # 計算主導信號
    dominant_signal = None
    if patterns:
        bullish_score = sum(p.confidence for p in patterns if p.signal == "bullish")
        bearish_score = sum(p.confidence for p in patterns if p.signal == "bearish")
        if bullish_score > bearish_score * 1.2:
            dominant_signal = "bullish"
        elif bearish_score > bullish_score * 1.2:
            dominant_signal = "bearish"
        else:
            dominant_signal = "neutral"

    return PatternResponse(
        stock_id=stock_id,
        has_patterns=len(patterns) > 0,
        dominant_signal=dominant_signal,
        patterns=patterns,
    )
