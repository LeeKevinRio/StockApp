"""
Global Financial News Fetcher
Fetches news from reliable global financial news sources for US/international stocks
Uses yfinance API as primary source (most reliable)
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
import time
import logging

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

logger = logging.getLogger(__name__)


class GlobalNewsFetcher:
    """
    Global Financial News Fetcher

    Primary Source (most reliable):
    - yfinance API (Yahoo Finance data)

    Fallback Sources:
    - Yahoo Finance (web scraping)
    - MarketWatch
    - Seeking Alpha
    - Benzinga
    """

    # Sentiment keywords for English news
    POSITIVE_KEYWORDS = [
        "surge", "soar", "rally", "jump", "gain", "rise", "climb", "beat",
        "exceed", "outperform", "upgrade", "bullish", "strong", "growth",
        "profit", "record", "breakthrough", "innovative", "expand", "win",
        "success", "positive", "optimistic", "confident", "boost", "recover",
        "high", "peak", "best", "top", "leading", "buy rating", "overweight",
    ]

    NEGATIVE_KEYWORDS = [
        "plunge", "crash", "drop", "fall", "decline", "slip", "tumble", "miss",
        "disappoint", "underperform", "downgrade", "bearish", "weak", "loss",
        "warning", "concern", "risk", "threat", "lawsuit", "investigation",
        "negative", "pessimistic", "worried", "cut", "reduce", "layoff",
        "low", "worst", "bottom", "sell rating", "underweight", "bankrupt",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.last_request_time = 0
        self.request_interval = 1.0

    def _rate_limit(self):
        """Simple rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of English text"""
        text_lower = text.lower()

        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)

        total = positive_count + negative_count
        if total == 0:
            return {"sentiment": "neutral", "score": 0.0}

        score = (positive_count - negative_count) / total

        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {"sentiment": sentiment, "score": round(score, 2)}

    def _parse_relative_time(self, time_str: str) -> Optional[datetime]:
        """Parse relative time strings like '2 hours ago'"""
        if not time_str:
            return None

        time_str = time_str.lower().strip()
        now = datetime.now()

        patterns = [
            (r'(\d+)\s*min', lambda m: now - timedelta(minutes=int(m.group(1)))),
            (r'(\d+)\s*hour', lambda m: now - timedelta(hours=int(m.group(1)))),
            (r'(\d+)\s*day', lambda m: now - timedelta(days=int(m.group(1)))),
            (r'(\d+)\s*week', lambda m: now - timedelta(weeks=int(m.group(1)))),
            (r'yesterday', lambda m: now - timedelta(days=1)),
            (r'today', lambda m: now),
        ]

        for pattern, func in patterns:
            match = re.search(pattern, time_str)
            if match:
                return func(match)

        return None

    def fetch_yahoo_finance_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Fetch news from Yahoo Finance"""
        self._rate_limit()

        url = f"https://finance.yahoo.com/quote/{ticker}/news"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []

            # Find news items
            articles = soup.find_all('li', class_=re.compile(r'stream-item'))[:limit]

            if not articles:
                # Try alternative selectors
                articles = soup.find_all('div', {'data-testid': 'news-stream'})
                if articles:
                    articles = articles[0].find_all('li')[:limit]

            for article in articles:
                try:
                    # Extract title and link
                    link_elem = article.find('a', href=True)
                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue

                    href = link_elem.get('href', '')
                    if href.startswith('/'):
                        href = f"https://finance.yahoo.com{href}"

                    # Extract source and time
                    source = "Yahoo Finance"
                    source_elem = article.find('span', class_=re.compile(r'provider'))
                    if source_elem:
                        source = source_elem.get_text(strip=True)

                    time_elem = article.find('span', class_=re.compile(r'time|ago'))
                    published_at = None
                    if time_elem:
                        published_at = self._parse_relative_time(time_elem.get_text())

                    sentiment_data = self._analyze_sentiment(title)

                    news_items.append({
                        "title": title,
                        "summary": "",
                        "source": source,
                        "url": href,
                        "published_at": published_at.isoformat() if published_at else None,
                        "sentiment": sentiment_data["sentiment"],
                        "sentiment_score": sentiment_data["score"],
                        "stock_id": ticker,
                        "market_region": "US",
                    })
                except Exception as e:
                    continue

            return news_items

        except Exception as e:
            logger.error(f"Yahoo Finance news error for {ticker}: {e}")
            return []

    def fetch_marketwatch_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Fetch news from MarketWatch"""
        self._rate_limit()

        url = f"https://www.marketwatch.com/investing/stock/{ticker.lower()}"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []

            # Find news section
            articles = soup.find_all('div', class_=re.compile(r'article__content'))[:limit]

            for article in articles:
                try:
                    link_elem = article.find('a', class_=re.compile(r'link'))
                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    if not title:
                        continue

                    href = link_elem.get('href', '')
                    if not href.startswith('http'):
                        href = f"https://www.marketwatch.com{href}"

                    sentiment_data = self._analyze_sentiment(title)

                    news_items.append({
                        "title": title,
                        "summary": "",
                        "source": "MarketWatch",
                        "url": href,
                        "published_at": None,
                        "sentiment": sentiment_data["sentiment"],
                        "sentiment_score": sentiment_data["score"],
                        "stock_id": ticker,
                        "market_region": "US",
                    })
                except Exception:
                    continue

            return news_items

        except Exception as e:
            logger.error(f"MarketWatch news error for {ticker}: {e}")
            return []

    def fetch_seeking_alpha_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Fetch news/analysis from Seeking Alpha"""
        self._rate_limit()

        url = f"https://seekingalpha.com/symbol/{ticker}/news"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []

            # Find article links
            articles = soup.find_all('article')[:limit]

            for article in articles:
                try:
                    link_elem = article.find('a', {'data-test-id': 'post-list-item-title'})
                    if not link_elem:
                        link_elem = article.find('a', href=True)

                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue

                    href = link_elem.get('href', '')
                    if href.startswith('/'):
                        href = f"https://seekingalpha.com{href}"

                    sentiment_data = self._analyze_sentiment(title)

                    news_items.append({
                        "title": title,
                        "summary": "",
                        "source": "Seeking Alpha",
                        "url": href,
                        "published_at": None,
                        "sentiment": sentiment_data["sentiment"],
                        "sentiment_score": sentiment_data["score"],
                        "stock_id": ticker,
                        "market_region": "US",
                    })
                except Exception:
                    continue

            return news_items

        except Exception as e:
            logger.error(f"Seeking Alpha news error for {ticker}: {e}")
            return []

    def fetch_benzinga_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Fetch news from Benzinga"""
        self._rate_limit()

        url = f"https://www.benzinga.com/stock/{ticker.lower()}"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []

            # Find news articles
            articles = soup.find_all('div', class_=re.compile(r'content-title'))[:limit]

            for article in articles:
                try:
                    link_elem = article.find('a', href=True)
                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    if not title:
                        continue

                    href = link_elem.get('href', '')
                    if not href.startswith('http'):
                        href = f"https://www.benzinga.com{href}"

                    sentiment_data = self._analyze_sentiment(title)

                    news_items.append({
                        "title": title,
                        "summary": "",
                        "source": "Benzinga",
                        "url": href,
                        "published_at": None,
                        "sentiment": sentiment_data["sentiment"],
                        "sentiment_score": sentiment_data["score"],
                        "stock_id": ticker,
                        "market_region": "US",
                    })
                except Exception:
                    continue

            return news_items

        except Exception as e:
            logger.error(f"Benzinga news error for {ticker}: {e}")
            return []

    def fetch_yfinance_news(self, ticker: str, limit: int = 15) -> List[Dict]:
        """
        Fetch news using yfinance API (most reliable method)
        """
        if not YFINANCE_AVAILABLE:
            logger.warning("yfinance not available")
            return []

        news_items = []

        try:
            stock = yf.Ticker(ticker)
            news_data = stock.news

            if not news_data:
                logger.info(f"No news from yfinance for {ticker}")
                return []

            logger.info(f"yfinance returned {len(news_data)} news items for {ticker}")

            for item in news_data[:limit]:
                # Handle new yfinance structure where data is nested under 'content'
                content = item.get("content", item)  # Fallback to item if no content key

                title = content.get("title", "")
                if not title:
                    continue

                # Parse timestamp - try multiple formats
                published_at = None
                # Try new format: pubDate as ISO string
                pub_date = content.get("pubDate") or content.get("displayTime")
                if pub_date and isinstance(pub_date, str):
                    try:
                        # Parse ISO format: "2026-01-25T12:54:34Z"
                        published_at = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"yfinance news date ISO parse failed: {e}")
                # Try old format: providerPublishTime as timestamp
                if not published_at:
                    timestamp = item.get("providerPublishTime")
                    if timestamp:
                        try:
                            published_at = datetime.fromtimestamp(timestamp)
                        except Exception as e:
                            logger.warning(f"yfinance news timestamp parse failed: {e}")

                sentiment_data = self._analyze_sentiment(title)

                # Get the link - handle new structure
                url = ""
                canonical_url = content.get("canonicalUrl", {})
                if isinstance(canonical_url, dict):
                    url = canonical_url.get("url", "")
                if not url:
                    click_url = content.get("clickThroughUrl", {})
                    if isinstance(click_url, dict):
                        url = click_url.get("url", "")
                if not url:
                    url = item.get("link", "")
                if not url:
                    # Try to construct Yahoo Finance URL from id
                    news_id = item.get("id", "") or content.get("id", "")
                    if news_id:
                        url = f"https://finance.yahoo.com/news/{news_id}"

                # Get publisher/source
                provider = content.get("provider", {})
                source = provider.get("displayName", "Yahoo Finance") if isinstance(provider, dict) else "Yahoo Finance"

                # Get summary
                summary = content.get("summary", "") or content.get("description", "")

                news_items.append({
                    "title": title,
                    "summary": summary[:500] if summary else "",
                    "source": source,
                    "url": url,
                    "published_at": published_at.isoformat() if published_at else None,
                    "sentiment": sentiment_data["sentiment"],
                    "sentiment_score": sentiment_data["score"],
                    "stock_id": ticker,
                    "market_region": "US",
                })

        except Exception as e:
            logger.error(f"yfinance news error for {ticker}: {e}")

        return news_items

    def fetch_stock_news(self, ticker: str, limit: int = 15) -> List[Dict]:
        """
        Fetch news from multiple sources for a US stock

        Primary: yfinance API (most reliable)
        Fallback: Web scraping from multiple sources
        """
        all_news = []

        # Try yfinance first (most reliable)
        try:
            yf_news = self.fetch_yfinance_news(ticker, limit)
            if yf_news:
                logger.info(f"Got {len(yf_news)} news from yfinance for {ticker}")
                all_news.extend(yf_news)
        except Exception as e:
            logger.error(f"yfinance news fetch failed: {e}")

        # If yfinance returns enough news, return it
        if len(all_news) >= limit // 2:
            return all_news[:limit]

        # Fallback to web scraping
        sources = [
            ("Yahoo Finance Web", self.fetch_yahoo_finance_news),
            ("MarketWatch", self.fetch_marketwatch_news),
            ("Seeking Alpha", self.fetch_seeking_alpha_news),
            ("Benzinga", self.fetch_benzinga_news),
        ]

        for source_name, fetch_func in sources:
            try:
                news = fetch_func(ticker, limit=5)
                all_news.extend(news)
                logger.info(f"Got {len(news)} news from {source_name}")
            except Exception as e:
                logger.warning(f"Error fetching from {source_name}: {e}")

        # Deduplicate by title similarity
        seen_titles = set()
        unique_news = []

        for item in all_news:
            # Normalize title for comparison
            normalized = re.sub(r'[^\w\s]', '', item["title"].lower())[:50]
            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique_news.append(item)

        # Sort by published_at (if available) or keep order
        unique_news.sort(
            key=lambda x: x.get("published_at") or "9999",
            reverse=True
        )

        return unique_news[:limit]

    def fetch_market_news(self, limit: int = 20) -> List[Dict]:
        """
        Fetch general market news (not stock-specific)
        Uses yfinance to get news from major indices
        """
        all_news = []

        # Get news from major US indices using yfinance
        if YFINANCE_AVAILABLE:
            indices = ["^GSPC", "^DJI", "^IXIC"]  # S&P 500, Dow Jones, NASDAQ

            for index in indices:
                try:
                    ticker = yf.Ticker(index)
                    news_data = ticker.news

                    if news_data:
                        for item in news_data[:5]:
                            # Handle new yfinance structure
                            content = item.get("content", item)

                            title = content.get("title", "")
                            if not title:
                                continue

                            # Parse timestamp
                            published_at = None
                            pub_date = content.get("pubDate") or content.get("displayTime")
                            if pub_date and isinstance(pub_date, str):
                                try:
                                    published_at = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                                except Exception as e:
                                    logger.warning(f"Market news date ISO parse failed: {e}")
                            if not published_at:
                                timestamp = item.get("providerPublishTime")
                                if timestamp:
                                    try:
                                        published_at = datetime.fromtimestamp(timestamp)
                                    except Exception as e:
                                        logger.warning(f"Market news timestamp parse failed: {e}")

                            sentiment_data = self._analyze_sentiment(title)

                            # Get URL
                            url = ""
                            canonical_url = content.get("canonicalUrl", {})
                            if isinstance(canonical_url, dict):
                                url = canonical_url.get("url", "")
                            if not url:
                                url = item.get("link", "")
                            if not url:
                                news_id = item.get("id", "") or content.get("id", "")
                                if news_id:
                                    url = f"https://finance.yahoo.com/news/{news_id}"

                            # Get source
                            provider = content.get("provider", {})
                            source = provider.get("displayName", "Yahoo Finance") if isinstance(provider, dict) else "Yahoo Finance"

                            # Get summary
                            summary = content.get("summary", "") or content.get("description", "")

                            all_news.append({
                                "title": title,
                                "summary": summary[:500] if summary else "",
                                "source": source,
                                "url": url,
                                "published_at": published_at.isoformat() if published_at else None,
                                "sentiment": sentiment_data["sentiment"],
                                "sentiment_score": sentiment_data["score"],
                                "stock_id": None,
                                "market_region": "US",
                            })
                except Exception as e:
                    logger.warning(f"Error fetching news for {index}: {e}")

        # Deduplicate
        seen_titles = set()
        unique_news = []
        for item in all_news:
            normalized = re.sub(r'[^\w\s]', '', item["title"].lower())[:50]
            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique_news.append(item)

        # Sort by published_at
        unique_news.sort(
            key=lambda x: x.get("published_at") or "9999",
            reverse=True
        )

        if unique_news:
            logger.info(f"Got {len(unique_news)} market news from yfinance")
            return unique_news[:limit]

        # Fallback to web scraping
        self._rate_limit()
        url = "https://finance.yahoo.com/topic/stock-market-news/"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = []

            articles = soup.find_all('li', class_=re.compile(r'stream-item'))[:limit]

            for article in articles:
                try:
                    link_elem = article.find('a', href=True)
                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue

                    href = link_elem.get('href', '')
                    if href.startswith('/'):
                        href = f"https://finance.yahoo.com{href}"

                    source = "Yahoo Finance"
                    source_elem = article.find('span', class_=re.compile(r'provider'))
                    if source_elem:
                        source = source_elem.get_text(strip=True)

                    sentiment_data = self._analyze_sentiment(title)

                    news_items.append({
                        "title": title,
                        "summary": "",
                        "source": source,
                        "url": href,
                        "published_at": None,
                        "sentiment": sentiment_data["sentiment"],
                        "sentiment_score": sentiment_data["score"],
                        "stock_id": None,
                        "market_region": "US",
                    })
                except Exception:
                    continue

            return news_items

        except Exception as e:
            logger.error(f"Market news fetch error: {e}")
            return []


# Global instance
global_news_fetcher = GlobalNewsFetcher()
