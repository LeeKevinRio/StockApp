"""
Stock Data Service
"""
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models import Stock, StockPrice
from app.data_fetchers import FinMindFetcher, FugleFetcher, TWSEFetcher
from app.config import settings


class StockDataService:
    """股票數據服務"""

    def __init__(self):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        self.fugle = FugleFetcher(settings.FUGLE_API_KEY) if settings.FUGLE_API_KEY else None
        self.twse = TWSEFetcher()

    def search_stocks(self, db: Session, query: str) -> List[Stock]:
        """搜尋股票"""
        return (
            db.query(Stock)
            .filter(
                (Stock.stock_id.like(f"%{query}%"))
                | (Stock.name.like(f"%{query}%"))
            )
            .limit(20)
            .all()
        )

    def get_stock(self, db: Session, stock_id: str) -> Optional[Stock]:
        """取得股票詳情"""
        return db.query(Stock).filter(Stock.stock_id == stock_id).first()

    def get_realtime_price(self, stock_id: str) -> dict:
        """取得即時報價（優先順序：TWSE → Fugle → FinMind）"""

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
            "updated_at": datetime.now(),
        }

    def get_history(self, db: Session, stock_id: str, days: int = 60) -> List[dict]:
        """取得歷史K線"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

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
            return [
                {
                    "date": p.date.isoformat(),  # 確保日期為 ISO 格式字符串
                    "open": float(p.open),        # 轉換為 float
                    "high": float(p.high),
                    "low": float(p.low),
                    "close": float(p.close),
                    "volume": int(p.volume),
                }
                for p in prices
            ]

        # Fallback to FinMind
        df = self.finmind.get_stock_price(
            stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )

        if len(df) == 0:
            return []

        # ✨ 關鍵修復：標準化欄位名稱（FinMind 使用 max/min 而非 high/low）
        if 'max' in df.columns:
            df['high'] = df['max']
        if 'min' in df.columns:
            df['low'] = df['min']
        if 'Trading_Volume' in df.columns:
            df['volume'] = df['Trading_Volume']

        # 選擇需要的欄位並確保格式正確
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": str(row['date']),  # 確保為字符串
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume']),
            })

        return result
