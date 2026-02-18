"""
Stock Data Service
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
import random
import threading

from app.models import Stock, StockPrice
from app.data_fetchers import FinMindFetcher, FugleFetcher, TWSEFetcher, USStockFetcher, GlobalNewsFetcher
from app.config import settings


class PriceCache:
    """價格緩存，依市場交易時段動態調整 TTL"""

    # 台股交易時間 09:00 ~ 13:30
    TW_MARKET_OPEN_HOUR = 9
    TW_MARKET_OPEN_MINUTE = 0
    TW_MARKET_CLOSE_HOUR = 13
    TW_MARKET_CLOSE_MINUTE = 30

    def __init__(self, ttl_trading: int = 30, ttl_closed: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._ttl_trading = ttl_trading    # 盤中 TTL（秒）
        self._ttl_closed = ttl_closed      # 收盤後 TTL（秒）
        self._last_clear_date: Optional[date] = None

    def _get_ttl(self) -> int:
        """根據台股交易時段回傳適當的 TTL"""
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday

        # 週末直接用長 TTL
        if weekday >= 5:
            return self._ttl_closed

        market_open = now.replace(
            hour=self.TW_MARKET_OPEN_HOUR, minute=self.TW_MARKET_OPEN_MINUTE, second=0
        )
        market_close = now.replace(
            hour=self.TW_MARKET_CLOSE_HOUR, minute=self.TW_MARKET_CLOSE_MINUTE, second=0
        )

        if market_open <= now <= market_close:
            return self._ttl_trading
        return self._ttl_closed

    def _auto_clear_on_new_day(self):
        """每天第一次存取時清除前一天快取，確保開盤拿到最新資料"""
        today = date.today()
        if self._last_clear_date != today:
            self._cache.clear()
            self._last_clear_date = today

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._auto_clear_on_new_day()
            if key in self._cache:
                entry = self._cache[key]
                if datetime.now() < entry["expires_at"]:
                    return entry["data"]
                else:
                    del self._cache[key]
        return None

    def set(self, key: str, data: Dict[str, Any]):
        with self._lock:
            self._auto_clear_on_new_day()
            ttl = self._get_ttl()
            self._cache[key] = {
                "data": data,
                "expires_at": datetime.now() + timedelta(seconds=ttl)
            }

    def get_batch(self, keys: List[str]) -> Dict[str, Dict[str, Any]]:
        result = {}
        with self._lock:
            self._auto_clear_on_new_day()
            now = datetime.now()
            for key in keys:
                if key in self._cache:
                    entry = self._cache[key]
                    if now < entry["expires_at"]:
                        result[key] = entry["data"]
        return result

    def set_batch(self, data: Dict[str, Dict[str, Any]]):
        with self._lock:
            self._auto_clear_on_new_day()
            ttl = self._get_ttl()
            expires_at = datetime.now() + timedelta(seconds=ttl)
            for key, value in data.items():
                self._cache[key] = {"data": value, "expires_at": expires_at}

    def clear(self):
        """手動清除所有快取"""
        with self._lock:
            self._cache.clear()


# 全局價格緩存：盤中 30 秒、收盤後 5 分鐘
_price_cache = PriceCache(ttl_trading=30, ttl_closed=300)

# K 線歷史資料快取：5 分鐘 TTL（歷史數據不常變）
_history_cache: Dict[str, Any] = {}
_history_cache_lock = threading.Lock()
_HISTORY_CACHE_TTL = 300  # 5 分鐘


def _get_history_cache(key: str) -> Optional[List[dict]]:
    """取得 K 線歷史快取"""
    with _history_cache_lock:
        if key in _history_cache:
            data, expires_at = _history_cache[key]
            if datetime.now() < expires_at:
                return data
            del _history_cache[key]
    return None


def _set_history_cache(key: str, data: List[dict]):
    """設定 K 線歷史快取"""
    with _history_cache_lock:
        _history_cache[key] = (data, datetime.now() + timedelta(seconds=_HISTORY_CACHE_TTL))


def generate_mock_stock_history(stock_id: str, days: int = 60) -> List[dict]:
    """Generate mock stock history data for testing"""
    base_price = random.uniform(50, 500)
    result = []
    current_date = date.today() - timedelta(days=days)

    for i in range(days):
        # Skip weekends
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        change = random.uniform(-0.03, 0.03)
        open_price = base_price * (1 + random.uniform(-0.01, 0.01))
        close_price = base_price * (1 + change)
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))

        result.append({
            "date": current_date.isoformat(),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": random.randint(1000000, 50000000),
        })

        base_price = close_price
        current_date += timedelta(days=1)

    return result


def generate_mock_realtime_price(stock_id: str, stock_name: str = "") -> dict:
    """Generate mock realtime price data for testing"""
    base_price = random.uniform(50, 500)
    change = random.uniform(-5, 5)
    change_percent = (change / base_price) * 100

    return {
        "stock_id": stock_id,
        "name": stock_name or stock_id,
        "current_price": Decimal(str(round(base_price, 2))),
        "change": Decimal(str(round(change, 2))),
        "change_percent": Decimal(str(round(change_percent, 2))),
        "open": Decimal(str(round(base_price - random.uniform(-2, 2), 2))),
        "high": Decimal(str(round(base_price + random.uniform(1, 5), 2))),
        "low": Decimal(str(round(base_price - random.uniform(1, 5), 2))),
        "volume": random.randint(1000000, 50000000),
        "market_region": "TW",
        "currency": "TWD",
        "updated_at": datetime.now(),
    }


class StockDataService:
    """股票數據服務 - 支援台股(TW)與美股(US)"""

    def __init__(self):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        self.fugle = FugleFetcher(settings.FUGLE_API_KEY) if settings.FUGLE_API_KEY else None
        self.twse = TWSEFetcher()
        self.us_fetcher = USStockFetcher()
        self.global_news = GlobalNewsFetcher()

    def search_stocks(self, db: Session, query: str, market: str = "TW") -> List:
        """
        搜尋股票

        Args:
            db: Database session
            query: Search query
            market: 'TW' for Taiwan stocks, 'US' for US stocks
        """
        if market == "US":
            # Use US stock fetcher for real-time search
            results = self.us_fetcher.search_stocks(query)
            return results
        else:
            # Search from database for Taiwan stocks
            return (
                db.query(Stock)
                .filter(
                    (Stock.market_region == "TW") &
                    ((Stock.stock_id.like(f"%{query}%"))
                    | (Stock.name.like(f"%{query}%")))
                )
                .limit(20)
                .all()
            )

    def get_stock(self, db: Session, stock_id: str, market: str = "TW") -> Optional[dict]:
        """
        取得股票詳情

        Args:
            db: Database session
            stock_id: Stock ID/Symbol
            market: 'TW' for Taiwan stocks, 'US' for US stocks
        """
        if market == "US":
            return self.us_fetcher.get_stock_info(stock_id)
        else:
            stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
            if stock:
                return {
                    "stock_id": stock.stock_id,
                    "name": stock.name,
                    "english_name": stock.english_name,
                    "industry": stock.industry,
                    "market": stock.market,
                    "market_region": stock.market_region or "TW",
                    "listed_date": stock.listed_date.isoformat() if stock.listed_date else None,
                }
            return None

    def get_realtime_price(self, stock_id: str, market: str = "TW") -> dict:
        """
        取得即時報價

        Args:
            stock_id: Stock ID/Symbol
            market: 'TW' for Taiwan stocks, 'US' for US stocks

        For TW: 優先順序 TWSE → Fugle → FinMind
        For US: Yahoo Finance via yfinance
        """
        if market == "US":
            return self._get_us_realtime_price(stock_id)
        else:
            return self._get_tw_realtime_price(stock_id)

    def _get_us_realtime_price(self, stock_id: str) -> dict:
        """取得美股即時報價"""
        try:
            quote = self.us_fetcher.get_realtime_quote(stock_id)
            if quote:
                return {
                    "stock_id": stock_id,
                    "name": quote.get("name", ""),
                    "current_price": Decimal(str(quote.get("price", 0))),
                    "change": Decimal(str(quote.get("change", 0))),
                    "change_percent": Decimal(str(quote.get("change_percent", 0))),
                    "open": Decimal(str(quote.get("open", 0))),
                    "high": Decimal(str(quote.get("high", 0))),
                    "low": Decimal(str(quote.get("low", 0))),
                    "volume": quote.get("volume", 0),
                    "market_region": "US",
                    "currency": quote.get("currency", "USD"),
                    "updated_at": datetime.now(),
                }
        except Exception as e:
            print(f"US Stock API 失敗: {e}")
        return None

    def _get_tw_realtime_price(self, stock_id: str) -> dict:
        """取得台股即時報價（優先順序：TWSE → Fugle → FinMind）"""

        def _safe_decimal(val, default=0):
            """安全轉換為 Decimal"""
            if val is None or val == '' or val == '-' or val == '--':
                return Decimal(str(default))
            try:
                return Decimal(str(val))
            except Exception:
                return Decimal(str(default))

        # 1. 優先使用 TWSE（免費即時）
        try:
            quote = self.twse.get_realtime_quote(stock_id)
            return {
                "stock_id": stock_id,
                "name": quote.get("name", ""),
                "current_price": _safe_decimal(quote.get("price")),
                "change": _safe_decimal(quote.get("change")),
                "change_percent": _safe_decimal(quote.get("change_percent")),
                "open": _safe_decimal(quote.get("open")),
                "high": _safe_decimal(quote.get("high")),
                "low": _safe_decimal(quote.get("low")),
                "volume": quote.get("volume", 0),
                "market_region": "TW",
                "currency": "TWD",
                "updated_at": datetime.now(),
            }
        except Exception as e:
            print(f"TWSE API 失敗: {e}")

        # 2. 回退到 Fugle（如果有配置）
        if self.fugle:
            try:
                quote = self.fugle.get_realtime_quote(stock_id)
                return {
                    "stock_id": stock_id,
                    "name": quote.get("name", ""),
                    "current_price": Decimal(str(quote.get("price", 0))),
                    "change": Decimal(str(quote.get("change", 0))),
                    "change_percent": Decimal(str(quote.get("change_percent", 0))),
                    "open": Decimal(str(quote.get("open", 0))),
                    "high": Decimal(str(quote.get("high", 0))),
                    "low": Decimal(str(quote.get("low", 0))),
                    "volume": quote.get("volume", 0),
                    "market_region": "TW",
                    "currency": "TWD",
                    "updated_at": datetime.now(),
                }
            except Exception as e:
                print(f"Fugle API 失敗: {e}")

        # 3. 最後使用 FinMind（延遲數據）
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=1)
            prices = self.finmind.get_stock_price(
                stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )
            if len(prices) == 0:
                # Return mock data for testing
                return generate_mock_realtime_price(stock_id)

            latest = prices.iloc[-1]
            prev_close = float(latest.get("open", latest.get("close", 0)))
            current = float(latest.get("close", 0))
            change = current - prev_close
            change_percent = (change / prev_close * 100) if prev_close > 0 else 0

            return {
                "stock_id": stock_id,
                "name": "",
                "current_price": Decimal(str(current)),
                "change": Decimal(str(change)),
                "change_percent": Decimal(str(change_percent)),
                "open": Decimal(str(latest.get("open", 0))),
                "high": Decimal(str(latest.get("max", 0))),
                "low": Decimal(str(latest.get("min", 0))),
                "volume": int(latest.get("Trading_Volume", 0)),
                "market_region": "TW",
                "currency": "TWD",
                "updated_at": datetime.now(),
            }
        except Exception as e:
            print(f"FinMind API 失敗: {e}")
            # Return mock data for testing
            return generate_mock_realtime_price(stock_id)

    def get_realtime_prices_batch(self, stock_ids: List[str], market: str = "TW") -> dict:
        """
        批量取得即時報價（優化版本，含快取）

        Args:
            stock_ids: 股票代碼列表
            market: 市場 'TW' 或 'US'

        Returns:
            dict: {stock_id: price_data}
        """
        if not stock_ids:
            return {}

        # 先從快取取得
        cache_keys = [f"{market}:{sid}" for sid in stock_ids]
        cached = _price_cache.get_batch(cache_keys)

        results = {}
        missing_ids = []

        for stock_id in stock_ids:
            cache_key = f"{market}:{stock_id}"
            if cache_key in cached:
                results[stock_id] = cached[cache_key]
            else:
                missing_ids.append(stock_id)

        # 如果全部都有快取，直接返回
        if not missing_ids:
            return results

        # 獲取缺少的報價
        new_prices = {}

        if market == "US":
            # US stocks - 逐一查詢（yfinance 沒有批量 API）
            for stock_id in missing_ids:
                try:
                    price_data = self._get_us_realtime_price(stock_id)
                    if price_data:
                        new_prices[stock_id] = price_data
                        results[stock_id] = price_data
                except Exception as e:
                    print(f"US Stock {stock_id} 報價失敗: {e}")
        else:
            # TW stocks - 使用 TWSE 批量 API（含上市+上櫃）
            try:
                batch_data = self.twse.get_realtime_price(missing_ids)
                for item in batch_data:
                    stock_id = item.get("stock_id", "")
                    if not stock_id:
                        continue

                    price = float(item.get("price", 0) or 0)
                    yesterday_close = float(item.get("yesterday_close", 0) or 0)

                    # 如果即時價為 0，嘗試用昨收
                    if price == 0 and yesterday_close > 0:
                        price = yesterday_close

                    change = price - yesterday_close if price and yesterday_close else 0
                    change_percent = (change / yesterday_close * 100) if yesterday_close > 0 else 0

                    price_data = {
                        "stock_id": stock_id,
                        "name": item.get("name", ""),
                        "current_price": Decimal(str(price)),
                        "change": Decimal(str(change)),
                        "change_percent": Decimal(str(round(change_percent, 2))),
                        "open": Decimal(str(item.get("open", 0) or 0)),
                        "high": Decimal(str(item.get("high", 0) or 0)),
                        "low": Decimal(str(item.get("low", 0) or 0)),
                        "volume": int(item.get("volume", 0) or 0),
                        "market_region": "TW",
                        "currency": "TWD",
                        "updated_at": datetime.now(),
                    }
                    new_prices[stock_id] = price_data
                    results[stock_id] = price_data
            except Exception as e:
                print(f"TWSE 批量報價失敗: {e}")

            # 對批量查詢未命中的股票，逐一補查
            still_missing = [sid for sid in missing_ids if sid not in results]
            if still_missing:
                for stock_id in still_missing:
                    try:
                        price_data = self._get_tw_realtime_price(stock_id)
                        if price_data:
                            new_prices[stock_id] = price_data
                            results[stock_id] = price_data
                    except Exception as e2:
                        print(f"TW Stock {stock_id} 逐一補查失敗: {e2}")

        # 快取新獲取的報價
        if new_prices:
            cache_data = {f"{market}:{sid}": data for sid, data in new_prices.items()}
            _price_cache.set_batch(cache_data)

        return results

    def get_history(self, db: Session, stock_id: str, days: int = 60, period: str = "day", market: str = "TW") -> List[dict]:
        """
        取得歷史K線

        Args:
            db: Database session
            stock_id: Stock ID
            days: Number of periods to return
            period: "day", "week", or "month"
            market: 'TW' for Taiwan stocks, 'US' for US stocks
        """
        if market == "US":
            return self._get_us_history(stock_id, days, period)
        else:
            return self._get_tw_history(db, stock_id, days, period)

    def _get_us_history(self, stock_id: str, days: int = 60, period: str = "day") -> List[dict]:
        """取得美股歷史K線（含快取）"""
        cache_key = f"us_history:{stock_id}:{days}:{period}"
        cached = _get_history_cache(cache_key)
        if cached is not None:
            return cached

        # Map days to yfinance period
        if period == "week":
            yf_period = f"{min(days * 7, 365)}d"
        elif period == "month":
            yf_period = f"{min(days * 31, 730)}d"
        else:
            yf_period = f"{min(days, 365)}d"

        raw_data = self.us_fetcher.get_stock_price(stock_id, period=yf_period)

        if not raw_data:
            return []

        # Apply aggregation if needed
        if period == "week":
            result = self._aggregate_to_weekly(raw_data, days)
        elif period == "month":
            result = self._aggregate_to_monthly(raw_data, days)
        else:
            result = raw_data[-days:] if len(raw_data) > days else raw_data

        _set_history_cache(cache_key, result)
        return result

    def _get_tw_history(self, db: Session, stock_id: str, days: int = 60, period: str = "day") -> List[dict]:
        """取得台股歷史K線"""
        # For weekly/monthly, we need more raw data to aggregate
        if period == "week":
            raw_days = days * 7
        elif period == "month":
            raw_days = days * 31
        else:
            raw_days = days

        end_date = date.today()
        start_date = end_date - timedelta(days=raw_days)

        # Try database first
        prices = (
            db.query(StockPrice)
            .filter(
                StockPrice.stock_id == stock_id,
                StockPrice.date >= start_date,
                StockPrice.date <= end_date,
            )
            .order_by(StockPrice.date)
            .all()
        )

        if prices:
            raw_data = [
                {
                    "date": p.date.isoformat(),
                    "open": float(p.open),
                    "high": float(p.high),
                    "low": float(p.low),
                    "close": float(p.close),
                    "volume": int(p.volume),
                }
                for p in prices
            ]
        else:
            # Fallback to FinMind
            try:
                df = self.finmind.get_stock_price(
                    stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
                )

                if len(df) == 0:
                    # Return mock data for testing
                    return generate_mock_stock_history(stock_id, days)

                # Standardize column names
                if 'max' in df.columns:
                    df['high'] = df['max']
                if 'min' in df.columns:
                    df['low'] = df['min']
                if 'Trading_Volume' in df.columns:
                    df['volume'] = df['Trading_Volume']

                raw_data = []
                for _, row in df.iterrows():
                    raw_data.append({
                        "date": str(row['date']),
                        "open": float(row['open']),
                        "high": float(row['high']),
                        "low": float(row['low']),
                        "close": float(row['close']),
                        "volume": int(row['volume']),
                    })
            except Exception as e:
                print(f"FinMind history API 失敗: {e}")
                # Return mock data for testing
                return generate_mock_stock_history(stock_id, days)

        # Apply aggregation if needed
        if period == "week":
            return self._aggregate_to_weekly(raw_data, days)
        elif period == "month":
            return self._aggregate_to_monthly(raw_data, days)

        return raw_data[-days:] if len(raw_data) > days else raw_data

    def _aggregate_to_weekly(self, daily_data: List[dict], limit: int) -> List[dict]:
        """Aggregate daily data to weekly K-lines"""
        if not daily_data:
            return []

        import pandas as pd

        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # Resample to weekly (W-FRI for Taiwan market week ending Friday)
        weekly = df.resample('W-FRI').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

        result = []
        for date_idx, row in weekly.iterrows():
            result.append({
                "date": date_idx.strftime("%Y-%m-%d"),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume']),
            })

        return result[-limit:] if len(result) > limit else result

    def _aggregate_to_monthly(self, daily_data: List[dict], limit: int) -> List[dict]:
        """Aggregate daily data to monthly K-lines"""
        if not daily_data:
            return []

        import pandas as pd

        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # Resample to monthly
        monthly = df.resample('ME').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

        result = []
        for date_idx, row in monthly.iterrows():
            result.append({
                "date": date_idx.strftime("%Y-%m-%d"),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume']),
            })

        return result[-limit:] if len(result) > limit else result

    def get_news(self, stock_id: str, market: str = "TW", limit: int = 10) -> List[dict]:
        """
        取得股票新聞

        Args:
            stock_id: Stock ID/Symbol
            market: 'TW' for Taiwan stocks, 'US' for US stocks
            limit: Maximum number of news items
        """
        if market == "US":
            # Combine news from multiple global sources
            all_news = []

            # 1. Get news from yfinance
            try:
                yf_news = self.us_fetcher.get_company_news(stock_id, limit // 2)
                all_news.extend(yf_news)
            except Exception as e:
                print(f"yfinance news error: {e}")

            # 2. Get news from global sources (Yahoo Finance, MarketWatch, etc.)
            try:
                global_news = self.global_news.fetch_stock_news(stock_id, limit)
                all_news.extend(global_news)
            except Exception as e:
                print(f"Global news error: {e}")

            # Deduplicate by title
            seen = set()
            unique_news = []
            for news in all_news:
                title_key = news.get("title", "")[:50].lower()
                if title_key not in seen:
                    seen.add(title_key)
                    unique_news.append(news)

            return unique_news[:limit]
        else:
            # Taiwan news handled by news_service
            return []
