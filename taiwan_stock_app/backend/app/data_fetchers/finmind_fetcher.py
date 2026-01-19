"""
FinMind API Integration
"""
import requests
from typing import Optional
import pandas as pd


class FinMindFetcher:
    BASE_URL = "https://api.finmindtrade.com/api/v4/data"

    def __init__(self, token: str):
        self.token = token

    def _request(self, dataset: str, params: dict) -> pd.DataFrame:
        """統一請求方法"""
        params.update({"dataset": dataset, "token": self.token})
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data["status"] != 200:
            raise Exception(f"FinMind API Error: {data.get('msg', 'Unknown error')}")
        return pd.DataFrame(data["data"])

    def get_stock_price(
        self, stock_id: str, start_date: str, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """取得股票歷史價格"""
        params = {"data_id": stock_id, "start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._request("TaiwanStockPrice", params)

    def get_institutional_investors(
        self, stock_id: str, start_date: str, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """取得三大法人買賣超"""
        params = {"data_id": stock_id, "start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._request("TaiwanStockInstitutionalInvestorsBuySell", params)

    def get_margin_trading(
        self, stock_id: str, start_date: str, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """取得融資融券資料"""
        params = {"data_id": stock_id, "start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._request("TaiwanStockMarginPurchaseShortSale", params)

    def get_monthly_revenue(
        self, stock_id: str, start_date: str, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """取得月營收資料"""
        params = {"data_id": stock_id, "start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        return self._request("TaiwanStockMonthRevenue", params)

    def get_stock_list(self) -> pd.DataFrame:
        """取得所有上市櫃股票清單"""
        return self._request("TaiwanStockInfo", {})
