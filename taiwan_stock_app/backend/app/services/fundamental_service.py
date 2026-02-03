"""
Fundamental Data Service - 基本面數據服務
Provides fundamental analysis, financial statements, dividends, institutional trading, margin trading
"""
from typing import List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import Stock
from app.models.fundamental import (
    StockFundamental,
    StockDividend,
    InstitutionalTrading,
    MarginTrading,
    FinancialStatement,
)
from app.data_fetchers.finmind_fetcher import FinMindFetcher
from app.data_fetchers.us_stock_fetcher import USStockFundamentalFetcher
from app.config import settings


class FundamentalService:
    """基本面數據服務 - 支援台股(TW)與美股(US)"""

    def __init__(self):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        self.us_fetcher = USStockFundamentalFetcher()

    async def get_fundamentals(self, db: Session, stock_id: str, market: str = "TW") -> Optional[Dict]:
        """
        取得股票基本面數據

        Args:
            db: Database session
            stock_id: Stock ID/Symbol
            market: 'TW' for Taiwan stocks, 'US' for US stocks

        Returns:
            Dict with fundamental metrics (PE, PB, EPS, ROE, etc.)
        """
        if market == "US":
            return self._get_us_fundamentals(stock_id)
        else:
            return await self._get_tw_fundamentals(db, stock_id)

    def _get_us_fundamentals(self, stock_id: str) -> Optional[Dict]:
        """取得美股基本面數據 (from yfinance)"""
        try:
            data = self.us_fetcher.get_fundamentals(stock_id)
            if data:
                return {
                    "stock_id": stock_id,
                    "report_date": data.get("report_date"),
                    "pe_ratio": data.get("pe_ratio"),
                    "forward_pe": data.get("forward_pe"),
                    "pb_ratio": data.get("pb_ratio"),
                    "ps_ratio": data.get("ps_ratio"),
                    "peg_ratio": data.get("peg_ratio"),
                    "eps": data.get("eps"),
                    "forward_eps": data.get("forward_eps"),
                    "roe": data.get("roe"),
                    "roa": data.get("roa"),
                    "revenue": data.get("revenue"),
                    "revenue_growth": data.get("revenue_growth"),
                    "gross_margin": data.get("gross_margin"),
                    "operating_margin": data.get("operating_margin"),
                    "net_margin": data.get("net_margin"),
                    "market_cap": data.get("market_cap"),
                    "enterprise_value": data.get("enterprise_value"),
                    "dividend_yield": data.get("dividend_yield"),
                    "beta": data.get("beta"),
                    "52_week_high": data.get("52_week_high"),
                    "52_week_low": data.get("52_week_low"),
                }
            return None
        except Exception as e:
            print(f"Error getting US fundamentals for {stock_id}: {e}")
            return None

    async def _get_tw_fundamentals(self, db: Session, stock_id: str) -> Optional[Dict]:
        """取得台股基本面數據 (from FinMind)"""
        try:
            # Check cache in database first
            cached = (
                db.query(StockFundamental)
                .filter(StockFundamental.stock_id == stock_id)
                .order_by(desc(StockFundamental.report_date))
                .first()
            )

            # If cached data is recent (within 1 day), use it
            if cached and cached.updated_at:
                if datetime.now() - cached.updated_at < timedelta(days=1):
                    return self._fundamental_to_dict(cached)

            # Fetch from FinMind
            end_date = date.today()
            start_date = end_date - timedelta(days=365)

            # Get P/E, P/B ratio
            per_data = self.finmind.get_per_pbr(
                stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )

            # Get financial statements for EPS, margins
            fs_data = self.finmind.get_financial_statements(
                stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )

            result = {
                "stock_id": stock_id,
                "report_date": end_date.isoformat(),
                "pe_ratio": None,
                "pb_ratio": None,
                "eps": None,
                "roe": None,
                "roa": None,
                "revenue": None,
                "gross_margin": None,
                "operating_margin": None,
                "net_margin": None,
                "market_cap": None,
                "dividend_yield": None,
            }

            # Parse P/E, P/B data
            if per_data is not None and len(per_data) > 0:
                latest = per_data.iloc[-1]
                result["pe_ratio"] = float(latest.get("PER", 0)) if latest.get("PER") else None
                result["pb_ratio"] = float(latest.get("PBR", 0)) if latest.get("PBR") else None
                result["dividend_yield"] = float(latest.get("dividend_yield", 0)) if latest.get("dividend_yield") else None

            # Parse financial statement data
            if fs_data is not None and len(fs_data) > 0:
                # Get EPS
                eps_rows = fs_data[fs_data['type'] == 'EPS'] if 'type' in fs_data.columns else fs_data
                if len(eps_rows) > 0:
                    result["eps"] = float(eps_rows.iloc[-1].get("value", 0)) if eps_rows.iloc[-1].get("value") else None

                # Get ROE
                roe_rows = fs_data[fs_data['type'] == 'ROE'] if 'type' in fs_data.columns else None
                if roe_rows is not None and len(roe_rows) > 0:
                    result["roe"] = float(roe_rows.iloc[-1].get("value", 0))

                # Get revenue
                rev_rows = fs_data[fs_data['type'] == 'Revenue'] if 'type' in fs_data.columns else None
                if rev_rows is not None and len(rev_rows) > 0:
                    result["revenue"] = float(rev_rows.iloc[-1].get("value", 0))

            # Save to database for caching
            self._save_fundamental(db, result)

            return result

        except Exception as e:
            print(f"Error getting TW fundamentals for {stock_id}: {e}")
            return None

    def _fundamental_to_dict(self, f: StockFundamental) -> Dict:
        """Convert StockFundamental model to dict"""
        return {
            "stock_id": f.stock_id,
            "report_date": f.report_date.isoformat() if f.report_date else None,
            "pe_ratio": float(f.pe_ratio) if f.pe_ratio else None,
            "pb_ratio": float(f.pb_ratio) if f.pb_ratio else None,
            "ps_ratio": float(f.ps_ratio) if f.ps_ratio else None,
            "eps": float(f.eps) if f.eps else None,
            "roe": float(f.roe) if f.roe else None,
            "roa": float(f.roa) if f.roa else None,
            "revenue": float(f.revenue) if f.revenue else None,
            "gross_margin": float(f.gross_margin) if f.gross_margin else None,
            "operating_margin": float(f.operating_margin) if f.operating_margin else None,
            "net_margin": float(f.net_margin) if f.net_margin else None,
            "market_cap": float(f.market_cap) if f.market_cap else None,
        }

    def _save_fundamental(self, db: Session, data: Dict):
        """Save fundamental data to database"""
        try:
            existing = (
                db.query(StockFundamental)
                .filter(
                    StockFundamental.stock_id == data["stock_id"],
                    StockFundamental.report_date == data.get("report_date")
                )
                .first()
            )

            if existing:
                for key, value in data.items():
                    if hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
            else:
                fundamental = StockFundamental(
                    stock_id=data["stock_id"],
                    report_date=data.get("report_date"),
                    pe_ratio=data.get("pe_ratio"),
                    pb_ratio=data.get("pb_ratio"),
                    eps=data.get("eps"),
                    roe=data.get("roe"),
                    roa=data.get("roa"),
                    revenue=data.get("revenue"),
                    gross_margin=data.get("gross_margin"),
                    operating_margin=data.get("operating_margin"),
                    net_margin=data.get("net_margin"),
                    market_cap=data.get("market_cap"),
                )
                db.add(fundamental)

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error saving fundamental data: {e}")

    async def get_financial_statements(self, db: Session, stock_id: str, market: str = "TW") -> Optional[Dict]:
        """
        取得財務報表 (損益表、資產負債表、現金流量表)

        Args:
            db: Database session
            stock_id: Stock ID/Symbol
            market: 'TW' for Taiwan stocks, 'US' for US stocks

        Returns:
            Dict with income_statement, balance_sheet, cash_flow arrays
        """
        if market == "US":
            return self._get_us_financial_statements(stock_id)
        else:
            return await self._get_tw_financial_statements(db, stock_id)

    def _get_us_financial_statements(self, stock_id: str) -> Optional[Dict]:
        """取得美股財務報表"""
        try:
            return self.us_fetcher.get_financial_statements(stock_id)
        except Exception as e:
            print(f"Error getting US financial statements for {stock_id}: {e}")
            return None

    async def _get_tw_financial_statements(self, db: Session, stock_id: str) -> Optional[Dict]:
        """取得台股財務報表"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=365 * 3)  # Last 3 years

            fs_data = self.finmind.get_financial_statements(
                stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )

            if fs_data is None or len(fs_data) == 0:
                return {"stock_id": stock_id, "income_statement": [], "balance_sheet": [], "cash_flow": []}

            result = {
                "stock_id": stock_id,
                "income_statement": [],
                "balance_sheet": [],
                "cash_flow": [],
            }

            # Group by date and organize
            if 'date' in fs_data.columns and 'type' in fs_data.columns:
                grouped = fs_data.groupby('date')
                for date_str, group in grouped:
                    income_data = {}
                    balance_data = {}
                    cashflow_data = {}

                    for _, row in group.iterrows():
                        metric_type = row.get('type', '')
                        value = row.get('value', 0)

                        # Income statement items
                        if metric_type in ['Revenue', 'GrossProfit', 'OperatingIncome', 'NetIncome', 'EPS']:
                            income_data[metric_type.lower()] = float(value) if value else None

                        # Balance sheet items
                        elif metric_type in ['TotalAssets', 'TotalLiabilities', 'TotalEquity']:
                            balance_data[metric_type.lower()] = float(value) if value else None

                        # Cash flow items
                        elif metric_type in ['OperatingCashFlow', 'InvestingCashFlow', 'FinancingCashFlow']:
                            cashflow_data[metric_type.lower()] = float(value) if value else None

                    if income_data:
                        income_data['period'] = str(date_str)
                        result['income_statement'].append(income_data)

                    if balance_data:
                        balance_data['period'] = str(date_str)
                        result['balance_sheet'].append(balance_data)

                    if cashflow_data:
                        cashflow_data['period'] = str(date_str)
                        result['cash_flow'].append(cashflow_data)

            return result

        except Exception as e:
            print(f"Error getting TW financial statements for {stock_id}: {e}")
            return None

    async def get_dividends(self, db: Session, stock_id: str, market: str = "TW") -> List[Dict]:
        """
        取得股息歷史

        Args:
            db: Database session
            stock_id: Stock ID/Symbol
            market: 'TW' for Taiwan stocks, 'US' for US stocks

        Returns:
            List of dividend records by year
        """
        if market == "US":
            return self._get_us_dividends(stock_id)
        else:
            return await self._get_tw_dividends(db, stock_id)

    def _get_us_dividends(self, stock_id: str) -> List[Dict]:
        """取得美股股息歷史"""
        try:
            return self.us_fetcher.get_dividends(stock_id)
        except Exception as e:
            print(f"Error getting US dividends for {stock_id}: {e}")
            return []

    async def _get_tw_dividends(self, db: Session, stock_id: str) -> List[Dict]:
        """取得台股股息歷史"""
        try:
            # Fetch from FinMind (always get fresh data)
            end_date = date.today()
            start_date = end_date - timedelta(days=365 * 10)  # Last 10 years

            div_data = self.finmind.get_dividend(
                stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )

            if div_data is None or len(div_data) == 0:
                # Fall back to cache
                cached = (
                    db.query(StockDividend)
                    .filter(StockDividend.stock_id == stock_id)
                    .order_by(desc(StockDividend.year))
                    .all()
                )
                if cached:
                    return [
                        {
                            "stock_id": d.stock_id,
                            "year": d.year,
                            "cash_dividend": float(d.cash_dividend) if d.cash_dividend else 0,
                            "stock_dividend": float(d.stock_dividend) if d.stock_dividend else 0,
                            "total_dividend": float(d.total_dividend) if d.total_dividend else 0,
                            "ex_dividend_date": d.ex_dividend_date.isoformat() if d.ex_dividend_date else None,
                            "payment_date": d.payment_date.isoformat() if d.payment_date else None,
                            "dividend_yield": float(d.dividend_yield) if d.dividend_yield else None,
                        }
                        for d in cached
                    ]
                return []

            # Group by year and aggregate dividends
            # Columns: date, stock_id, year, StockEarningsDistribution, StockStatutorySurplus,
            #          CashEarningsDistribution, CashStatutorySurplus, CashExDividendTradingDate, CashDividendPaymentDate
            year_dividends = {}

            for _, row in div_data.iterrows():
                # Extract year from date (YYYY-MM-DD format) or announcement date
                date_str = str(row.get('date', ''))
                ex_div_date = str(row.get('CashExDividendTradingDate', '')) or ''

                # Determine the year - prefer ex-dividend date year
                if ex_div_date and len(ex_div_date) >= 4:
                    year = int(ex_div_date[:4])
                elif date_str and len(date_str) >= 4:
                    year = int(date_str[:4])
                else:
                    continue

                cash_div = float(row.get('CashEarningsDistribution', 0) or 0) + \
                           float(row.get('CashStatutorySurplus', 0) or 0)
                stock_div = float(row.get('StockEarningsDistribution', 0) or 0) + \
                            float(row.get('StockStatutorySurplus', 0) or 0)

                if year not in year_dividends:
                    year_dividends[year] = {
                        "stock_id": stock_id,
                        "year": year,
                        "cash_dividend": 0.0,
                        "stock_dividend": 0.0,
                        "total_dividend": 0.0,
                        "ex_dividend_date": ex_div_date if ex_div_date else None,
                        "payment_date": str(row.get('CashDividendPaymentDate', '')) or None,
                        "dividend_yield": None,
                    }

                # Accumulate dividends for the year (company may pay multiple times)
                year_dividends[year]["cash_dividend"] += cash_div
                year_dividends[year]["stock_dividend"] += stock_div
                year_dividends[year]["total_dividend"] += cash_div + stock_div

                # Update ex-dividend date to latest
                if ex_div_date:
                    year_dividends[year]["ex_dividend_date"] = ex_div_date

            # Convert to list and sort by year descending
            results = []
            for year in sorted(year_dividends.keys(), reverse=True):
                record = year_dividends[year]
                # Round to 2 decimal places
                record["cash_dividend"] = round(record["cash_dividend"], 2)
                record["stock_dividend"] = round(record["stock_dividend"], 2)
                record["total_dividend"] = round(record["total_dividend"], 2)
                results.append(record)

                # Save to database
                self._save_dividend(db, record)

            return results

        except Exception as e:
            print(f"Error getting TW dividends for {stock_id}: {e}")
            return []

    def _save_dividend(self, db: Session, data: Dict):
        """Save dividend data to database"""
        try:
            existing = (
                db.query(StockDividend)
                .filter(
                    StockDividend.stock_id == data["stock_id"],
                    StockDividend.year == data["year"]
                )
                .first()
            )

            if not existing:
                dividend = StockDividend(
                    stock_id=data["stock_id"],
                    year=data["year"],
                    cash_dividend=data.get("cash_dividend"),
                    stock_dividend=data.get("stock_dividend"),
                    total_dividend=data.get("total_dividend"),
                    dividend_yield=data.get("dividend_yield"),
                )
                db.add(dividend)
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error saving dividend data: {e}")

    async def get_institutional_trading(self, db: Session, stock_id: str, days: int = 30) -> List[Dict]:
        """
        取得法人買賣超 (台股專用)

        Args:
            db: Database session
            stock_id: Stock ID
            days: Number of days to retrieve

        Returns:
            List of institutional trading records
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Fetch from FinMind (always get fresh data for accuracy)
            inst_data = self.finmind.get_institutional_investors(
                stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )

            if inst_data is None or len(inst_data) == 0:
                # Fall back to cache
                cached = (
                    db.query(InstitutionalTrading)
                    .filter(
                        InstitutionalTrading.stock_id == stock_id,
                        InstitutionalTrading.date >= start_date
                    )
                    .order_by(desc(InstitutionalTrading.date))
                    .all()
                )
                if cached:
                    return [
                        {
                            "date": t.date.isoformat(),
                            "foreign_buy": t.foreign_buy or 0,
                            "foreign_sell": t.foreign_sell or 0,
                            "foreign_net": t.foreign_net or 0,
                            "trust_buy": t.trust_buy or 0,
                            "trust_sell": t.trust_sell or 0,
                            "trust_net": t.trust_net or 0,
                            "dealer_buy": t.dealer_buy or 0,
                            "dealer_sell": t.dealer_sell or 0,
                            "dealer_net": t.dealer_net or 0,
                            "total_net": t.total_net or 0,
                        }
                        for t in cached
                    ]
                return []

            # FinMind returns data with each row being one investor type per date
            # We need to pivot by date and aggregate by investor type
            # Columns: date, stock_id, buy, name, sell
            # name values: Foreign_Investor, Investment_Trust, Dealer_self, Dealer_Hedging

            date_records = {}
            for _, row in inst_data.iterrows():
                date_str = str(row.get('date', ''))
                if not date_str:
                    continue

                if date_str not in date_records:
                    date_records[date_str] = {
                        "date": date_str,
                        "foreign_buy": 0, "foreign_sell": 0, "foreign_net": 0,
                        "trust_buy": 0, "trust_sell": 0, "trust_net": 0,
                        "dealer_buy": 0, "dealer_sell": 0, "dealer_net": 0,
                        "total_net": 0,
                    }

                name = row.get('name', '')
                buy = int(row.get('buy', 0) or 0)
                sell = int(row.get('sell', 0) or 0)
                net = buy - sell

                if name == 'Foreign_Investor':
                    date_records[date_str]["foreign_buy"] = buy
                    date_records[date_str]["foreign_sell"] = sell
                    date_records[date_str]["foreign_net"] = net
                elif name == 'Investment_Trust':
                    date_records[date_str]["trust_buy"] = buy
                    date_records[date_str]["trust_sell"] = sell
                    date_records[date_str]["trust_net"] = net
                elif name in ['Dealer_self', 'Dealer_Hedging']:
                    # Combine dealer self and hedging
                    date_records[date_str]["dealer_buy"] += buy
                    date_records[date_str]["dealer_sell"] += sell
                    date_records[date_str]["dealer_net"] += net

            # Calculate total and sort by date descending
            results = []
            for date_str in sorted(date_records.keys(), reverse=True):
                record = date_records[date_str]
                record["total_net"] = record["foreign_net"] + record["trust_net"] + record["dealer_net"]
                results.append(record)

                # Save to database
                self._save_institutional(db, stock_id, record)

            return results

        except Exception as e:
            print(f"Error getting institutional trading for {stock_id}: {e}")
            return []

    def _save_institutional(self, db: Session, stock_id: str, data: Dict):
        """Save institutional trading data to database"""
        try:
            date_str = data.get("date", "")
            if not date_str:
                return

            trade_date = datetime.strptime(date_str, "%Y-%m-%d").date() if isinstance(date_str, str) else date_str

            existing = (
                db.query(InstitutionalTrading)
                .filter(
                    InstitutionalTrading.stock_id == stock_id,
                    InstitutionalTrading.date == trade_date
                )
                .first()
            )

            if not existing:
                trading = InstitutionalTrading(
                    stock_id=stock_id,
                    date=trade_date,
                    foreign_buy=data.get("foreign_buy"),
                    foreign_sell=data.get("foreign_sell"),
                    foreign_net=data.get("foreign_net"),
                    trust_buy=data.get("trust_buy"),
                    trust_sell=data.get("trust_sell"),
                    trust_net=data.get("trust_net"),
                    dealer_buy=data.get("dealer_buy"),
                    dealer_sell=data.get("dealer_sell"),
                    dealer_net=data.get("dealer_net"),
                    total_net=data.get("total_net"),
                )
                db.add(trading)
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error saving institutional data: {e}")

    async def get_margin_trading(self, db: Session, stock_id: str, days: int = 30) -> List[Dict]:
        """
        取得融資融券 (台股專用)

        Args:
            db: Database session
            stock_id: Stock ID
            days: Number of days to retrieve

        Returns:
            List of margin trading records
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            # Check cache first
            cached = (
                db.query(MarginTrading)
                .filter(
                    MarginTrading.stock_id == stock_id,
                    MarginTrading.date >= start_date
                )
                .order_by(desc(MarginTrading.date))
                .all()
            )

            if cached and len(cached) >= days * 0.5:
                return [
                    {
                        "date": m.date.isoformat(),
                        "margin_buy": m.margin_buy,
                        "margin_sell": m.margin_sell,
                        "margin_balance": m.margin_balance,
                        "margin_limit": m.margin_limit,
                        "margin_utilization": float(m.margin_utilization) if m.margin_utilization else None,
                        "short_sell": m.short_sell,
                        "short_buy": m.short_buy,
                        "short_balance": m.short_balance,
                    }
                    for m in cached
                ]

            # Fetch from FinMind
            margin_data = self.finmind.get_margin_trading(
                stock_id, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )

            if margin_data is None or len(margin_data) == 0:
                return []

            results = []
            for _, row in margin_data.iterrows():
                record = {
                    "date": str(row.get('date', '')),
                    "margin_buy": int(row.get('MarginPurchaseBuy', 0) or 0),
                    "margin_sell": int(row.get('MarginPurchaseSell', 0) or 0),
                    "margin_balance": int(row.get('MarginPurchaseTodayBalance', 0) or 0),
                    "margin_limit": int(row.get('MarginPurchaseLimit', 0) or 0),
                    "margin_utilization": None,
                    "short_sell": int(row.get('ShortSaleSell', 0) or 0),
                    "short_buy": int(row.get('ShortSaleBuy', 0) or 0),
                    "short_balance": int(row.get('ShortSaleTodayBalance', 0) or 0),
                }

                # Calculate utilization
                if record["margin_limit"] and record["margin_limit"] > 0:
                    record["margin_utilization"] = round(
                        record["margin_balance"] / record["margin_limit"] * 100, 2
                    )

                results.append(record)

                # Save to database
                self._save_margin(db, stock_id, record)

            return results

        except Exception as e:
            print(f"Error getting margin trading for {stock_id}: {e}")
            return []

    def _save_margin(self, db: Session, stock_id: str, data: Dict):
        """Save margin trading data to database"""
        try:
            date_str = data.get("date", "")
            if not date_str:
                return

            trade_date = datetime.strptime(date_str, "%Y-%m-%d").date() if isinstance(date_str, str) else date_str

            existing = (
                db.query(MarginTrading)
                .filter(
                    MarginTrading.stock_id == stock_id,
                    MarginTrading.date == trade_date
                )
                .first()
            )

            if not existing:
                margin = MarginTrading(
                    stock_id=stock_id,
                    date=trade_date,
                    margin_buy=data.get("margin_buy"),
                    margin_sell=data.get("margin_sell"),
                    margin_balance=data.get("margin_balance"),
                    margin_limit=data.get("margin_limit"),
                    margin_utilization=data.get("margin_utilization"),
                    short_sell=data.get("short_sell"),
                    short_buy=data.get("short_buy"),
                    short_balance=data.get("short_balance"),
                )
                db.add(margin)
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error saving margin data: {e}")


# Global service instance
fundamental_service = FundamentalService()
