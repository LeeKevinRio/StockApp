"""
證交所 OpenAPI 整合
"""
import requests
from typing import Dict, List
import time


class TWSEFetcher:
    """
    證交所 OpenAPI 整合
    注意事項:
    - 每5秒最多3次請求，否則會被暫時封鎖
    - 即時行情約有5-20秒延遲
    """

    REALTIME_URL = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    DAILY_URL = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"
    INSTITUTIONAL_URL = "https://www.twse.com.tw/rwd/zh/fund/T86"

    def __init__(self):
        self.last_request_time = 0
        self.request_interval = 2  # 每次請求間隔2秒

    def _rate_limit(self):
        """簡單的請求頻率控制"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def get_realtime_quote(self, stock_id: str) -> Dict:
        """取得單一股票即時報價"""
        self._rate_limit()

        # 格式: tse_2330.tw (上市) 或 otc_6165.tw (上櫃)
        # 先嘗試上市
        ex_ch = f"tse_{stock_id}.tw"

        response = requests.get(
            self.REALTIME_URL,
            params={"ex_ch": ex_ch, "json": "1", "_": int(time.time() * 1000)},
        )
        response.raise_for_status()
        data = response.json()

        msg_array = data.get("msgArray", [])

        # 檢查回傳的資料是否有效（c 欄位為股票代碼，空代表無效）
        has_valid_data = (
            msg_array
            and len(msg_array) > 0
            and msg_array[0].get("c", "") != ""
        )

        # 如果上市沒有有效數據，嘗試上櫃
        if not has_valid_data:
            self._rate_limit()
            ex_ch = f"otc_{stock_id}.tw"
            response = requests.get(
                self.REALTIME_URL,
                params={"ex_ch": ex_ch, "json": "1", "_": int(time.time() * 1000)},
            )
            response.raise_for_status()
            data = response.json()
            msg_array = data.get("msgArray", [])

        if not msg_array or len(msg_array) == 0 or msg_array[0].get("c", "") == "":
            raise Exception(f"找不到股票 {stock_id} 的即時報價數據")

        item = msg_array[0]
        current_price = self._safe_float(item.get("z"))
        yesterday_close = self._safe_float(item.get("y"))

        # 如果即時價為 0（未成交），嘗試用昨收
        if current_price == 0 and yesterday_close > 0:
            current_price = yesterday_close

        # 計算漲跌
        change = current_price - yesterday_close if current_price and yesterday_close else 0
        change_percent = (change / yesterday_close * 100) if yesterday_close > 0 else 0

        return {
            "stock_id": stock_id,
            "name": item.get("n", ""),
            "price": current_price,
            "change": change,
            "change_percent": change_percent,
            "open": self._safe_float(item.get("o")),
            "high": self._safe_float(item.get("h")),
            "low": self._safe_float(item.get("l")),
            "volume": int(self._safe_float(item.get("v"))),
            "updated_at": item.get("t", ""),  # 時間戳
        }

    def _safe_float(self, value, default=0) -> float:
        """安全轉換為 float，處理 '-' 等無效值"""
        if value is None or value == '' or value == '-' or value == '--':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_realtime_price(self, stock_ids: List[str]) -> List[Dict]:
        """取得即時報價（證交所 MIS API）- 批量查詢，同時查上市與上櫃"""
        self._rate_limit()

        # 同時查詢上市(tse)與上櫃(otc)
        ex_ch_parts = []
        for sid in stock_ids:
            ex_ch_parts.append(f"tse_{sid}.tw")
            ex_ch_parts.append(f"otc_{sid}.tw")
        ex_ch = "|".join(ex_ch_parts)

        response = requests.get(
            self.REALTIME_URL,
            params={"ex_ch": ex_ch, "json": "1", "_": int(time.time() * 1000)},
        )
        response.raise_for_status()
        data = response.json()

        # 用 dict 去重（同一股票可能 tse 和 otc 都有回傳，取有效的那個）
        seen = {}
        for item in data.get("msgArray", []):
            stock_id = item.get("c", "")
            if not stock_id:
                continue
            price = self._safe_float(item.get("z"))
            yesterday_close = self._safe_float(item.get("y"))

            if stock_id in seen:
                existing = seen[stock_id]
                # 已有完整有效數據（price > 0 且 yesterday_close > 0），不覆蓋
                if existing["price"] > 0 and existing["yesterday_close"] > 0:
                    continue
                # 新數據也沒有價格，跳過
                if price == 0:
                    continue

            seen[stock_id] = {
                "stock_id": stock_id,
                "name": item.get("n", ""),
                "price": price,
                "open": self._safe_float(item.get("o")),
                "high": self._safe_float(item.get("h")),
                "low": self._safe_float(item.get("l")),
                "volume": int(self._safe_float(item.get("v"))),
                "yesterday_close": yesterday_close,
            }

        return list(seen.values())

    def get_daily_trading(self, stock_id: str, year: int, month: int) -> List[Dict]:
        """取得個股月成交資訊"""
        self._rate_limit()

        date_str = f"{year}{month:02d}01"
        response = requests.get(
            self.DAILY_URL,
            params={"date": date_str, "stockNo": stock_id, "response": "json"},
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for row in data.get("data", []):
            results.append(
                {
                    "date": row[0],
                    "volume": int(row[1].replace(",", "")),
                    "open": float(row[3].replace(",", "")),
                    "high": float(row[4].replace(",", "")),
                    "low": float(row[5].replace(",", "")),
                    "close": float(row[6].replace(",", "")),
                }
            )
        return results

    def get_institutional_daily(self, date_str: str) -> List[Dict]:
        """取得三大法人買賣超日報"""
        self._rate_limit()

        response = requests.get(
            self.INSTITUTIONAL_URL, params={"date": date_str, "response": "json"}
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for row in data.get("data", []):
            results.append(
                {
                    "stock_id": row[0],
                    "name": row[1],
                    "foreign_buy": int(row[2].replace(",", "")),
                    "foreign_sell": int(row[3].replace(",", "")),
                    "foreign_net": int(row[4].replace(",", "")),
                    "trust_buy": int(row[5].replace(",", "")),
                    "trust_sell": int(row[6].replace(",", "")),
                    "trust_net": int(row[7].replace(",", "")),
                }
            )
        return results


# 建立全域實例
twse_fetcher = TWSEFetcher()


def get_stock_realtime_price(stock_id: str) -> Dict:
    """取得單一股票即時報價的便捷函數"""
    try:
        return twse_fetcher.get_realtime_quote(stock_id)
    except Exception:
        return None
