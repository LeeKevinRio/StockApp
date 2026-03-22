"""
加密貨幣市場服務 - CoinGecko API 整合
支援 BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK, UNI 等
提供價格、K線、市場概覽、AI 分析、與股票相關性分析
"""

import aiohttp
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)

# CoinGecko API 基礎 URL（免費 API，無需金鑰）
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
ALTERNATIVE_ME_URL = "https://api.alternative.me/fng/"

# 支援的加密貨幣 ID 對應表（CoinGecko ID -> 顯示符號）
CRYPTO_ID_MAP = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "cardano": "ADA",
    "dogecoin": "DOGE",
    "avalanche-2": "AVAX",
    "polkadot": "DOT",
    "matic-network": "MATIC",
    "chainlink": "LINK",
    "uniswap": "UNI",
    "litecoin": "LTC",
    "cosmos": "ATOM",
    "vechain": "VET",
    "polygon": "MATIC",
}

# 反向對應表（符號 -> CoinGecko ID）
SYMBOL_TO_ID = {v: k for k, v in CRYPTO_ID_MAP.items()}


@dataclass
class CryptoPrice:
    """加密貨幣價格數據"""
    symbol: str
    name: str
    price: float
    price_change_24h: float
    price_change_7d: float
    market_cap: Optional[float]
    volume_24h: Optional[float]
    market_cap_rank: Optional[int]
    timestamp: datetime


