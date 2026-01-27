"""
Stock Data Service
"""
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models import Stock, StockPrice
from app.data_fetchers import FinMindFetcher, FugleFetcher, TWSEFetcher, USStockFetcher, GlobalNewsFetcher
from app.config import settings


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

        # 1. 優先使用 TWSE（免費即時）
        try:
            quote = self.twse.get_realtime_quote(stock_id)
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
        end_date = date.today()
        start_date = end_date - timedelta(days=1)
        prices = self.finmind.get_stock_price(
            stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
        if len(prices) == 0:
            return None

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
        """取得美股歷史K線"""
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
            return self._aggregate_to_weekly(raw_data, days)
        elif period == "month":
            return self._aggregate_to_monthly(raw_data, days)

        return raw_data[-days:] if len(raw_data) > days else raw_data

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
            df = self.finmind.get_stock_price(
                stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )

            if len(df) == 0:
                return []

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
