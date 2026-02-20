"""
Stocks router - 支援台股(TW)與美股(US)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models import User, Stock
from app.validators import validate_stock_id, MarketEnum
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
    validate_stock_id(stock_id)
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
    validate_stock_id(stock_id)
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
    days: int = Query(60, ge=1, le=365),
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
    validate_stock_id(stock_id)
    if period not in ["day", "week", "month"]:
        period = "day"
    history = stock_service.get_history(db, stock_id, days, period=period, market=market)
    return history


@router.get("/{stock_id}/news")
def get_stock_news(
    stock_id: str,
    market: str = Query("TW", description="Market region: TW or US"),
    limit: int = Query(10, ge=1, le=50, description="Number of news items"),
    current_user: User = Depends(get_current_user),
):
    """
    取得股票新聞

    Args:
        stock_id: 股票代碼
        market: 市場 - "TW"(台股) 或 "US"(美股)
        limit: 新聞數量
    """
    validate_stock_id(stock_id)
    news = stock_service.get_news(stock_id, market=market, limit=limit)
    return news


def _get_history_dataframe(stock_id: str, db: Session, days: int = 120, market: str = "TW") -> pd.DataFrame:
    """取得歷史數據並轉換為 DataFrame"""
    validate_stock_id(stock_id)
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


@router.get("/{stock_id}/risk")
def get_stock_risk(
    stock_id: str,
    days: int = Query(252, description="計算天數（預設一年252交易日）"),
    market: str = Query("TW", description="Market region: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得股票風險指標

    回傳：Beta、波動度、VaR、最大回撤
    """
    import numpy as np

    df = _get_history_dataframe(stock_id, db, days + 30, market=market)
    if df.empty or len(df) < 30:
        raise HTTPException(status_code=404, detail="Insufficient history data for risk calculation")

    closes = df['close'].values.astype(float)

    # 日報酬率
    returns = np.diff(closes) / closes[:-1]

    # 波動度（年化標準差）
    daily_volatility = float(np.std(returns))
    annual_volatility = daily_volatility * np.sqrt(252)

    # VaR (Value at Risk) - 95% 信心水準
    var_95 = float(np.percentile(returns, 5))
    var_99 = float(np.percentile(returns, 1))

    # 最大回撤 (Maximum Drawdown)
    peak = closes[0]
    max_drawdown = 0.0
    for price in closes:
        if price > peak:
            peak = price
        drawdown = (peak - price) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Beta — 需要大盤指數
    beta = None
    benchmark_id = "^TWII" if market == "TW" else "^GSPC"
    try:
        benchmark_df = _get_history_dataframe(benchmark_id, db, days + 30, market=market)
        if not benchmark_df.empty and len(benchmark_df) >= 30:
            bench_closes = benchmark_df['close'].values.astype(float)
            # 對齊長度
            min_len = min(len(closes), len(bench_closes))
            stock_rets = np.diff(closes[-min_len:]) / closes[-min_len:-1]
            bench_rets = np.diff(bench_closes[-min_len:]) / bench_closes[-min_len:-1]

            if len(stock_rets) == len(bench_rets) and len(stock_rets) > 1:
                covariance = np.cov(stock_rets, bench_rets)[0][1]
                bench_variance = np.var(bench_rets)
                if bench_variance > 0:
                    beta = float(covariance / bench_variance)
    except Exception as e:
        logger.warning(f"Beta calculation failed for {stock_id}: {e}")

    # 夏普比率（假設無風險利率 2%）
    risk_free_rate = 0.02
    avg_annual_return = float(np.mean(returns)) * 252
    sharpe_ratio = None
    if annual_volatility > 0:
        sharpe_ratio = round((avg_annual_return - risk_free_rate) / annual_volatility, 3)

    return {
        "stock_id": stock_id,
        "market": market,
        "data_days": len(df),
        "beta": round(beta, 3) if beta is not None else None,
        "annual_volatility": round(annual_volatility * 100, 2),
        "daily_volatility": round(daily_volatility * 100, 2),
        "var_95": round(var_95 * 100, 2),
        "var_99": round(var_99 * 100, 2),
        "max_drawdown": round(max_drawdown * 100, 2),
        "sharpe_ratio": sharpe_ratio,
        "risk_level": _classify_risk_level(annual_volatility, max_drawdown, beta),
    }


def _classify_risk_level(volatility: float, max_drawdown: float, beta: float = None) -> str:
    """根據風險指標分類風險等級"""
    score = 0
    # 波動度評分
    if volatility > 0.5:
        score += 3
    elif volatility > 0.3:
        score += 2
    elif volatility > 0.15:
        score += 1

    # 最大回撤評分
    if max_drawdown > 0.4:
        score += 3
    elif max_drawdown > 0.2:
        score += 2
    elif max_drawdown > 0.1:
        score += 1

    # Beta 評分
    if beta is not None:
        if abs(beta) > 1.5:
            score += 2
        elif abs(beta) > 1.0:
            score += 1

    if score >= 6:
        return "極高"
    elif score >= 4:
        return "高"
    elif score >= 2:
        return "中"
    else:
        return "低"


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
