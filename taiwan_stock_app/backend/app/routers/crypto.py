"""
加密貨幣 API 路由
公開加密貨幣市場數據、K線圖、市場概覽、AI 分析與相關性分析的端點
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
import logging
from typing import List, Dict, Optional, Any

from app.models.user import User
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crypto", tags=["crypto"])


# ==================== 端點實現 ====================


@router.get("/prices")
async def get_crypto_prices(
    limit: int = Query(20, ge=1, le=250),
    vs_currency: str = Query("usd", pattern="^[a-z]{3}$"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    取得加密貨幣價格（前 N 個）

    **查詢參數：**
    - limit: 返回數量（預設 20，最多 250）
    - vs_currency: 兌換幣種（預設 usd，支援 twd 等）

    **回應：**
    包含加密貨幣符號、價格、漲跌幅、市值排名等資訊
    """
    try:
        # 延遲導入以避免循環導入
        from app.services.crypto_market_service import get_crypto_market_service

        service = get_crypto_market_service()

        # 預設貨幣清單（按市值排序）
        top_symbols = [
            "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX",
            "DOT", "MATIC", "LINK", "UNI", "LTC", "ATOM", "VET",
            "AAVE", "ALGO", "BCH", "EOS", "FIL"
        ]

        # 限制數量
        symbols_to_fetch = top_symbols[:limit]

        # 取得價格數據
        prices = await service.get_crypto_prices(
            symbols=symbols_to_fetch,
            vs_currency=vs_currency
        )

        if not prices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="無法取得加密貨幣價格數據"
            )

        # 轉換為 JSON 格式
        result = {}
        for symbol, price_obj in prices.items():
            result[symbol] = {
                "symbol": price_obj.symbol,
                "name": price_obj.name,
                "price": price_obj.price,
                "price_change_24h": price_obj.price_change_24h,
                "price_change_7d": price_obj.price_change_7d,
                "market_cap": price_obj.market_cap,
                "volume_24h": price_obj.volume_24h,
                "market_cap_rank": price_obj.market_cap_rank,
                "timestamp": price_obj.timestamp.isoformat(),
            }

        return {
            "status": "success",
            "data": result,
            "count": len(result),
        }

    except Exception as e:
        logger.error(f"獲取加密貨幣價格失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法取得加密貨幣價格"
        )


