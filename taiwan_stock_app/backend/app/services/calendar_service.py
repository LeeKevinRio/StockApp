"""
財報日曆 + 除息日曆 + 經濟行事曆服務
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


    def get_economic_calendar(self, market: str = "TW", month: int = None, year: int = None) -> Dict:
        """取得經濟行事曆"""
        today = date.today()
        target_year = year or today.year
        target_month = month or today.month

        if market == "US":
            return self._get_us_economic_calendar(target_year, target_month)
        else:
            return self._get_tw_economic_calendar(target_year, target_month)

    def _get_tw_economic_calendar(self, year: int, month: int) -> Dict:
        """台灣經濟行事曆 — 重要經濟數據公佈時程"""
        events = []

        # 台灣主要經濟數據公佈時程
        tw_economic_events = {
            1: [
                {"day": 7, "title": "12月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 20, "title": "12月外銷訂單統計", "type": "export_orders", "importance": "medium"},
            ],
            2: [
                {"day": 7, "title": "1月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 25, "title": "Q4 GDP初估值", "type": "gdp", "importance": "critical"},
            ],
            3: [
                {"day": 7, "title": "2月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 20, "title": "央行理監事會議（利率決議）", "type": "interest_rate", "importance": "critical"},
            ],
            4: [
                {"day": 7, "title": "3月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 28, "title": "Q1 GDP概估值", "type": "gdp", "importance": "critical"},
            ],
            5: [
                {"day": 7, "title": "4月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 22, "title": "Q1 GDP修正值", "type": "gdp", "importance": "high"},
            ],
            6: [
                {"day": 7, "title": "5月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 15, "title": "央行理監事會議（利率決議）", "type": "interest_rate", "importance": "critical"},
            ],
            7: [
                {"day": 7, "title": "6月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 28, "title": "Q2 GDP概估值", "type": "gdp", "importance": "critical"},
            ],
            8: [
                {"day": 7, "title": "7月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 18, "title": "Q2 GDP修正值", "type": "gdp", "importance": "high"},
            ],
            9: [
                {"day": 7, "title": "8月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 19, "title": "央行理監事會議（利率決議）", "type": "interest_rate", "importance": "critical"},
            ],
            10: [
                {"day": 7, "title": "9月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 28, "title": "Q3 GDP概估值", "type": "gdp", "importance": "critical"},
            ],
            11: [
                {"day": 7, "title": "10月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 22, "title": "Q3 GDP修正值", "type": "gdp", "importance": "high"},
            ],
            12: [
                {"day": 7, "title": "11月CPI年增率公佈", "type": "cpi", "importance": "high"},
                {"day": 15, "title": "央行理監事會議（利率決議）", "type": "interest_rate", "importance": "critical"},
            ],
        }

        for evt in tw_economic_events.get(month, []):
            events.append({
                "date": f"{year}-{month:02d}-{evt['day']:02d}",
                "type": evt["type"],
                "title": evt["title"],
                "description": f"台灣 {evt['title']}",
                "importance": evt["importance"],
            })

        # 每月固定事件：外資買賣超統計
        events.append({
            "date": f"{year}-{month:02d}-01",
            "type": "institutional",
            "title": "上月外資買賣超統計公佈",
            "description": "證交所公佈上月外資買賣超彙總",
            "importance": "medium",
        })

        events.sort(key=lambda x: x.get("date", ""))
        return {
            "market": "TW",
            "year": year,
            "month": month,
            "events": events,
        }

    def _get_us_economic_calendar(self, year: int, month: int) -> Dict:
        """美國經濟行事曆 — 重要經濟數據公佈時程"""
        events = []

        # 美國主要經濟數據時程（每月固定事件）
        us_monthly_events = [
            {"day": 3, "title": "ISM Manufacturing PMI", "type": "pmi", "importance": "high",
             "description": "ISM 製造業 PMI 指數，反映製造業景氣"},
            {"day": 5, "title": "ISM Services PMI", "type": "pmi", "importance": "high",
             "description": "ISM 非製造業 PMI 指數，反映服務業景氣"},
            {"day": 10, "title": "CPI 消費者物價指數", "type": "cpi", "importance": "critical",
             "description": "美國 CPI 年增率，聯準會決策關鍵依據"},
            {"day": 13, "title": "PPI 生產者物價指數", "type": "ppi", "importance": "high",
             "description": "美國 PPI 年增率，通膨先行指標"},
            {"day": 15, "title": "零售銷售數據", "type": "retail_sales", "importance": "high",
             "description": "美國零售銷售月增率，消費動能指標"},
            {"day": 17, "title": "工業生產指數", "type": "industrial_production", "importance": "medium",
             "description": "美國工業生產月增率"},
            {"day": 22, "title": "成屋銷售", "type": "existing_home_sales", "importance": "medium",
             "description": "美國成屋銷售數據"},
            {"day": 27, "title": "耐久財訂單", "type": "durable_goods", "importance": "high",
             "description": "美國耐久財訂單月增率"},
        ]

        for evt in us_monthly_events:
            events.append({
                "date": f"{year}-{month:02d}-{evt['day']:02d}",
                "type": evt["type"],
                "title": evt["title"],
                "description": evt["description"],
                "importance": evt["importance"],
            })

        # FOMC 會議（每年 8 次，大約 6 週一次）
        fomc_months = {1: 29, 3: 19, 5: 7, 6: 18, 7: 30, 9: 17, 11: 5, 12: 17}
        if month in fomc_months:
            events.append({
                "date": f"{year}-{month:02d}-{fomc_months[month]:02d}",
                "type": "fomc",
                "title": "FOMC 利率決議",
                "description": "聯準會利率決策公佈，影響全球金融市場",
                "importance": "critical",
            })

        # 非農就業報告（每月第一個週五）
        first_day = date(year, month, 1)
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + timedelta(days=days_until_friday)
        events.append({
            "date": first_friday.isoformat(),
            "type": "nonfarm_payrolls",
            "title": "非農就業報告",
            "description": "美國非農就業人數變動，最重要的就業指標",
            "importance": "critical",
        })

        # GDP（1月/4月/7月/10月公佈上季）
        gdp_months = {1: "Q4", 4: "Q1", 7: "Q2", 10: "Q3"}
        if month in gdp_months:
            events.append({
                "date": f"{year}-{month:02d}-25",
                "type": "gdp",
                "title": f"GDP {gdp_months[month]} 初估值",
                "description": f"美國 {gdp_months[month]} GDP 年化季增率",
                "importance": "critical",
            })

        events.sort(key=lambda x: x.get("date", ""))
        return {
            "market": "US",
            "year": year,
            "month": month,
            "events": events,
        }


# 全域實例
calendar_service = CalendarService()