@dataclass
class CryptoOHLC:
    """K線數據"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float]


class TTLCache:
    """簡易 TTL 快取"""

    def __init__(self):
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        """取得快取資料，若已過期則回傳 None"""
        if key in self._store:
            expire_time, data = self._store[key]
            if time.time() < expire_time:
                logger.debug(f"快取命中: {key}")
                return data
            del self._store[key]
            logger.debug(f"快取已過期: {key}")
        return None

    def set(self, key: str, data: Any, ttl_seconds: int):
        """寫入快取，設定 TTL（秒）"""
        self._store[key] = (time.time() + ttl_seconds, data)
        logger.debug(f"快取已寫入: {key}, TTL={ttl_seconds}s")

    def clear(self):
        """清除所有快取"""
        self._store.clear()


class CryptoMarketService:
    """加密貨幣市場服務"""

    def __init__(self):
        self._cache = TTLCache()
        self._session: Optional[aiohttp.ClientSession] = None
        # 快取 TTL 設定（秒）
        self.PRICE_CACHE_TTL = 120  # 2 分鐘
        self.MARKET_CACHE_TTL = 300  # 5 分鐘
        self.OHLC_CACHE_TTL = 600  # 10 分鐘

    async def _get_session(self) -> aiohttp.ClientSession:
        """取得或建立 aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _fetch_json(self, url: str, params: Dict = None) -> Optional[Dict]:
        """發送 HTTP GET 請求並解析 JSON"""
        try:
            session = await self._get_session()
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.warning(f"HTTP {resp.status}: {url}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"請求超時: {url}")
            return None
        except Exception as e:
            logger.error(f"HTTP 請求失敗: {url}, 錯誤: {e}")
            return None

    def _get_coingecko_id(self, symbol: str) -> Optional[str]:
        """轉換符號為 CoinGecko ID"""
        symbol_upper = symbol.upper()
        return SYMBOL_TO_ID.get(symbol_upper)

    # ==================== 價格數據 ====================

    async def get_crypto_prices(
        self,
        symbols: List[str],
        vs_currency: str = "usd"
    ) -> Dict[str, CryptoPrice]:
        """
        取得加密貨幣當前價格

        Args:
            symbols: 加密貨幣符號列表 (e.g., ["BTC", "ETH", "SOL"])
            vs_currency: 兌換幣種 (預設: "usd", 可用 "twd")

        Returns:
            Dict[symbol] -> CryptoPrice
        """
        cache_key = f"prices:{','.join(sorted(symbols))}:{vs_currency}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        # 轉換符號為 CoinGecko ID
        ids = []
        symbol_to_id_map = {}
        for symbol in symbols:
            cg_id = self._get_coingecko_id(symbol)
            if cg_id:
                ids.append(cg_id)
                symbol_to_id_map[cg_id] = symbol
            else:
                logger.warning(f"未知的加密貨幣符號: {symbol}")

        if not ids:
            return {}

        # 調用 CoinGecko API
        url = f"{COINGECKO_BASE_URL}/simple/price"
        params = {
            "ids": ",".join(ids),
            "vs_currencies": vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_7d_change": "true",
            "include_market_cap_rank": "true",
        }

        data = await self._fetch_json(url, params)
        if not data:
            logger.error("無法取得加密貨幣價格")
            return {}

        result = {}
        now = datetime.utcnow()

        for cg_id, price_data in data.items():
            symbol = symbol_to_id_map.get(cg_id, cg_id.upper())
            price = price_data.get(vs_currency, 0)
            change_24h = price_data.get(f"{vs_currency}_24h_change", 0)
            change_7d = price_data.get(f"{vs_currency}_7d_change", 0)
            market_cap = price_data.get(f"{vs_currency}_market_cap")
            volume_24h = price_data.get(f"{vs_currency}_24h_vol")
            market_cap_rank = price_data.get("market_cap_rank")

            result[symbol] = CryptoPrice(
                symbol=symbol,
                name=cg_id.upper(),
                price=float(price),
                price_change_24h=float(change_24h),
                price_change_7d=float(change_7d),
                market_cap=float(market_cap) if market_cap else None,
                volume_24h=float(volume_24h) if volume_24h else None,
                market_cap_rank=market_cap_rank,
                timestamp=now,
            )

        # 快取結果
        self._cache.set(cache_key, result, self.PRICE_CACHE_TTL)
        return result

    # ==================== K 線數據 ====================

    async def get_crypto_ohlc(
        self,
        symbol: str,
        days: int = 30
    ) -> List[CryptoOHLC]:
        """
        取得加密貨幣 OHLC (K線) 數據用於圖表

        Args:
            symbol: 加密貨幣符號 (e.g., "BTC")
            days: 時間範圍 (1, 7, 30, 90, 365)

        Returns:
            List[CryptoOHLC] - K線數據列表
        """
        cg_id = self._get_coingecko_id(symbol)
        if not cg_id:
            logger.warning(f"未知的加密貨幣符號: {symbol}")
            return []

        cache_key = f"ohlc:{cg_id}:{days}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        # CoinGecko OHLC 端點
        url = f"{COINGECKO_BASE_URL}/coins/{cg_id}/ohlc"
        params = {
            "vs_currency": "usd",
            "days": days,
        }

        data = await self._fetch_json(url, params)
        if not data or not isinstance(data, list):
            logger.error(f"無法取得 OHLC 數據: {symbol}")
            return []

        result = []
        for candle in data:
            if len(candle) >= 5:
                try:
                    result.append(CryptoOHLC(
                        timestamp=datetime.fromtimestamp(candle[0] / 1000),
                        open=float(candle[1]),
                        high=float(candle[2]),
                        low=float(candle[3]),
                        close=float(candle[4]),
                        volume=None,  # CoinGecko OHLC 不含成交量
                    ))
                except (ValueError, IndexError) as e:
                    logger.warning(f"OHLC 數據解析失敗: {e}")
                    continue

        self._cache.set(cache_key, result, self.OHLC_CACHE_TTL)
        return result

    async def get_crypto_history(
        self,
        symbol: str,
        days: int = 30
    ) -> List[Tuple[datetime, float]]:
        """
        取得加密貨幣歷史價格數據（用於折線圖）

        Args:
            symbol: 加密貨幣符號 (e.g., "BTC")
            days: 時間範圍

        Returns:
            List[(datetime, price)]
        """
        cg_id = self._get_coingecko_id(symbol)
        if not cg_id:
            return []

        cache_key = f"history:{cg_id}:{days}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        # CoinGecko 市場圖表數據
        url = f"{COINGECKO_BASE_URL}/coins/{cg_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": "daily" if days > 7 else None,
        }
        # 移除 None 值
        params = {k: v for k, v in params.items() if v is not None}

        data = await self._fetch_json(url, params)
        if not data or "prices" not in data:
            logger.error(f"無法取得歷史價格: {symbol}")
            return []

        result = []
        for timestamp_ms, price in data["prices"]:
            try:
                dt = datetime.fromtimestamp(timestamp_ms / 1000)
                result.append((dt, float(price)))
            except (ValueError, TypeError) as e:
                logger.warning(f"歷史價格解析失敗: {e}")
                continue

        self._cache.set(cache_key, result, self.OHLC_CACHE_TTL)
        return result

    # ==================== 市場概覽 ====================

    async def get_market_overview(self) -> Dict[str, Any]:
        """
        取得加密貨幣市場概覽（市值、BTC 佔比、恐懼指數、漲跌家數）

        Returns:
            {
                "total_market_cap": float,
                "btc_dominance": float,
                "fear_greed_index": {
                    "value": int (0-100),
                    "classification": str,
                    "timestamp": datetime
                },
                "top_gainers": List[{symbol, price_change_24h, ...}],
                "top_losers": List[{symbol, price_change_24h, ...}],
            }
        """
        cache_key = "market_overview"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        result = {
            "total_market_cap": None,
            "btc_dominance": None,
            "fear_greed_index": None,
            "top_gainers": [],
            "top_losers": [],
        }

        # 1. 取得全球數據
        try:
            global_data = await self._fetch_json(f"{COINGECKO_BASE_URL}/global")
            if global_data:
                result["total_market_cap"] = global_data.get("total_market_cap", {}).get("usd")
                result["btc_dominance"] = global_data.get("btc_dominance", {}).get("usd")
        except Exception as e:
            logger.error(f"無法取得全球市場數據: {e}")

        # 2. 取得恐懼指數
        try:
            fng_data = await self._fetch_json(ALTERNATIVE_ME_URL)
            if fng_data and "data" in fng_data:
                latest_fng = fng_data["data"][0]
                result["fear_greed_index"] = {
                    "value": int(latest_fng.get("value", 0)),
                    "classification": latest_fng.get("value_classification", "neutral"),
                    "timestamp": datetime.fromtimestamp(int(latest_fng.get("timestamp", 0))),
                }
        except Exception as e:
            logger.error(f"無法取得恐懼指數: {e}")

        # 3. 取得漲跌榜單
        try:
            # 取得前 250 個加密貨幣的價格變化
            top_cryptos = await self._fetch_json(
                f"{COINGECKO_BASE_URL}/coins/markets",
                {
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 250,
                    "page": 1,
                    "include_market_cap": "false",
                    "include_24hr_vol": "false",
                    "include_24hr_change": "true",
                }
            )

            if top_cryptos:
                # 依 24h 變化排序
                sorted_cryptos = sorted(
                    top_cryptos,
                    key=lambda x: x.get("price_change_percentage_24h", 0) or 0,
                    reverse=True
                )

                # 前 5 大漲家
                result["top_gainers"] = [
                    {
                        "symbol": CRYPTO_ID_MAP.get(c["id"], c["symbol"].upper()),
                        "name": c["name"],
                        "price": c.get("current_price"),
                        "price_change_24h": c.get("price_change_percentage_24h"),
                    }
                    for c in sorted_cryptos[:5]
                ]

                # 前 5 大跌家
                result["top_losers"] = [
                    {
                        "symbol": CRYPTO_ID_MAP.get(c["id"], c["symbol"].upper()),
                        "name": c["name"],
                        "price": c.get("current_price"),
                        "price_change_24h": c.get("price_change_percentage_24h"),
                    }
                    for c in sorted_cryptos[-5:][::-1]
                ]
        except Exception as e:
            logger.error(f"無法取得漲跌榜: {e}")

        self._cache.set(cache_key, result, self.MARKET_CACHE_TTL)
        return result

    # ==================== AI 分析 ====================

    async def get_ai_crypto_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        使用 AI (Gemini/Groq) 分析加密貨幣
        分析包括：價格趨勢、成交量模式、市場情緒、on-chain 指標

        Args:
            symbol: 加密貨幣符號 (e.g., "BTC")

        Returns:
            {
                "symbol": str,
                "analysis": str,
                "trend": "uptrend" | "downtrend" | "sideways",
                "suggestion": "buy" | "sell" | "hold",
                "confidence": 0-100,
                "timestamp": datetime
            }
        """
        # 取得當前價格與歷史數據
        prices = await self.get_crypto_prices([symbol])
        if symbol not in prices:
            logger.warning(f"無法取得價格數據: {symbol}")
            return None

        price_data = prices[symbol]
        history = await self.get_crypto_history(symbol, days=30)

        if not history:
            logger.warning(f"無法取得歷史數據: {symbol}")
            return None

        # 計算簡單的技術指標
        prices_list = [p for _, p in history]
        avg_price = sum(prices_list) / len(prices_list) if prices_list else 0
        price_momentum = ((prices_list[-1] - prices_list[0]) / prices_list[0] * 100) if prices_list[0] > 0 else 0

        # 構建 AI 提示
        prompt = f"""
