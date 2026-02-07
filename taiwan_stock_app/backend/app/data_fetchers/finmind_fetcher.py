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

    def get_financial_statements(
        self, stock_id: str, start_date: str, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """取得財務報表（季報）- 含 EPS、毛利率、營業利益率等"""
        params = {"data_id": stock_id, "start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        try:
            return self._request("TaiwanStockFinancialStatements", params)
        except:
            return pd.DataFrame()

    def get_per_pbr(
        self, stock_id: str, start_date: str, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """取得本益比、股價淨值比"""
        params = {"data_id": stock_id, "start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        try:
            return self._request("TaiwanStockPER", params)
        except:
            return pd.DataFrame()

    def get_dividend(
        self, stock_id: str, start_date: str, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """取得股利資料"""
        params = {"data_id": stock_id, "start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        try:
            return self._request("TaiwanStockDividend", params)
        except:
            return pd.DataFrame()

    def get_stock_list(self) -> pd.DataFrame:
        """取得所有上市櫃股票清單"""
        return self._request("TaiwanStockInfo", {})

    def get_balance_sheet(
        self, stock_id: str, start_date: str, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """取得資產負債表"""
        params = {"data_id": stock_id, "start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        try:
            return self._request("TaiwanStockBalanceSheet", params)
        except:
            return pd.DataFrame()

    def get_cash_flow(
        self, stock_id: str, start_date: str, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """取得現金流量表"""
        params = {"data_id": stock_id, "start_date": start_date}
        if end_date:
            params["end_date"] = end_date
        try:
            return self._request("TaiwanStockCashFlowsStatement", params)
        except:
            return pd.DataFrame()
