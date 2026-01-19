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

    def get_realtime_price(self, stock_ids: List[str]) -> List[Dict]:
        """取得即時報價（證交所 MIS API）"""
        self._rate_limit()

        # 格式: tse_2330.tw|tse_2317.tw
        ex_ch = "|".join([f"tse_{sid}.tw" for sid in stock_ids])

        response = requests.get(
            self.REALTIME_URL,
            params={"ex_ch": ex_ch, "json": "1", "_": int(time.time() * 1000)},
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("msgArray", []):
            results.append(
                {
                    "stock_id": item.get("c", ""),
                    "name": item.get("n", ""),
                    "price": float(item.get("z", 0) or 0),
                    "open": float(item.get("o", 0) or 0),
                    "high": float(item.get("h", 0) or 0),
                    "low": float(item.get("l", 0) or 0),
                    "volume": int(item.get("v", 0) or 0),
                    "yesterday_close": float(item.get("y", 0) or 0),
                }
            )
        return results

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
