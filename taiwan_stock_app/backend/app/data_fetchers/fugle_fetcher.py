"""
Fugle API Integration - 即時報價
"""
import requests
from typing import Dict, List
import asyncio
import websockets
import json


class FugleFetcher:
    """
    Fugle API 整合 - 即時報價
    免費方案限制:
    - REST API: 60 次/分鐘
    - WebSocket: 5 個訂閱
    """

    REST_BASE_URL = "https://api.fugle.tw/marketdata/v1.0/stock"
    WS_URL = "wss://api.fugle.tw/marketdata/v1.0/stock/streaming"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-API-KEY": api_key}

    def get_realtime_quote(self, stock_id: str) -> Dict:
        """取得即時報價"""
        url = f"{self.REST_BASE_URL}/intraday/quote/{stock_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()

        return {
            "stock_id": stock_id,
            "name": data.get("name", ""),
            "price": data.get("lastPrice", 0),
            "change": data.get("change", 0),
            "change_percent": data.get("changePercent", 0),
            "open": data.get("openPrice", 0),
            "high": data.get("highPrice", 0),
            "low": data.get("lowPrice", 0),
            "volume": data.get("totalVolume", 0),
            "updated_at": data.get("lastUpdated", ""),
        }

    def get_realtime_quotes_batch(self, stock_ids: List[str]) -> List[Dict]:
        """批量取得即時報價（注意 60次/分鐘限制）"""
        results = []
        for stock_id in stock_ids:
            try:
                quote = self.get_realtime_quote(stock_id)
                results.append(quote)
            except Exception as e:
                results.append({"stock_id": stock_id, "error": str(e)})
        return results

    async def subscribe_realtime(self, stock_ids: List[str], callback):
        """WebSocket 訂閱即時報價（最多5檔）"""
        if len(stock_ids) > 5:
            raise ValueError("免費方案最多訂閱5檔股票")

        uri = f"{self.WS_URL}?apiToken={self.api_key}"

        async with websockets.connect(uri) as websocket:
            # 訂閱
            for stock_id in stock_ids:
                subscribe_msg = {
                    "event": "subscribe",
                    "data": {"channel": "quote", "symbol": stock_id},
                }
                await websocket.send(json.dumps(subscribe_msg))

            # 接收訊息
            async for message in websocket:
                data = json.loads(message)
                await callback(data)
