"""
US Stock Data Fetcher using Yahoo Finance (yfinance)
"""
import yfinance as yf
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)


class USStockFetcher:
    """
    US Stock Data Fetcher using Yahoo Finance API

    Features:
    - Real-time quotes
    - Historical price data
    - Company info
    - News
    - Stock search
    """

    # Popular US stocks for initialization
    POPULAR_STOCKS = [
        "AAPL", "GOOGL", "GOOG", "MSFT", "AMZN", "TSLA", "META", "NVDA",
        "BRK-B", "JPM", "JNJ", "V", "PG", "UNH", "HD", "MA", "DIS", "PYPL",
        "NFLX", "ADBE", "CRM", "INTC", "AMD", "QCOM", "TXN", "AVGO",
        "PEP", "KO", "MCD", "NKE", "SBUX", "WMT", "COST", "TGT",
        "BAC", "WFC", "GS", "MS", "C", "AXP",
        "XOM", "CVX", "COP", "SLB",
        "PFE", "MRK", "ABBV", "LLY", "BMY",
        "BA", "CAT", "GE", "MMM", "HON",
        "UBER", "LYFT", "ABNB", "DASH", "COIN", "RBLX", "PLTR", "SNOW",
        "SPY", "QQQ", "DIA", "IWM", "VTI"
    ]

    def __init__(self):
        self.last_request_time = 0
        self.request_interval = 0.5  # Rate limiting
        self._cache = {}
        self._cache_ttl = 60  # Cache for 60 seconds

    def _rate_limit(self):
        """Simple rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """Get yfinance Ticker object with caching"""
        cache_key = f"ticker_{symbol}"
        now = time.time()

        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return cached_data

        ticker = yf.Ticker(symbol)
        self._cache[cache_key] = (ticker, now)
        return ticker

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get stock basic information"""
        self._rate_limit()

        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info

            if not info or info.get('regularMarketPrice') is None:
                return None

            return {
                "stock_id": symbol.upper(),
                "symbol": symbol.upper(),
                "name": info.get("shortName", info.get("longName", symbol)),
                "long_name": info.get("longName", ""),
                "industry": info.get("industry", ""),
                "sector": info.get("sector", ""),
                "exchange": info.get("exchange", ""),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "dividend_yield": info.get("dividendYield"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "currency": info.get("currency", "USD"),
                "country": info.get("country", "United States"),
                "website": info.get("website", ""),
                "description": info.get("longBusinessSummary", ""),
                "market_region": "US"
            }
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {e}")
            return None

    def get_realtime_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time quote for a single stock"""
        self._rate_limit()

        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info

            if not info:
                return None

            current_price = info.get('regularMarketPrice', 0) or info.get('currentPrice', 0)
            previous_close = info.get('regularMarketPreviousClose', 0) or info.get('previousClose', 0)

            if not current_price:
                # Try fast_info as fallback
                try:
                    fast_info = ticker.fast_info
                    current_price = fast_info.get('lastPrice', 0)
                    previous_close = fast_info.get('previousClose', 0)
                except Exception as e:
                    logger.warning(f"fast_info fallback failed for {symbol}: {e}")

            if not current_price:
                return None

            change = current_price - previous_close if previous_close else 0
            change_percent = (change / previous_close * 100) if previous_close else 0

            return {
                "stock_id": symbol.upper(),
                "symbol": symbol.upper(),
                "name": info.get("shortName", info.get("longName", symbol)),
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "open": round(info.get("regularMarketOpen", 0) or 0, 2),
                "high": round(info.get("regularMarketDayHigh", 0) or 0, 2),
                "low": round(info.get("regularMarketDayLow", 0) or 0, 2),
                "volume": info.get("regularMarketVolume", 0) or 0,
                "previous_close": round(previous_close, 2),
                "market_cap": info.get("marketCap", 0),
                "currency": info.get("currency", "USD"),
                "market_region": "US",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"Error fetching realtime quote for {symbol}: {e}")
            return None

    def get_realtime_quotes_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        批量取得美股即時報價（使用 yf.download 一次取得所有股票）
        比逐一查詢快 5-10 倍
        """
        if not symbols:
            return {}

        results = {}
        try:
            # yf.download 支援批量，一次 HTTP 取得所有股票
            data = yf.download(
                symbols,
                period="2d",
                group_by="ticker" if len(symbols) > 1 else "column",
                progress=False,
                threads=True,
            )

            if data.empty:
                return {}

            for symbol in symbols:
                try:
                    if len(symbols) > 1:
                        stock_data = data[symbol] if symbol in data.columns.get_level_values(0) else None
                    else:
                        stock_data = data

                    if stock_data is None or stock_data.empty:
                        continue

                    # 取最後兩筆計算漲跌
                    stock_data = stock_data.dropna(subset=['Close'])
                    if len(stock_data) < 1:
                        continue

                    latest = stock_data.iloc[-1]
                    prev_close = float(stock_data.iloc[-2]['Close']) if len(stock_data) >= 2 else 0
                    current_price = float(latest['Close'])

                    if current_price <= 0:
                        continue

                    change = current_price - prev_close if prev_close > 0 else 0
                    change_percent = (change / prev_close * 100) if prev_close > 0 else 0

                    results[symbol] = {
                        "stock_id": symbol.upper(),
                        "symbol": symbol.upper(),
                        "name": symbol.upper(),
                        "price": round(current_price, 2),
                        "change": round(change, 2),
                        "change_percent": round(change_percent, 2),
                        "open": round(float(latest.get('Open', 0) or 0), 2),
                        "high": round(float(latest.get('High', 0) or 0), 2),
                        "low": round(float(latest.get('Low', 0) or 0), 2),
                        "volume": int(latest.get('Volume', 0) or 0),
                        "previous_close": round(prev_close, 2),
                        "currency": "USD",
                        "market_region": "US",
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                except Exception as e:
                    logger.warning(f"解析 {symbol} 批量數據失敗: {e}")

        except Exception as e:
            logger.error(f"yfinance 批量下載失敗: {e}")
            # 降級為逐一查詢
            for symbol in symbols:
                quote = self.get_realtime_quote(symbol)
                if quote:
                    results[symbol] = quote

        return results

    def get_realtime_quotes(self, symbols: List[str]) -> List[Dict]:
        """Get real-time quotes for multiple stocks"""
        results = []
        for symbol in symbols:
            quote = self.get_realtime_quote(symbol)
            if quote:
                results.append(quote)
        return results

    def get_stock_price(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "1mo"
    ) -> List[Dict]:
        """
        Get historical price data (K-line data)

        Args:
            symbol: Stock symbol (e.g., AAPL)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

        Returns:
            List of OHLCV data
        """
        self._rate_limit()

        try:
            ticker = self._get_ticker(symbol)

            if start_date and end_date:
                hist = ticker.history(start=start_date, end=end_date)
            else:
                hist = ticker.history(period=period)

            if hist.empty:
                return []

            results = []
            for date, row in hist.iterrows():
                results.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]),
                    "stock_id": symbol.upper(),
                    "market_region": "US"
                })

            return results
        except Exception as e:
            logger.error(f"Error fetching price history for {symbol}: {e}")
            return []

    def search_stocks(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for US stocks by symbol or name

        Strategy:
        1. Try the query as a direct symbol first (supports any valid ticker)
        2. Use yfinance Search API for broader results
        3. Fallback to matching against popular stocks list
        """
        query = query.upper().strip()
        results = []
        seen_symbols = set()

        # 1. Always try the query as a direct symbol first
        if len(query) >= 1:
            info = self.get_stock_info(query)
            if info:
                results.append({
                    "stock_id": query,
                    "symbol": query,
                    "name": info.get("name", query),
                    "industry": info.get("industry", ""),
                    "exchange": info.get("exchange", ""),
                    "market_region": "US"
                })
                seen_symbols.add(query)

        # 2. Use yfinance Search API for broader results
        if len(results) < limit:
            try:
                search_result = yf.Search(query, max_results=limit)
                quotes = getattr(search_result, 'quotes', [])
                for q in quotes:
                    symbol = q.get('symbol', '').upper()
                    # 只包含美股（排除非美股交易所）
                    exchange = q.get('exchange', '')
                    exchDisp = q.get('exchDisp', '')
                    quoteType = q.get('quoteType', '')
                    # 排除台股、港股、日股等非美股
                    if any(x in exchange for x in ['TAI', 'HKG', 'TYO', 'SHH', 'SHZ', 'TWO']):
                        continue
                    if symbol and symbol not in seen_symbols:
                        results.append({
                            "stock_id": symbol,
                            "symbol": symbol,
                            "name": q.get('shortname', q.get('longname', symbol)),
                            "industry": q.get('industry', ''),
                            "exchange": exchDisp or exchange,
                            "market_region": "US"
                        })
                        seen_symbols.add(symbol)
                        if len(results) >= limit:
                            break
            except Exception as e:
                logger.warning(f"yfinance Search API failed for '{query}': {e}")

        # 3. Fallback: match against popular stocks list
        if len(results) < limit:
            for symbol in self.POPULAR_STOCKS:
                if query in symbol and symbol not in seen_symbols:
                    info = self.get_stock_info(symbol)
                    if info:
                        results.append({
                            "stock_id": symbol,
                            "symbol": symbol,
                            "name": info.get("name", symbol),
                            "industry": info.get("industry", ""),
                            "exchange": info.get("exchange", ""),
                            "market_region": "US"
                        })
                        seen_symbols.add(symbol)
                        if len(results) >= limit:
                            break

        return results[:limit]

    def get_company_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Get news for a specific stock"""
        self._rate_limit()

        try:
            ticker = self._get_ticker(symbol)
            news = ticker.news

            if not news:
                return []

            results = []
            for item in news[:limit]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "publisher": item.get("publisher", ""),
                    "published_at": datetime.fromtimestamp(
                        item.get("providerPublishTime", 0)
                    ).strftime("%Y-%m-%d %H:%M:%S") if item.get("providerPublishTime") else "",
                    "thumbnail": item.get("thumbnail", {}).get("resolutions", [{}])[0].get("url", "") if item.get("thumbnail") else "",
                    "stock_id": symbol.upper(),
                    "market_region": "US"
                })

            return results
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    def get_popular_stocks(self) -> List[Dict]:
        """Get list of popular US stocks with basic info"""
        results = []

        # Only fetch a subset for efficiency
        popular_subset = self.POPULAR_STOCKS[:30]

        for symbol in popular_subset:
            quote = self.get_realtime_quote(symbol)
            if quote:
                results.append(quote)

        return results

    def validate_symbol(self, symbol: str) -> bool:
        """Check if a symbol is valid"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info is not None and info.get('regularMarketPrice') is not None
        except Exception as e:
            logger.warning(f"Symbol validation failed for {symbol}: {e}")
            return False


# Global instance
us_stock_fetcher = USStockFetcher()


def get_us_stock_realtime_price(symbol: str) -> Optional[Dict]:
    """Convenience function to get real-time price for a US stock"""
    try:
        return us_stock_fetcher.get_realtime_quote(symbol)
    except Exception:
        return None


class USStockFundamentalFetcher:
    """
    US Stock Fundamental Data Fetcher using Yahoo Finance API
    Provides fundamental analysis, financial statements, and dividend data
    """

    def __init__(self):
        self.last_request_time = 0
        self.request_interval = 0.5
        self._cache = {}
        self._cache_ttl = 300  # Cache for 5 minutes

    def _rate_limit(self):
        """Simple rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """Get yfinance Ticker object"""
        return yf.Ticker(symbol)

    def get_fundamentals(self, symbol: str) -> Optional[Dict]:
        """
        Get comprehensive fundamental data for a US stock

        Returns:
            Dict containing PE, PB, EPS, ROE, revenue, margins, etc.
        """
        self._rate_limit()

        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info

            if not info:
                return None

            # Calculate ROE if not available directly
            roe = info.get('returnOnEquity')
            if roe:
                roe = round(roe * 100, 2)  # Convert to percentage

            # Calculate ROA if not available directly
            roa = info.get('returnOnAssets')
            if roa:
                roa = round(roa * 100, 2)  # Convert to percentage

            # Calculate gross margin
            gross_margin = info.get('grossMargins')
            if gross_margin:
                gross_margin = round(gross_margin * 100, 2)

            # Calculate operating margin
            operating_margin = info.get('operatingMargins')
            if operating_margin:
                operating_margin = round(operating_margin * 100, 2)

            # Calculate net margin
            net_margin = info.get('profitMargins')
            if net_margin:
                net_margin = round(net_margin * 100, 2)

            return {
                "stock_id": symbol.upper(),
                "report_date": datetime.now().strftime("%Y-%m-%d"),

                # Valuation metrics
                "pe_ratio": info.get('trailingPE'),
                "forward_pe": info.get('forwardPE'),
                "pb_ratio": info.get('priceToBook'),
                "ps_ratio": info.get('priceToSalesTrailing12Months'),
                "peg_ratio": info.get('pegRatio'),

                # Profitability metrics
                "eps": info.get('trailingEps'),
                "forward_eps": info.get('forwardEps'),
                "roe": roe,
                "roa": roa,

                # Revenue metrics
                "revenue": info.get('totalRevenue'),
                "revenue_growth": round(info.get('revenueGrowth', 0) * 100, 2) if info.get('revenueGrowth') else None,
                "gross_margin": gross_margin,
                "operating_margin": operating_margin,
                "net_margin": net_margin,

                # Market data
                "market_cap": info.get('marketCap'),
                "enterprise_value": info.get('enterpriseValue'),
                "book_value": info.get('bookValue'),

                # Dividend
                "dividend_yield": round(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else None,
                "dividend_rate": info.get('dividendRate'),

                # Additional info
                "beta": info.get('beta'),
                "52_week_high": info.get('fiftyTwoWeekHigh'),
                "52_week_low": info.get('fiftyTwoWeekLow'),
                "shares_outstanding": info.get('sharesOutstanding'),
            }
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return None

    def get_financial_statements(self, symbol: str) -> Optional[Dict]:
        """
        Get financial statements (Income, Balance Sheet, Cash Flow)

        Returns:
            Dict containing quarterly and annual financial data
        """
        self._rate_limit()

        try:
            ticker = self._get_ticker(symbol)

            result = {
                "stock_id": symbol.upper(),
                "income_statement": [],
                "balance_sheet": [],
                "cash_flow": []
            }

            # Get quarterly income statement
            try:
                income_quarterly = ticker.quarterly_income_stmt
                if income_quarterly is not None and not income_quarterly.empty:
                    for col in income_quarterly.columns[:4]:  # Last 4 quarters
                        data = income_quarterly[col]
                        result["income_statement"].append({
                            "period": col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col),
                            "revenue": self._safe_get(data, 'Total Revenue'),
                            "cost_of_revenue": self._safe_get(data, 'Cost Of Revenue'),
                            "gross_profit": self._safe_get(data, 'Gross Profit'),
                            "operating_expense": self._safe_get(data, 'Operating Expense'),
                            "operating_income": self._safe_get(data, 'Operating Income'),
                            "net_income": self._safe_get(data, 'Net Income'),
                            "ebitda": self._safe_get(data, 'EBITDA'),
                        })
            except Exception as e:
                logger.error(f"Error fetching income statement for {symbol}: {e}")

            # Get quarterly balance sheet
            try:
                balance_quarterly = ticker.quarterly_balance_sheet
                if balance_quarterly is not None and not balance_quarterly.empty:
                    for col in balance_quarterly.columns[:4]:
                        data = balance_quarterly[col]
                        result["balance_sheet"].append({
                            "period": col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col),
                            "total_assets": self._safe_get(data, 'Total Assets'),
                            "total_liabilities": self._safe_get(data, 'Total Liabilities Net Minority Interest'),
                            "total_equity": self._safe_get(data, 'Total Equity Gross Minority Interest'),
                            "current_assets": self._safe_get(data, 'Current Assets'),
                            "current_liabilities": self._safe_get(data, 'Current Liabilities'),
                            "cash": self._safe_get(data, 'Cash And Cash Equivalents'),
                            "total_debt": self._safe_get(data, 'Total Debt'),
                        })
            except Exception as e:
                logger.error(f"Error fetching balance sheet for {symbol}: {e}")

            # Get quarterly cash flow
            try:
                cashflow_quarterly = ticker.quarterly_cashflow
                if cashflow_quarterly is not None and not cashflow_quarterly.empty:
                    for col in cashflow_quarterly.columns[:4]:
                        data = cashflow_quarterly[col]
                        result["cash_flow"].append({
                            "period": col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col),
                            "operating_cash_flow": self._safe_get(data, 'Operating Cash Flow'),
                            "investing_cash_flow": self._safe_get(data, 'Investing Cash Flow'),
                            "financing_cash_flow": self._safe_get(data, 'Financing Cash Flow'),
                            "free_cash_flow": self._safe_get(data, 'Free Cash Flow'),
                            "capital_expenditure": self._safe_get(data, 'Capital Expenditure'),
                        })
            except Exception as e:
                logger.error(f"Error fetching cash flow for {symbol}: {e}")

            return result
        except Exception as e:
            logger.error(f"Error fetching financial statements for {symbol}: {e}")
            return None

    def _safe_get(self, data, key):
        """Safely get value from pandas Series"""
        try:
            if key in data.index:
                val = data[key]
                if val is not None and not (isinstance(val, float) and val != val):  # Check for NaN
                    return float(val)
        except Exception as e:
            logger.warning(f"Safe get failed for key '{key}': {e}")
        return None

    def get_dividends(self, symbol: str) -> List[Dict]:
        """
        Get dividend history for a US stock

        Returns:
            List of dividend payments
        """
        self._rate_limit()

        try:
            ticker = self._get_ticker(symbol)
            dividends = ticker.dividends

            if dividends is None or dividends.empty:
                return []

            results = []
            # Group by year for summary
            yearly_dividends = {}

            for date, amount in dividends.items():
                year = date.year
                if year not in yearly_dividends:
                    yearly_dividends[year] = {
                        "total": 0,
                        "payments": []
                    }
                yearly_dividends[year]["total"] += float(amount)
                yearly_dividends[year]["payments"].append({
                    "date": date.strftime("%Y-%m-%d"),
                    "amount": round(float(amount), 4)
                })

            # Convert to list format
            for year in sorted(yearly_dividends.keys(), reverse=True):
                data = yearly_dividends[year]
                results.append({
                    "stock_id": symbol.upper(),
                    "year": year,
                    "cash_dividend": round(data["total"], 4),
                    "stock_dividend": 0,  # US stocks typically don't have stock dividends
                    "total_dividend": round(data["total"], 4),
                    "payment_count": len(data["payments"]),
                    "payments": data["payments"][:4]  # Latest 4 payments for that year
                })

            return results[:10]  # Return last 10 years
        except Exception as e:
            logger.error(f"Error fetching dividends for {symbol}: {e}")
            return []

    def get_earnings_history(self, symbol: str) -> List[Dict]:
        """
        Get earnings history and estimates

        Returns:
            List of earnings data by quarter
        """
        self._rate_limit()

        try:
            ticker = self._get_ticker(symbol)

            # Get earnings dates
            try:
                earnings_dates = ticker.earnings_dates
                if earnings_dates is not None and not earnings_dates.empty:
                    results = []
                    for date, row in earnings_dates.head(8).iterrows():  # Last 8 quarters
                        results.append({
                            "date": date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date),
                            "eps_estimate": row.get('EPS Estimate'),
                            "eps_actual": row.get('Reported EPS'),
                            "surprise_percent": row.get('Surprise(%)'),
                        })
                    return results
            except Exception as e:
                logger.warning(f"Earnings dates fetch failed for {symbol}: {e}")

            return []
        except Exception as e:
            logger.error(f"Error fetching earnings for {symbol}: {e}")
            return []


# Global instance
us_fundamental_fetcher = USStockFundamentalFetcher()
