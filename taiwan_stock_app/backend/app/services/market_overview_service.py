"""
市場概覽服務
聚合產業數據、熱力圖、漲跌排行
"""
from typing import Dict, List, Any, Tuple
from datetime import date, timedelta
import logging
import time

from sqlalchemy.orm import Session

from app.data_fetchers import FinMindFetcher, TWSEFetcher, USStockFetcher
from app.config import settings
from app.database import SessionLocal
from app.models.stock import Stock

logger = logging.getLogger(__name__)


class TTLCache:
    """簡易 TTL 快取，基於 dict + 時間戳記"""

    def __init__(self):
        self._store: Dict[str, Tuple[float, Any]] = {}  # key -> (expire_time, data)

    def get(self, key: str) -> Any:
        """取得快取資料，若已過期則回傳 None"""
        if key in self._store:
            expire_time, data = self._store[key]
            if time.time() < expire_time:
                logger.info(f"TTL 快取命中: {key}")
                return data
            # 已過期，移除
            del self._store[key]
            logger.info(f"TTL 快取已過期: {key}")
        return None

    def set(self, key: str, data: Any, ttl_seconds: int):
        """寫入快取，設定 TTL（秒）"""
        self._store[key] = (time.time() + ttl_seconds, data)
        logger.info(f"TTL 快取已寫入: {key}, TTL={ttl_seconds}s")

    def clear(self):
        """清除所有快取"""
        self._store.clear()

    def invalidate(self, prefix: str = ""):
        """清除符合前綴的快取"""
        if not prefix:
            self.clear()
            return
        keys_to_remove = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_remove:
            del self._store[k]


# 模組層級的快取實例（跨請求共享）
_result_cache = TTLCache()

# 快取 TTL 設定（秒）
HEATMAP_CACHE_TTL = 300   # 熱力圖快取 5 分鐘
RANKINGS_CACHE_TTL = 180   # 排行快取 3 分鐘


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
        """取得熱力圖數據（按產業分組），帶 TTL 快取（5 分鐘）"""
        cache_key = f"heatmap:{market}"
        cached = _result_cache.get(cache_key)
        if cached is not None:
            return cached

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

        # 清除 _tw_quote_cache 避免跨請求的陳舊資料
        self._tw_quote_cache.clear()

        # 寫入結果快取
        _result_cache.set(cache_key, result, HEATMAP_CACHE_TTL)

        return result

    def get_rankings(self, market: str = "TW", category: str = "gainers", limit: int = 20) -> Dict:
        """取得漲跌排行，帶 TTL 快取（3 分鐘）"""
        cache_key = f"rankings:{market}:{category}:{limit}"
        cached = _result_cache.get(cache_key)
        if cached is not None:
            return cached

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

        result = {
            "market": market,
            "category": category,
            "stocks": all_stocks[:limit],
            "total": len(all_stocks),
        }

        # 寫入結果快取
        _result_cache.set(cache_key, result, RANKINGS_CACHE_TTL)

        return result

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
