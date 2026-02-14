"""
市場概覽服務
聚合產業數據、熱力圖、漲跌排行
"""
from typing import Dict, List
from datetime import date, timedelta
import logging

from sqlalchemy.orm import Session

from app.data_fetchers import FinMindFetcher, TWSEFetcher, USStockFetcher
from app.config import settings
from app.database import SessionLocal
from app.models.stock import Stock

logger = logging.getLogger(__name__)


class MarketOverviewService:
    """市場概覽服務"""

    # 台股產業分類
    TW_SECTORS = {
        "半導體": ["2330", "2454", "2303", "3711", "2379", "3034", "2408", "6415"],
        "電子零組件": ["2317", "2382", "3231", "2327", "2345", "3037"],
        "金融": ["2881", "2882", "2883", "2884", "2886", "2885", "2891", "2892"],
        "傳產": ["1301", "1303", "1326", "2002", "1402", "2105"],
        "航運": ["2603", "2609", "2615", "2618", "5608"],
        "通訊網路": ["2412", "3045", "4904", "6285"],
        "生技醫療": ["4743", "6446", "1760", "4147"],
        "電腦設備": ["2353", "2324", "2357", "3702", "2377"],
        "光電": ["3008", "2409", "3481", "6176"],
        "汽車": ["2201", "2207", "2227", "1513"],
    }

    # 美股產業分類
    US_SECTORS = {
        "科技": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "ADBE", "CRM"],
        "半導體": ["NVDA", "AMD", "INTC", "QCOM", "AVGO", "TXN"],
        "電商零售": ["AMZN", "WMT", "COST", "TGT", "HD"],
        "金融": ["JPM", "BAC", "GS", "MS", "V", "MA"],
        "醫療": ["JNJ", "PFE", "MRK", "ABBV", "LLY", "UNH"],
        "能源": ["XOM", "CVX", "COP", "SLB"],
        "電動車": ["TSLA", "RIVN", "LCID", "NIO"],
        "串流娛樂": ["NFLX", "DIS", "RBLX"],
        "雲端SaaS": ["SNOW", "PLTR", "COIN", "UBER"],
    }

    def __init__(self):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        self.twse = TWSEFetcher()
        self.us_fetcher = USStockFetcher()
        self._stock_name_cache: Dict[str, str] = {}
        self._tw_quote_cache: Dict[str, Dict] = {}

    def _get_stock_name(self, stock_id: str) -> str:
        """從資料庫查詢台股公司名稱"""
        if stock_id in self._stock_name_cache:
            return self._stock_name_cache[stock_id]
        try:
            db = SessionLocal()
            stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
            db.close()
            name = stock.name if stock and stock.name else stock_id
            self._stock_name_cache[stock_id] = name
            return name
        except Exception:
            return stock_id

    def _prefetch_tw_quotes(self, stock_ids: List[str]):
        """批量預取台股報價（TWSE API），快取結果"""
        try:
            results = self.twse.get_realtime_price(stock_ids)
            for item in results:
                sid = item["stock_id"]
                price = item.get("price", 0)
                yesterday = item.get("yesterday_close", 0)
                change = price - yesterday if price and yesterday else 0
                change_pct = (change / yesterday * 100) if yesterday > 0 else 0
                self._tw_quote_cache[sid] = {
                    "stock_id": sid,
                    "name": item.get("name", sid),
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                    "volume": item.get("volume", 0),
                }
            logger.info(f"TWSE 批量預取成功: {len(results)} 支股票")
        except Exception as e:
            logger.warning(f"TWSE 批量預取失敗: {e}")

    def get_heatmap_data(self, market: str = "TW") -> Dict:
        """取得熱力圖數據（按產業分組）"""
        sectors = self.TW_SECTORS if market == "TW" else self.US_SECTORS
        result = {"sectors": [], "market": market}

        # 台股：先用 TWSE 批量預取所有股票報價
        if market == "TW":
            all_tw_ids = []
            for ids in sectors.values():
                all_tw_ids.extend(ids[:6])
            self._prefetch_tw_quotes(list(set(all_tw_ids)))

        for sector_name, stock_ids in sectors.items():
            sector_data = {
                "name": sector_name,
                "stocks": [],
                "avg_change": 0,
                "total_volume": 0,
            }

            changes = []
            for stock_id in stock_ids[:6]:  # 每產業最多 6 支
                try:
                    if market == "TW":
                        quote = self._get_tw_quote(stock_id)
                    else:
                        quote = self.us_fetcher.get_realtime_quote(stock_id)

                    if quote:
                        change_pct = quote.get("change_percent", 0) or 0
                        changes.append(change_pct)
                        sector_data["stocks"].append({
                            "stock_id": stock_id,
                            "name": quote.get("name", stock_id),
                            "price": quote.get("price", 0),
                            "change_percent": round(change_pct, 2),
                            "volume": quote.get("volume", 0),
                        })
                        sector_data["total_volume"] += quote.get("volume", 0)
                except Exception as e:
                    logger.warning(f"取得 {stock_id} 行情失敗: {e}")

            if changes:
                sector_data["avg_change"] = round(sum(changes) / len(changes), 2)

            if sector_data["stocks"]:
                result["sectors"].append(sector_data)

        # 按平均漲跌幅排序
        result["sectors"].sort(key=lambda x: x["avg_change"], reverse=True)
        return result

    def get_rankings(self, market: str = "TW", category: str = "gainers", limit: int = 20) -> Dict:
        """取得漲跌排行"""
        sectors = self.TW_SECTORS if market == "TW" else self.US_SECTORS
        all_stocks = []

        # 收集所有股票報價
        all_ids = set()
        for ids in sectors.values():
            all_ids.update(ids)

        # 台股：批量預取
        if market == "TW" and not self._tw_quote_cache:
            self._prefetch_tw_quotes(list(all_ids))

        for stock_id in all_ids:
            try:
                if market == "TW":
                    quote = self._get_tw_quote(stock_id)
                else:
                    quote = self.us_fetcher.get_realtime_quote(stock_id)

                if quote and quote.get("price", 0) > 0:
                    all_stocks.append({
                        "stock_id": stock_id,
                        "name": quote.get("name", stock_id),
                        "price": quote.get("price", 0),
                        "change": quote.get("change", 0),
                        "change_percent": round(quote.get("change_percent", 0), 2),
                        "volume": quote.get("volume", 0),
                    })
            except Exception as e:
                logger.warning(f"取得 {stock_id} 排行數據失敗: {e}")

        # 排序
        if category == "gainers":
            all_stocks.sort(key=lambda x: x["change_percent"], reverse=True)
        elif category == "losers":
            all_stocks.sort(key=lambda x: x["change_percent"])
        elif category == "volume":
            all_stocks.sort(key=lambda x: x["volume"], reverse=True)
        elif category == "active":
            all_stocks.sort(key=lambda x: abs(x["change_percent"]), reverse=True)

        return {
            "market": market,
            "category": category,
            "stocks": all_stocks[:limit],
            "total": len(all_stocks),
        }

    def _get_tw_quote(self, stock_id: str) -> Dict:
        """取得台股即時報價（TWSE 快取 → FinMind → TWSE 單股 fallback）"""
        # 1. 先檢查 TWSE 批量預取的快取
        if stock_id in self._tw_quote_cache:
            return self._tw_quote_cache[stock_id]

        # 2. 嘗試 FinMind
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            prices = self.finmind.get_stock_price(
                stock_id,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            )
            if len(prices) >= 2:
                latest = prices.iloc[-1]
                prev = prices.iloc[-2]
                price = float(latest["close"])
                prev_close = float(prev["close"])
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                return {
                    "stock_id": stock_id,
                    "name": self._get_stock_name(stock_id),
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                    "volume": int(latest.get("Trading_Volume", 0)),
                }
            elif len(prices) == 1:
                latest = prices.iloc[0]
                return {
                    "stock_id": stock_id,
                    "name": self._get_stock_name(stock_id),
                    "price": round(float(latest["close"]), 2),
                    "change": 0,
                    "change_percent": 0,
                    "volume": int(latest.get("Trading_Volume", 0)),
                }
        except Exception as e:
            logger.warning(f"FinMind 報價失敗 {stock_id}: {e}")

        # 3. Fallback: TWSE 單股即時查詢
        try:
            quote = self.twse.get_realtime_quote(stock_id)
            if quote and quote.get("price", 0) > 0:
                return {
                    "stock_id": stock_id,
                    "name": quote.get("name") or self._get_stock_name(stock_id),
                    "price": round(quote.get("price", 0), 2),
                    "change": round(quote.get("change", 0), 2),
                    "change_percent": round(quote.get("change_percent", 0), 2),
                    "volume": quote.get("volume", 0),
                }
        except Exception as e:
            logger.warning(f"TWSE 報價也失敗 {stock_id}: {e}")

        return {}
