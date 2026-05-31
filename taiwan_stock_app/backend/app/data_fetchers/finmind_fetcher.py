"""
FinMind API Integration
"""
import requests
import time
import threading
from typing import Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class FinMindFetcher:
    BASE_URL = "https://api.finmindtrade.com/api/v4/data"

    # 短期共用快取：FinMind 回傳的都是「當日/歷史」資料(股價收盤、法人、營收、財報等)，
    # 同一檔同一天重複預測(refresh / 批次後再單股查)會重抓多次。
    # 改用 class-level 快取讓所有 request / 平行執行緒共享，明顯減少重複外部呼叫。
    # 注意:即時報價走 TWSE/Fugle(另有來源)，這裡都是日級資料，快取 15 分鐘安全。
    _cache: dict = {}
    _cache_lock = threading.Lock()
    _CACHE_TTL = 900          # 15 分鐘
    _CACHE_MAX_ENTRIES = 500  # 容量上限，避免記憶體無限膨脹

    def __init__(self, token: str):
        self.token = token

    def _cache_key(self, dataset: str, params: dict) -> str:
        """以 dataset + 查詢參數(排除 token)組成快取 key"""
        items = sorted((k, v) for k, v in params.items() if k != "token")
        return dataset + "|" + "&".join(f"{k}={v}" for k, v in items)

    def _request(self, dataset: str, params: dict) -> pd.DataFrame:
        """統一請求方法（含 15 分鐘共用快取）"""
        cache_key = self._cache_key(dataset, params)
        now = time.time()

        # 先讀快取
        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                df, ts = cached
                if now - ts < self._CACHE_TTL:
                    return df.copy()  # 回傳副本，避免呼叫端修改污染快取

        params.update({"dataset": dataset, "token": self.token})
        # 必須設 timeout：此方法是所有 FinMind 呼叫的入口，每檔股票會打多次，
        # 若無 timeout 一旦遠端卡住，worker thread 會無限期阻塞 → AI 預測整個掛住
        response = requests.get(self.BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data["status"] != 200:
            raise Exception(f"FinMind API Error: {data.get('msg', 'Unknown error')}")
        df = pd.DataFrame(data["data"])

        # 只快取成功且非空的結果
        if not df.empty:
            with self._cache_lock:
                if len(self._cache) >= self._CACHE_MAX_ENTRIES:
                    # 簡易淘汰：清掉最舊的一筆
                    oldest = min(self._cache, key=lambda k: self._cache[k][1])
                    self._cache.pop(oldest, None)
                self._cache[cache_key] = (df, now)
        return df.copy()

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
        except Exception as e:
            logger.warning(f"取得財務報表失敗 (stock_id={stock_id}): {e}")
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
        except Exception as e:
            logger.warning(f"取得本益比/股價淨值比失敗 (stock_id={stock_id}): {e}")
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
        except Exception as e:
            logger.warning(f"取得股利資料失敗 (stock_id={stock_id}): {e}")
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
        except Exception as e:
            logger.warning(f"取得資產負債表失敗 (stock_id={stock_id}): {e}")
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
        except Exception as e:
            logger.warning(f"取得現金流量表失敗 (stock_id={stock_id}): {e}")
            return pd.DataFrame()
