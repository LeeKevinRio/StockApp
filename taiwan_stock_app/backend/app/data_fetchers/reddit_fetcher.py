"""
Reddit Stock Sentiment Fetcher
Fetches discussions from popular stock/investing subreddits for US stocks
Uses multiple fallback methods to handle rate limiting
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
import time
import random


class RedditFetcher:
    """
    Reddit Stock Discussion Fetcher

    Subreddits monitored:
    - r/wallstreetbets (WSB) - High activity, retail sentiment
    - r/stocks - General stock discussions
    - r/investing - Long-term investment discussions
    - r/options - Options trading
    - r/StockMarket - Market analysis
    """

    SUBREDDITS = [
        "wallstreetbets",
        "stocks",
        "investing",
        "options",
        "StockMarket",
    ]

    # Common US stock tickers to track
    POPULAR_TICKERS = [
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "TSLA", "META", "NVDA",
        "AMD", "INTC", "NFLX", "DIS", "PYPL", "SQ", "COIN", "GME", "AMC",
        "SPY", "QQQ", "PLTR", "NIO", "BABA", "SOFI", "RIVN", "LCID",
        "JPM", "BAC", "WFC", "GS", "V", "MA",
    ]

    # Sentiment keywords
    POSITIVE_KEYWORDS = [
        "bull", "bullish", "moon", "rocket", "buy", "calls", "long",
        "breakout", "squeeze", "diamond hands", "hold", "hodl", "tendies",
        "gains", "profit", "green", "pump", "rally", "surge", "soar",
        "beat", "exceeded", "outperform", "upgrade", "strong buy",
        "to the moon", "ath", "all time high", "undervalued",
    ]

    NEGATIVE_KEYWORDS = [
        "bear", "bearish", "crash", "dump", "sell", "puts", "short",
        "breakdown", "loss", "red", "tank", "plunge", "drop", "fall",
        "miss", "disappoint", "underperform", "downgrade", "overvalued",
        "paper hands", "bag holder", "rip", "dead", "worthless",
        "bubble", "scam", "fraud", "bankrupt",
    ]

    # User agents rotation for better success rate
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.request_interval = 3.0  # Rate limiting - 3 seconds between requests
        self._update_headers()

    def _update_headers(self):
        """Update session headers with random user agent"""
        self.session.headers.update({
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
        })

    def _rate_limit(self):
        """Simple rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        # Pattern: $TICKER or standalone TICKER (1-5 uppercase letters)
        patterns = [
            r'\$([A-Z]{1,5})\b',  # $AAPL format
            r'\b([A-Z]{2,5})\b',  # Standalone like AAPL
        ]

        tickers = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Filter out common words that look like tickers
                if match not in ['I', 'A', 'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT',
                                'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR',
                                'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW',
                                'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'WAY',
                                'WHO', 'BOY', 'DID', 'OWN', 'SAY', 'SHE', 'TOO',
                                'USE', 'CEO', 'CFO', 'IPO', 'ETF', 'USD', 'EUR',
                                'GDP', 'CPI', 'FED', 'SEC', 'NYSE', 'NASDAQ', 'DD',
                                'YOLO', 'IMO', 'TBH', 'FYI', 'TLDR', 'EPS', 'PE',
                                'US', 'UK', 'EU', 'AI', 'EV', 'IT', 'TV', 'PC']:
                    if match in self.POPULAR_TICKERS:
                        tickers.add(match)

        return list(tickers)

    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text"""
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

    def _fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """Fetch URL with retry and header rotation"""
        for attempt in range(max_retries):
            self._rate_limit()
            self._update_headers()

            try:
                response = self.session.get(url, timeout=15)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    print(f"Reddit 403 error (attempt {attempt + 1}), retrying...")
                    time.sleep(2 + attempt * 2)
                elif response.status_code == 429:
                    print(f"Reddit rate limited (attempt {attempt + 1}), waiting...")
                    time.sleep(5 + attempt * 5)
                else:
                    print(f"Reddit API error: {response.status_code}")
                    return None
            except Exception as e:
                print(f"Reddit request error: {e}")
                time.sleep(2)

        return None

    def fetch_subreddit_posts(self, subreddit: str, limit: int = 25) -> List[Dict]:
        """Fetch recent posts from a subreddit using Reddit's JSON API"""
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}&raw_json=1"

        data = self._fetch_with_retry(url)
        if not data:
            return []

        posts = []
        for child in data.get("data", {}).get("children", []):
            post_data = child.get("data", {})

            # Skip pinned/stickied posts
            if post_data.get("stickied"):
                continue

            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            full_text = f"{title} {selftext}"

            tickers = self._extract_tickers(full_text)
            sentiment_data = self._analyze_sentiment(full_text)

            # Convert Unix timestamp to datetime
            created_utc = post_data.get("created_utc", 0)
            posted_at = datetime.fromtimestamp(created_utc) if created_utc else None

            posts.append({
                "id": post_data.get("id", ""),
                "title": title,
                "content": selftext[:500] if selftext else "",
                "author": post_data.get("author", ""),
                "subreddit": subreddit,
                "url": f"https://reddit.com{post_data.get('permalink', '')}",
                "score": post_data.get("score", 0),  # Upvotes - downvotes
                "upvote_ratio": post_data.get("upvote_ratio", 0.5),
                "num_comments": post_data.get("num_comments", 0),
                "tickers": tickers,
                "sentiment": sentiment_data["sentiment"],
                "sentiment_score": sentiment_data["score"],
                "posted_at": posted_at.isoformat() if posted_at else None,
                "platform": "reddit",
            })

        return posts

    def fetch_recent_posts(self, limit_per_sub: int = 20) -> List[Dict]:
        """Fetch recent posts from all monitored subreddits"""
        all_posts = []

        for subreddit in self.SUBREDDITS:
            posts = self.fetch_subreddit_posts(subreddit, limit_per_sub)
            all_posts.extend(posts)

        # Sort by score (popularity)
        all_posts.sort(key=lambda x: x.get("score", 0), reverse=True)

        return all_posts

    def fetch_stock_discussions(self, ticker: str, limit: int = 50) -> List[Dict]:
        """Fetch discussions mentioning a specific stock ticker"""
        # Search Reddit for the ticker
        search_query = f"{ticker} (subreddit:wallstreetbets OR subreddit:stocks OR subreddit:investing)"
        url = f"https://www.reddit.com/search.json?q={requests.utils.quote(search_query)}&sort=new&limit={limit}&raw_json=1"

        data = self._fetch_with_retry(url)
        if not data:
            return []

        posts = []
        for child in data.get("data", {}).get("children", []):
            post_data = child.get("data", {})

            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            full_text = f"{title} {selftext}"

            # Only include if ticker is actually mentioned
            if ticker.upper() not in full_text.upper():
                continue

            sentiment_data = self._analyze_sentiment(full_text)
            created_utc = post_data.get("created_utc", 0)
            posted_at = datetime.fromtimestamp(created_utc) if created_utc else None

            posts.append({
                "id": post_data.get("id", ""),
                "title": title,
                "content": selftext[:500] if selftext else "",
                "author": post_data.get("author", ""),
                "subreddit": post_data.get("subreddit", ""),
                "url": f"https://reddit.com{post_data.get('permalink', '')}",
                "score": post_data.get("score", 0),
                "upvote_ratio": post_data.get("upvote_ratio", 0.5),
                "num_comments": post_data.get("num_comments", 0),
                "tickers": [ticker.upper()],
                "sentiment": sentiment_data["sentiment"],
                "sentiment_score": sentiment_data["score"],
                "posted_at": posted_at.isoformat() if posted_at else None,
                "platform": "reddit",
            })

        return posts

    def get_hot_stocks(self, limit: int = 20) -> List[Dict]:
        """Get trending stocks based on Reddit mentions"""
        all_posts = self.fetch_recent_posts(limit_per_sub=25)

        # Aggregate ticker mentions
        ticker_data = {}

        for post in all_posts:
            for ticker in post.get("tickers", []):
                if ticker not in ticker_data:
                    ticker_data[ticker] = {
                        "stock_id": ticker,
                        "mention_count": 0,
                        "total_score": 0,
                        "sentiment_sum": 0.0,
                        "posts": [],
                    }

                ticker_data[ticker]["mention_count"] += 1
                ticker_data[ticker]["total_score"] += post.get("score", 0)
                ticker_data[ticker]["sentiment_sum"] += post.get("sentiment_score", 0)

                if len(ticker_data[ticker]["posts"]) < 5:
                    # Format to match frontend SocialPost model
                    created_str = post.get("posted_at")
                    ticker_data[ticker]["posts"].append({
                        "id": post.get("id"),
                        "platform": "reddit",
                        "board": f"r/{post['subreddit']}",
                        "title": post["title"],
                        "content": post.get("content", ""),
                        "author": post.get("author", ""),
                        "url": post["url"],
                        "sentiment": post["sentiment"],
                        "sentiment_score": post.get("sentiment_score", 0),
                        "push_count": post["score"],  # Reddit score as push_count
                        "boo_count": 0,
                        "comment_count": post.get("num_comments", 0),
                        "posted_at": created_str,
                    })

        # Calculate average sentiment and sort by mentions
        hot_stocks = []
        for ticker, data in ticker_data.items():
            if data["mention_count"] >= 1:  # At least 1 mention
                avg_sentiment = data["sentiment_sum"] / data["mention_count"]

                if avg_sentiment > 0.1:
                    sentiment = "positive"
                elif avg_sentiment < -0.1:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

                hot_stocks.append({
                    "stock_id": ticker,
                    "stock_name": ticker,  # Would need external lookup for full name
                    "mention_count": data["mention_count"],
                    "total_score": data["total_score"],
                    "sentiment": sentiment,
                    "sentiment_score": round(avg_sentiment, 2),
                    "sample_posts": data["posts"],  # Match frontend expected field
                })

        # Sort by mention count
        hot_stocks.sort(key=lambda x: x["mention_count"], reverse=True)

        return hot_stocks[:limit]

    def get_market_sentiment(self) -> Dict:
        """Get overall market sentiment from Reddit"""
        all_posts = self.fetch_recent_posts(limit_per_sub=30)

        if not all_posts:
            return {
                "overall": "neutral",
                "score": 0.0,
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
            }

        positive = sum(1 for p in all_posts if p.get("sentiment") == "positive")
        negative = sum(1 for p in all_posts if p.get("sentiment") == "negative")
        neutral = len(all_posts) - positive - negative

        total = len(all_posts)
        score = (positive - negative) / total if total > 0 else 0

        if score > 0.1:
            overall = "positive"
        elif score < -0.1:
            overall = "negative"
        else:
            overall = "neutral"

        return {
            "overall": overall,
            "score": round(score, 2),
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
        }


# Global instance
reddit_fetcher = RedditFetcher()