@router.get("/{symbol}/detail")
async def get_crypto_detail(
    symbol: str,
    vs_currency: str = Query("usd", pattern="^[a-z]{3}$"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    取得指定加密貨幣的詳細資訊

    **路徑參數：**
    - symbol: 加密貨幣符號（如 BTC、ETH）

    **查詢參數：**
    - vs_currency: 兌換幣種（預設 usd）

    **回應：**
    包含當前價格、24/7日漲跌、市值、成交量、排名等詳細資訊
    """
    try:
        symbol_upper = symbol.upper()

        # 延遲導入以避免循環導入
        from app.services.crypto_market_service import get_crypto_market_service

        service = get_crypto_market_service()

        # 取得價格數據
        prices = await service.get_crypto_prices(
            symbols=[symbol_upper],
            vs_currency=vs_currency
        )

        if symbol_upper not in prices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到加密貨幣: {symbol}"
            )

        price_obj = prices[symbol_upper]

        return {
            "status": "success",
            "data": {
                "symbol": price_obj.symbol,
                "name": price_obj.name,
                "price": price_obj.price,
                "price_change_24h": price_obj.price_change_24h,
                "price_change_7d": price_obj.price_change_7d,
                "market_cap": price_obj.market_cap,
                "volume_24h": price_obj.volume_24h,
                "market_cap_rank": price_obj.market_cap_rank,
                "timestamp": price_obj.timestamp.isoformat(),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取加密貨幣詳細資訊失敗: {symbol}, {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"無法取得加密貨幣 {symbol} 的詳細資訊"
        )


@router.get("/{symbol}/kline")
async def get_crypto_kline(
    symbol: str,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    取得加密貨幣 K線/蠟燭線圖數據

    **路徑參數：**
    - symbol: 加密貨幣符號（如 BTC、ETH）

    **查詢參數：**
    - days: 時間範圍天數（預設 30，範圍 1-365）

    **回應：**
    OHLC（開盤價、最高價、最低價、收盤價）數據列表，用於繪製 K線圖
    """
    try:
        symbol_upper = symbol.upper()

        # 延遲導入以避免循環導入
        from app.services.crypto_market_service import get_crypto_market_service

        service = get_crypto_market_service()

        # 取得 OHLC 數據
        ohlc_list = await service.get_crypto_ohlc(
            symbol=symbol_upper,
            days=days
        )

        if not ohlc_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"無法取得 {symbol} 的 K線數據"
            )

        # 轉換為 JSON 格式
        klines = [
            {
                "timestamp": ohlc.timestamp.isoformat(),
                "open": ohlc.open,
                "high": ohlc.high,
                "low": ohlc.low,
                "close": ohlc.close,
                "volume": ohlc.volume,
            }
            for ohlc in ohlc_list
        ]

        return {
            "status": "success",
            "symbol": symbol_upper,
            "days": days,
            "data": klines,
            "count": len(klines),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取 K線數據失敗: {symbol}, {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"無法取得 {symbol} 的 K線數據"
        )


@router.get("/market-overview")
async def get_market_overview(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    取得加密貨幣市場概覽

    **回應包含：**
    - total_market_cap: 全球加密貨幣市值
    - btc_dominance: BTC 市場佔有率
    - fear_greed_index: 恐懼指數（0-100）
    - top_gainers: 漲幅前 5 名
    - top_losers: 跌幅前 5 名
    """
    try:
        # 延遲導入以避免循環導入
        from app.services.crypto_market_service import get_crypto_market_service

        service = get_crypto_market_service()

        # 取得市場概覽
        overview = await service.get_market_overview()

        if not overview:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="無法取得市場概覽數據"
            )

        # 處理恐懼指數的日期時間
        if overview.get("fear_greed_index"):
            fng = overview["fear_greed_index"]
            fng["timestamp"] = fng.get("timestamp", "").isoformat() if hasattr(fng.get("timestamp"), "isoformat") else str(fng.get("timestamp"))

        return {
            "status": "success",
            "data": {
                "total_market_cap": overview.get("total_market_cap"),
                "btc_dominance": overview.get("btc_dominance"),
                "fear_greed_index": overview.get("fear_greed_index"),
                "top_gainers": overview.get("top_gainers", []),
                "top_losers": overview.get("top_losers", []),
            }
        }

    except Exception as e:
        logger.error(f"獲取市場概覽失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法取得市場概覽數據"
        )


@router.get("/{symbol}/ai-analysis")
async def get_crypto_ai_analysis(
    symbol: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    取得加密貨幣 AI 分析

    **路徑參數：**
    - symbol: 加密貨幣符號（如 BTC、ETH）

    **回應包含：**
    - analysis: AI 分析文字
    - trend: 趨勢（uptrend/downtrend/sideways）
    - suggestion: 建議（buy/sell/hold）
    - confidence: 信心度（0-100）
    """
    try:
        symbol_upper = symbol.upper()

        # 延遲導入以避免循環導入
        from app.services.crypto_market_service import get_crypto_market_service

        service = get_crypto_market_service()

        # 取得 AI 分析
        analysis = await service.get_ai_crypto_analysis(symbol=symbol_upper)

        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"無法取得 {symbol} 的 AI 分析"
            )

        return {
            "status": "success",
            "data": {
                "symbol": analysis.get("symbol"),
                "analysis": analysis.get("analysis"),
                "trend": analysis.get("trend"),
                "suggestion": analysis.get("suggestion"),
                "confidence": analysis.get("confidence"),
                "timestamp": analysis.get("timestamp", "").isoformat() if hasattr(analysis.get("timestamp"), "isoformat") else str(analysis.get("timestamp")),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI 分析失敗: {symbol}, {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"無法取得 {symbol} 的 AI 分析"
        )


@router.get("/correlation/{stock_id}")
async def get_crypto_stock_correlation(
    stock_id: str = Path(..., min_length=2, max_length=20),
    crypto: str = Query("BTC", min_length=2, max_length=10),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    取得加密貨幣與股票的相關性分析

    **路徑參數：**
    - stock_id: 股票代碼（如 TAIEX、SP500）

    **查詢參數：**
    - crypto: 加密貨幣符號（預設 BTC）
    - days: 分析時間範圍（預設 30，範圍 1-365）

    **回應包含：**
    - correlation: 相關係數（-1 到 1）
    - interpretation: 相關性解釋
    - crypto_trend: 加密貨幣趨勢（百分比變化）
    - stock_trend: 股票趨勢（百分比變化）
    """
    try:
        crypto_upper = crypto.upper()
        stock_upper = stock_id.upper()

        # 延遲導入以避免循環導入
        from app.services.crypto_market_service import get_crypto_market_service

        service = get_crypto_market_service()

        # 取得相關性分析
        correlation = await service.get_crypto_stock_correlation(
            crypto=crypto_upper,
            stock_index=stock_upper,
            days=days
        )

        if correlation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"無法取得 {crypto} 與 {stock_id} 的相關性數據"
            )

        return {
            "status": "success",
            "data": {
                "crypto": correlation.get("crypto"),
                "stock_index": correlation.get("stock_index"),
                "correlation": correlation.get("correlation"),
                "interpretation": correlation.get("interpretation"),
                "crypto_trend": correlation.get("crypto_trend"),
                "stock_trend": correlation.get("stock_trend"),
                "days": correlation.get("days"),
                "timestamp": correlation.get("timestamp", "").isoformat() if hasattr(correlation.get("timestamp"), "isoformat") else str(correlation.get("timestamp")),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"相關性分析失敗: {crypto}/{stock_id}, {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"無法取得 {crypto} 與 {stock_id} 的相關性數據"
        )