分析加密貨幣 {symbol}：

**當前數據：**
- 現價: ${price_data.price:,.2f}
- 24h 變化: {price_data.price_change_24h:.2f}%
- 7d 變化: {price_data.price_change_7d:.2f}%
- 市場佔有率: {price_data.market_cap_rank}

**技術數據：**
- 30 天平均價: ${avg_price:,.2f}
- 30 天動能: {price_momentum:.2f}%
- 成交量 (24h): ${price_data.volume_24h:,.0f if price_data.volume_24h else 'N/A'}

請提供：
1. 價格趨勢分析（上升/下降/整盤）
2. 市場情緒評估
3. 買賣建議（買進/賣出/持有）
4. 信心度（0-100）

以 JSON 格式回應：
{{
    "analysis": "分析文字",
    "trend": "uptrend|downtrend|sideways",
    "suggestion": "buy|sell|hold",
    "confidence": 75
}}
"""

        try:
            from app.services.ai_client_factory import AIClientFactory, AIConfig

            # 使用預設 AI 配置
            config = AIConfig(
                provider=settings.AI_PROVIDER,
                model=settings.AI_MODEL_FREE,
                api_key=settings.GOOGLE_API_KEY,
            )
            ai_client = AIClientFactory.create_client(config)

            response_json = ai_client.generate_json(prompt, temperature=0.3)

            if response_json:
                return {
                    "symbol": symbol,
                    "analysis": response_json.get("analysis", ""),
                    "trend": response_json.get("trend", "sideways"),
                    "suggestion": response_json.get("suggestion", "hold"),
                    "confidence": int(response_json.get("confidence", 50)),
                    "timestamp": datetime.utcnow(),
                }
        except Exception as e:
            logger.error(f"AI 分析失敗: {e}")
            return None

        return None

    # ==================== 相關性分析 ====================

    async def get_crypto_stock_correlation(
        self,
        crypto: str,
        stock_index: str,
        days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        計算加密貨幣與股票指數的相關性

        Args:
            crypto: 加密貨幣符號 (e.g., "BTC")
            stock_index: 股票指數 (e.g., "SP500", "TAIEX", "NASDAQ")
            days: 時間範圍

        Returns:
            {
                "crypto": str,
                "stock_index": str,
                "correlation": float (-1 to 1),
                "interpretation": str,
                "crypto_trend": float (變化百分比),
                "stock_trend": float (變化百分比),
                "days": int,
                "timestamp": datetime
            }
        """
        cache_key = f"correlation:{crypto}:{stock_index}:{days}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        # 取得加密貨幣歷史數據
        crypto_history = await self.get_crypto_history(crypto, days)
        if not crypto_history:
            logger.warning(f"無法取得加密貨幣歷史數據: {crypto}")
            return None

        # 取得股票指數歷史數據（簡化版本 - 實際應從股票服務獲取）
        stock_prices = await self._get_stock_index_prices(stock_index, days)
        if not stock_prices:
            logger.warning(f"無法取得股票指數數據: {stock_index}")
            return None

        # 計算相關性
        try:
            import statistics

            # 提取對應時期的收益率
            crypto_returns = self._calculate_returns([p for _, p in crypto_history])
            stock_returns = self._calculate_returns(stock_prices)

            # 確保長度一致
            min_len = min(len(crypto_returns), len(stock_returns))
            crypto_returns = crypto_returns[:min_len]
            stock_returns = stock_returns[:min_len]

            if not crypto_returns or not stock_returns:
                return None

            # 計算 Pearson 相關係數
            correlation = self._pearson_correlation(crypto_returns, stock_returns)

            # 計算趨勢
            crypto_prices = [p for _, p in crypto_history]
            crypto_trend = ((crypto_prices[-1] - crypto_prices[0]) / crypto_prices[0] * 100)
            stock_trend = ((stock_prices[-1] - stock_prices[0]) / stock_prices[0] * 100)

            # 解釋相關性
            if correlation > 0.7:
                interpretation = "強正相關 - 加密貨幣與股票同向波動"
            elif correlation > 0.3:
                interpretation = "中度正相關 - 加密貨幣與股票有關聯"
            elif correlation > -0.3:
                interpretation = "弱相關 - 走勢相對獨立"
            elif correlation > -0.7:
                interpretation = "中度負相關 - 加密貨幣與股票反向波動"
            else:
                interpretation = "強負相關 - 加密貨幣與股票強烈反向波動"

            result = {
                "crypto": crypto,
                "stock_index": stock_index,
                "correlation": round(correlation, 3),
                "interpretation": interpretation,
                "crypto_trend": round(crypto_trend, 2),
                "stock_trend": round(stock_trend, 2),
                "days": days,
                "timestamp": datetime.utcnow(),
            }

            self._cache.set(cache_key, result, self.MARKET_CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"相關性計算失敗: {e}")
            return None

    async def _get_stock_index_prices(
        self,
        index: str,
        days: int
    ) -> Optional[List[float]]:
        """
        取得股票指數的歷史價格（簡化版本）
        實際應與股票數據服務整合
        """
        # 這是一個佔位實現 - 實際應從 FinMind 等資料來源取得
        # 例如：S&P500 (^GSPC), TAIEX (^TWII), NASDAQ (^IXIC)
        try:
            from app.data_fetchers import USStockFetcher, FinMindFetcher

            if index in ["SP500", "^GSPC"]:
                fetcher = USStockFetcher()
                # 簡化版本 - 實際應調用正確的方法
                logger.warning(f"股票指數數據取得未實現: {index}")
                return None
            elif index in ["TAIEX", "^TWII"]:
                fetcher = FinMindFetcher(settings.FINMIND_TOKEN)
                logger.warning(f"股票指數數據取得未實現: {index}")
                return None
            else:
                logger.warning(f"未知的股票指數: {index}")
                return None
        except Exception as e:
            logger.error(f"無法取得股票指數數據: {e}")
            return None

    def _calculate_returns(self, prices: List[float]) -> List[float]:
        """計算日收益率"""
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
        return returns

    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """計算 Pearson 相關係數"""
        if not x or not y or len(x) != len(y):
            return 0.0

        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
        denominator = (
            sum((x[i] - mean_x) ** 2 for i in range(len(x))) *
            sum((y[i] - mean_y) ** 2 for i in range(len(y)))
        ) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator

    # ==================== 監控列表 ====================

    async def get_watchlist_prices(
        self,
        watchlist: List[str],
        vs_currency: str = "usd"
    ) -> Dict[str, CryptoPrice]:
        """
        取得使用者監控列表中的加密貨幣價格

        Args:
            watchlist: 加密貨幣符號列表
            vs_currency: 兌換幣種

        Returns:
            Dict[symbol] -> CryptoPrice
        """
        return await self.get_crypto_prices(watchlist, vs_currency)

    # ==================== 清理資源 ====================

    async def close(self):
        """關閉 aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    def clear_cache(self):
        """清除所有快取"""
        self._cache.clear()


# 全域服務實例
_crypto_market_service: Optional[CryptoMarketService] = None


def get_crypto_market_service() -> CryptoMarketService:
    """取得全域 CryptoMarketService 實例"""
    global _crypto_market_service
    if _crypto_market_service is None:
        _crypto_market_service = CryptoMarketService()
    return _crypto_market_service


# 便捷別名
crypto_market_service = get_crypto_market_service()
