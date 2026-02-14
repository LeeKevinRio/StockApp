"""
財報日曆 + 除息日曆服務
"""
from typing import Dict, List
from datetime import date, timedelta
import logging

from app.data_fetchers import FinMindFetcher, USStockFetcher
from app.config import settings

logger = logging.getLogger(__name__)


class CalendarService:
    """財報日曆與除息日曆服務"""

    def __init__(self):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        self.us_fetcher = USStockFetcher()

    def get_earnings_calendar(self, market: str = "TW", month: int = None, year: int = None) -> Dict:
        """取得財報公佈日曆"""
        today = date.today()
        target_year = year or today.year
        target_month = month or today.month

        if market == "US":
            return self._get_us_earnings_calendar(target_year, target_month)
        else:
            return self._get_tw_earnings_calendar(target_year, target_month)

    def get_dividend_calendar(self, market: str = "TW", month: int = None, year: int = None) -> Dict:
        """取得除權息日曆"""
        today = date.today()
        target_year = year or today.year
        target_month = month or today.month

        if market == "US":
            return self._get_us_dividend_calendar(target_year, target_month)
        else:
            return self._get_tw_dividend_calendar(target_year, target_month)

    def _get_tw_earnings_calendar(self, year: int, month: int) -> Dict:
        """台股財報公佈日曆 — 根據法規時程推估"""
        events = []

        # 台股財報公佈時程（法規規定）
        deadlines = {
            3: {"quarter": "Q4/年報", "deadline": f"{year}-03-31"},
            5: {"quarter": "Q1", "deadline": f"{year}-05-15"},
            8: {"quarter": "Q2/半年報", "deadline": f"{year}-08-14"},
            11: {"quarter": "Q3", "deadline": f"{year}-11-14"},
        }

        # 營收公佈：每月10日前
        events.append({
            "date": f"{year}-{month:02d}-10",
            "type": "revenue",
            "title": f"{month-1 if month > 1 else 12}月營收公佈截止",
            "description": "上市櫃公司公佈上月營收",
            "importance": "high",
        })

        # 財報截止日
        if month in deadlines:
            info = deadlines[month]
            events.append({
                "date": info["deadline"],
                "type": "earnings",
                "title": f"{info['quarter']} 財報公佈截止",
                "description": f"上市櫃公司公佈 {info['quarter']} 財務報告",
                "importance": "critical",
            })

        return {
            "market": "TW",
            "year": year,
            "month": month,
            "events": events,
        }

    def _get_us_earnings_calendar(self, year: int, month: int) -> Dict:
        """美股財報日曆 — 抓取主要公司 earnings dates"""
        events = []

        # 主要美股公司的 earnings 日期
        major_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]

        for symbol in major_stocks:
            try:
                earnings = self.us_fetcher.get_earnings_history(symbol)
                for earning in earnings[:2]:
                    earn_date = earning.get("date", "")
                    if earn_date and earn_date.startswith(f"{year}-{month:02d}"):
                        events.append({
                            "date": earn_date,
                            "type": "earnings",
                            "title": f"{symbol} 財報公佈",
                            "stock_id": symbol,
                            "eps_estimate": earning.get("eps_estimate"),
                            "eps_actual": earning.get("eps_actual"),
                            "surprise_pct": earning.get("surprise_percent"),
                            "importance": "high",
                        })
            except Exception as e:
                logger.warning(f"取得 {symbol} earnings 失敗: {e}")

        events.sort(key=lambda x: x.get("date", ""))
        return {
            "market": "US",
            "year": year,
            "month": month,
            "events": events,
        }

    def _get_tw_dividend_calendar(self, year: int, month: int) -> Dict:
        """台股除權息日曆"""
        events = []
        start_date = f"{year}-{month:02d}-01"
        end_month = month + 1 if month < 12 else 1
        end_year = year if month < 12 else year + 1
        end_date = f"{end_year}-{end_month:02d}-01"

        # 熱門台股除息查詢
        popular_tw = ["2330", "2317", "2454", "2881", "2882", "2886",
                       "1301", "1303", "2412", "2603"]

        for stock_id in popular_tw:
            try:
                div_data = self.finmind.get_dividend(stock_id, start_date, end_date)
                if len(div_data) > 0:
                    for _, row in div_data.iterrows():
                        ex_date = str(row.get("date", ""))
                        if ex_date.startswith(f"{year}-{month:02d}"):
                            cash_div = float(row.get("CashEarningsDistribution", 0) or 0) + \
                                       float(row.get("CashStatutorySurplus", 0) or 0)
                            stock_div = float(row.get("StockEarningsDistribution", 0) or 0)
                            events.append({
                                "date": ex_date,
                                "type": "dividend",
                                "title": f"{stock_id} 除息",
                                "stock_id": stock_id,
                                "cash_dividend": round(cash_div, 2),
                                "stock_dividend": round(stock_div, 2),
                                "importance": "medium",
                            })
            except Exception as e:
                logger.warning(f"取得 {stock_id} 除息資料失敗: {e}")

        events.sort(key=lambda x: x.get("date", ""))
        return {
            "market": "TW",
            "year": year,
            "month": month,
            "events": events,
        }

    def _get_us_dividend_calendar(self, year: int, month: int) -> Dict:
        """美股除息日曆"""
        events = []
        major_div_stocks = ["AAPL", "MSFT", "JNJ", "PG", "KO", "JPM", "V", "HD"]

        for symbol in major_div_stocks:
            try:
                divs = self.us_fetcher.get_dividends(symbol)
                for year_data in divs:
                    for payment in (year_data.get("payments") or []):
                        pay_date = payment.get("date", "")
                        if pay_date.startswith(f"{year}-{month:02d}"):
                            events.append({
                                "date": pay_date,
                                "type": "dividend",
                                "title": f"{symbol} 除息",
                                "stock_id": symbol,
                                "cash_dividend": payment.get("amount", 0),
                                "importance": "medium",
                            })
            except Exception as e:
                logger.warning(f"取得 {symbol} dividend 失敗: {e}")

        events.sort(key=lambda x: x.get("date", ""))
        return {
            "market": "US",
            "year": year,
            "month": month,
            "events": events,
        }


# 全域實例
calendar_service = CalendarService()
