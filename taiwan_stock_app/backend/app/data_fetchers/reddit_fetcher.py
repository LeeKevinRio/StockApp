"""
社交媒體股票情感分析器
從 Reddit 和 X (Twitter) 上爬取股票討論
使用多個備用方法處理速率限制
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
import time
import random
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# 嘗試導入增強情感分析器，如果不可用則降級使用簡單分析
try:
    from app.services.enhanced_sentiment_analyzer import enhanced_analyzer
    HAS_ENHANCED_SENTIMENT = True
except ImportError:
    HAS_ENHANCED_SENTIMENT = False
    logger.warning("增強情感分析器不可用，將使用簡單關鍵詞方法")


class SocialMediaFetcher:
    """
    社交媒體股票討論爬蟲

    監控的 Reddit 社群:
    - r/wallstreetbets (WSB) - 高度活躍，散戶情感
    - r/stocks - 一般股票討論
    - r/investing - 長期投資討論
    - r/options - 選擇權交易
    - r/StockMarket - 市場分析
    - r/twstock - 台灣股票 (若存在)
    - r/taiwan_stock - 台灣股票 (若存在)
    - r/ValueInvesting - 價值投資
    - r/dividends - 股息投資
    - r/thetagang - Theta 交易策略

    監控的 X (Twitter) 資源:
    - Nitter 公開實例（無需 API 密鑰）
    """

    # Reddit 社群
    SUBREDDITS = [
        "wallstreetbets",
        "stocks",
        "investing",
        "options",
        "StockMarket",
        "ValueInvesting",
        "dividends",
        "thetagang",
    ]

    # 台灣相關社群（使用 try/except 處理不存在的情況）
    TAIWAN_SUBREDDITS = [
        "twstock",
        "taiwan_stock",
    ]

    # Nitter 實例列表（備用方案）
    NITTER_INSTANCES = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
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
        self.base_request_interval = 2.0  # 基礎速率限制 - 2 秒
        self.request_interval = self.base_request_interval
        self.request_count = 0
        self.retry_count = 0
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
        """
        帶有指數退避的速率限制
        遇到速率限制時會逐漸增加等待時間
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _handle_rate_limit(self, status_code: int):
        """
        根據響應狀態碼調整速率限制
        使用指數退避策略
        """
        if status_code == 429:  # Too Many Requests
            self.retry_count += 1
            # 指數退避: 2秒 -> 4秒 -> 8秒 -> 16秒
            self.request_interval = self.base_request_interval * (2 ** min(self.retry_count, 3))
            logger.warning(f"遇到速率限制，調整間隔至 {self.request_interval:.1f} 秒")
        elif status_code == 200:
            # 成功時逐漸恢復基礎間隔
            if self.retry_count > 0:
                self.retry_count -= 1
                self.request_interval = self.base_request_interval * (2 ** max(0, self.retry_count - 1))
                if self.request_interval < self.base_request_interval:
                    self.request_interval = self.base_request_interval

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
        """
        分析文本情感
        優先使用增強情感分析器，降級使用簡單關鍵詞方法
        """
        # 嘗試使用增強情感分析器
        if HAS_ENHANCED_SENTIMENT:
            try:
                result = enhanced_analyzer.analyze(text)
                return {
                    "sentiment": result.get("sentiment", "neutral"),
                    "score": result.get("score", 0.0),
                    "confidence": result.get("confidence", 0.0),
                }
            except Exception as e:
                logger.warning(f"增強分析器出錯，降級使用簡單方法: {e}")

        # 降級：簡單關鍵詞計數
        text_lower = text.lower()

        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)

        total = positive_count + negative_count
        if total == 0:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}

        score = (positive_count - negative_count) / total

        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "confidence": round(min(abs(score), 1.0), 2)
        }

    def _fetch_with_retry(self, url: str, max_retries: int = 3, is_nitter: bool = False) -> Optional[Dict]:
        """
        帶有重試和標頭輪轉的 URL 爬取
        支援指數退避策略
        """
        for attempt in range(max_retries):
            self._rate_limit()
            self._update_headers()

            try:
                response = self.session.get(url, timeout=15)
                self._handle_rate_limit(response.status_code)

                if response.status_code == 200:
                    if is_nitter:
                        return response.text  # Nitter 返回 HTML
                    else:
                        return response.json()  # Reddit API 返回 JSON

                elif response.status_code == 403:
                    logger.warning(f"403 錯誤 (嘗試 {attempt + 1}/{max_retries})，重試中...")
                    time.sleep(2 + attempt * 2)

                elif response.status_code == 429:
                    logger.warning(f"速率限制 (嘗試 {attempt + 1}/{max_retries})，等待中...")
                    wait_time = (self.base_request_interval * (2 ** (attempt + 1)))
                    time.sleep(wait_time)

                else:
                    logger.error(f"API 錯誤: {response.status_code}")
                    if attempt == max_retries - 1:
                        return None

            except requests.exceptions.Timeout:
                logger.warning(f"請求超時 (嘗試 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 + attempt * 2)

            except requests.exceptions.ConnectionError:
                logger.warning(f"連接錯誤 (嘗試 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 + attempt * 2)

            except Exception as e:
                logger.error(f"請求錯誤: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 + attempt * 2)

        return None

    def fetch_subreddit_posts(self, subreddit: str, limit: int = 25) -> List[Dict]:
        """
        從 Reddit 社群爬取最新文章
        使用 Reddit JSON API
        """
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}&raw_json=1"

        data = self._fetch_with_retry(url)
        if not data:
            logger.warning(f"無法從 r/{subreddit} 爬取數據")
            return []

        posts = []
        for child in data.get("data", {}).get("children", []):
            post_data = child.get("data", {})

            # 跳過置頂文章
            if post_data.get("stickied"):
                continue

            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            full_text = f"{title} {selftext}"

            tickers = self._extract_tickers(full_text)
            sentiment_data = self._analyze_sentiment(full_text)

            # 轉換 Unix 時間戳為 datetime
            created_utc = post_data.get("created_utc", 0)
            posted_at = datetime.fromtimestamp(created_utc) if created_utc else None

            posts.append({
                "id": post_data.get("id", ""),
                "title": title,
                "content": selftext[:500] if selftext else "",
                "author": post_data.get("author", ""),
                "subreddit": subreddit,
                "url": f"https://reddit.com{post_data.get('permalink', '')}",
                "score": post_data.get("score", 0),  # 上投票 - 下投票
                "upvote_ratio": post_data.get("upvote_ratio", 0.5),
                "num_comments": post_data.get("num_comments", 0),
                "tickers": tickers,
                "sentiment": sentiment_data.get("sentiment", "neutral"),
                "sentiment_score": sentiment_data.get("score", 0.0),
                "sentiment_confidence": sentiment_data.get("confidence", 0.0),
                "posted_at": posted_at.isoformat() if posted_at else None,
                "platform": "reddit",
            })

        return posts

    def fetch_x_discussions(self, ticker: str, limit: int = 50) -> List[Dict]:
        """
        從 X (Twitter) 爬取股票討論
        使用 Nitter 公開實例（無需 API 密鑰）
        自動故障轉移至備用實例
        """
        posts = []

        # 嘗試每個 Nitter 實例
        for nitter_url in self.NITTER_INSTANCES:
            try:
                # 搜尋包含股票代碼的推文
                search_url = f"{nitter_url}/search?q=%24{ticker}%20lang%3Aen&type=latest&limit={limit}"

                html_content = self._fetch_with_retry(search_url, max_retries=2, is_nitter=True)

                if not html_content:
                    logger.warning(f"Nitter 實例 {nitter_url} 無法回應")
                    continue

                # 簡單的 HTML 解析以提取推文
                # 查找推文容器
                import re as regex_module

                # 尋找推文文本和作者
                tweet_pattern = r'<div[^>]*class="[^"]*tweet[^"]*"[^>]*>.*?<div[^>]*class="[^"]*tweet-content[^"]*"[^>]*>(.*?)</div>'
                author_pattern = r'<a href="/@([^"]+)"'

                tweet_texts = regex_module.findall(tweet_pattern, html_content, regex_module.DOTALL)
                authors = regex_module.findall(author_pattern, html_content)

                for idx, tweet_text in enumerate(tweet_texts[:limit]):
                    # 清理 HTML 標籤
                    cleaned_text = regex_module.sub('<[^<]+?>', '', tweet_text)
                    cleaned_text = cleaned_text.strip()

                    if not cleaned_text or len(cleaned_text) < 10:
                        continue

                    sentiment_data = self._analyze_sentiment(cleaned_text)

                    posts.append({
                        "id": f"x_{ticker}_{idx}",
                        "title": cleaned_text[:100],
                        "content": cleaned_text[:280],  # X 限制字數
                        "author": authors[idx] if idx < len(authors) else "unknown",
                        "platform": "x",
                        "board": "twitter",
                        "url": f"{nitter_url}/search?q=%24{ticker}",
                        "score": 0,  # X 上沒有直接的点贊數據從 Nitter
                        "num_comments": 0,
                        "tickers": [ticker.upper()],
                        "sentiment": sentiment_data.get("sentiment", "neutral"),
                        "sentiment_score": sentiment_data.get("score", 0.0),
                        "sentiment_confidence": sentiment_data.get("confidence", 0.0),
                        "posted_at": datetime.now().isoformat(),
                    })

                # 如果成功取得數據，則跳出迴圈
                if posts:
                    logger.info(f"從 {nitter_url} 成功爬取 {len(posts)} 條推文")
                    break

            except Exception as e:
                logger.warning(f"從 Nitter 實例 {nitter_url} 爬取失敗: {e}")
                continue

        return posts

    def fetch_recent_posts(self, limit_per_sub: int = 20, include_taiwan: bool = False) -> List[Dict]:
        """
        從所有監控的 Reddit 社群爬取最新文章
        可選包含台灣相關社群
        """
        all_posts = []
        subreddits_to_fetch = self.SUBREDDITS[:]

        # 如果要求台灣社群，嘗試添加它們
        if include_taiwan:
            subreddits_to_fetch.extend(self.TAIWAN_SUBREDDITS)

        for subreddit in subreddits_to_fetch:
            try:
                posts = self.fetch_subreddit_posts(subreddit, limit_per_sub)
                all_posts.extend(posts)
            except Exception as e:
                logger.warning(f"無法從 r/{subreddit} 爬取數據: {e}")
                continue

        # 按分數排序（受歡迎程度）
        all_posts.sort(key=lambda x: x.get("score", 0), reverse=True)

        return all_posts

    def fetch_stock_discussions(self, ticker: str, limit: int = 50) -> List[Dict]:
        """
        爬取提及特定股票代碼的討論
        同時搜尋多個主要社群
        """
        # 在 Reddit 上搜尋股票代碼
        search_query = f"{ticker} (subreddit:wallstreetbets OR subreddit:stocks OR subreddit:investing)"
        url = f"https://www.reddit.com/search.json?q={requests.utils.quote(search_query)}&sort=new&limit={limit}&raw_json=1"

        data = self._fetch_with_retry(url)
        if not data:
            logger.warning(f"無法搜尋 Reddit 上的 {ticker}")
            return []

        posts = []
        for child in data.get("data", {}).get("children", []):
            post_data = child.get("data", {})

            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            full_text = f"{title} {selftext}"

            # 僅包含實際提及股票代碼的文章
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
                "sentiment": sentiment_data.get("sentiment", "neutral"),
                "sentiment_score": sentiment_data.get("score", 0.0),
                "sentiment_confidence": sentiment_data.get("confidence", 0.0),
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

    def get_trending_tickers(self, hours: int = 24, limit: int = 20) -> List[Dict]:
        """
        找出最近 24 小時內所有 Reddit 社群中最多被提及的股票代碼
        返回趨勢排名
        """
        all_posts = self.fetch_recent_posts(limit_per_sub=50)

        # 過濾最近 N 小時內的文章
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_posts = []

        for post in all_posts:
            try:
                if post.get("posted_at"):
                    posted_at = datetime.fromisoformat(post["posted_at"])
                    if posted_at > cutoff_time:
                        recent_posts.append(post)
            except:
                recent_posts.append(post)  # 時間解析失敗時也包含

        # 聚集股票代碼提及
        ticker_data = defaultdict(lambda: {
            "mention_count": 0,
            "sentiment_scores": [],
            "sentiments": defaultdict(int),
            "subreddits": set(),
            "sample_posts": [],
        })

        for post in recent_posts:
            for ticker in post.get("tickers", []):
                ticker_data[ticker]["mention_count"] += 1
                ticker_data[ticker]["sentiment_scores"].append(post.get("sentiment_score", 0))
                ticker_data[ticker]["sentiments"][post.get("sentiment", "neutral")] += 1
                ticker_data[ticker]["subreddits"].add(post.get("subreddit", ""))

                # 保存範例文章
                if len(ticker_data[ticker]["sample_posts"]) < 3:
                    ticker_data[ticker]["sample_posts"].append({
                        "title": post.get("title", ""),
                        "content": post.get("content", ""),
                        "subreddit": post.get("subreddit", ""),
                        "sentiment": post.get("sentiment", "neutral"),
                        "url": post.get("url", ""),
                    })

        # 計算聚集統計
        trending = []
        for ticker, data in ticker_data.items():
            if data["mention_count"] >= 2:  # 至少 2 次提及
                avg_sentiment = (
                    sum(data["sentiment_scores"]) / len(data["sentiment_scores"])
                    if data["sentiment_scores"]
                    else 0.0
                )

                # 確定主導情感
                sentiments = data["sentiments"]
                dominant_sentiment = max(sentiments.items(), key=lambda x: x[1])[0]

                trending.append({
                    "ticker": ticker,
                    "mention_count": data["mention_count"],
                    "avg_sentiment_score": round(avg_sentiment, 2),
                    "dominant_sentiment": dominant_sentiment,
                    "sentiment_breakdown": dict(sentiments),
                    "subreddit_count": len(data["subreddits"]),
                    "subreddits": list(data["subreddits"]),
                    "sample_posts": data["sample_posts"],
                    "trend_strength": min(data["mention_count"] * abs(avg_sentiment), 10.0),  # 0-10 分數
                })

        # 按提及次數和趨勢強度排序
        trending.sort(key=lambda x: (x["mention_count"], x["trend_strength"]), reverse=True)

        return trending[:limit]

    def get_social_sentiment_for_ai(self, ticker: str) -> Dict:
        """
        為 AI 分析管線獲取社交情感數據
        整合 Reddit 和 X (Twitter) 的情感分析
        返回結構化字典供 AI 分析使用
        """
        try:
            # 並行爬取 Reddit 和 X 討論
            reddit_posts = self.fetch_stock_discussions(ticker, limit=30)
            x_posts = self.fetch_x_discussions(ticker, limit=30)

            # 計算 Reddit 情感
            reddit_sentiment = self._aggregate_sentiment(reddit_posts)

            # 計算 X 情感
            x_sentiment = self._aggregate_sentiment(x_posts)

            # 合併情感
            all_posts = reddit_posts + x_posts
            overall_sentiment = self._aggregate_sentiment(all_posts)

            # 按情感分類文章
            bullish_posts = [p for p in all_posts if p.get("sentiment") == "positive"]
            bearish_posts = [p for p in all_posts if p.get("sentiment") == "negative"]

            # 按分數排序
            bullish_posts.sort(key=lambda x: x.get("sentiment_score", 0), reverse=True)
            bearish_posts.sort(key=lambda x: x.get("sentiment_score", 0))

            # 返回 AI 分析用的結構化數據
            return {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "overall_sentiment": overall_sentiment["sentiment"],
                "overall_sentiment_score": overall_sentiment["score"],
                "overall_confidence": overall_sentiment["confidence"],
                "reddit_sentiment": {
                    "sentiment": reddit_sentiment["sentiment"],
                    "score": reddit_sentiment["score"],
                    "confidence": reddit_sentiment["confidence"],
                    "post_count": len(reddit_posts),
                    "avg_engagement": (
                        sum(p.get("score", 0) for p in reddit_posts) / len(reddit_posts)
                        if reddit_posts
                        else 0
                    ),
                },
                "x_sentiment": {
                    "sentiment": x_sentiment["sentiment"],
                    "score": x_sentiment["score"],
                    "confidence": x_sentiment["confidence"],
                    "post_count": len(x_posts),
                    "avg_engagement": (
                        sum(p.get("score", 0) for p in x_posts) / len(x_posts)
                        if x_posts
                        else 0
                    ),
                },
                "discussion_volume": len(all_posts),
                "reddit_discussion_volume": len(reddit_posts),
                "x_discussion_volume": len(x_posts),
                "top_bullish_posts": [
                    {
                        "title": p.get("title", ""),
                        "content": p.get("content", ""),
                        "platform": p.get("platform", ""),
                        "sentiment_score": p.get("sentiment_score", 0),
                        "engagement": p.get("score", 0),
                        "url": p.get("url", ""),
                    }
                    for p in bullish_posts[:5]
                ],
                "top_bearish_posts": [
                    {
                        "title": p.get("title", ""),
                        "content": p.get("content", ""),
                        "platform": p.get("platform", ""),
                        "sentiment_score": p.get("sentiment_score", 0),
                        "engagement": p.get("score", 0),
                        "url": p.get("url", ""),
                    }
                    for p in bearish_posts[:5]
                ],
                "sentiment_ratio": {
                    "bullish": len(bullish_posts),
                    "bearish": len(bearish_posts),
                    "neutral": len(all_posts) - len(bullish_posts) - len(bearish_posts),
                },
            }

        except Exception as e:
            logger.error(f"為 {ticker} 獲取社交情感數據失敗: {e}")
            # 返回中性默認值
            return {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "overall_sentiment": "neutral",
                "overall_sentiment_score": 0.0,
                "overall_confidence": 0.0,
                "reddit_sentiment": {"sentiment": "neutral", "score": 0.0, "confidence": 0.0, "post_count": 0},
                "x_sentiment": {"sentiment": "neutral", "score": 0.0, "confidence": 0.0, "post_count": 0},
                "discussion_volume": 0,
                "reddit_discussion_volume": 0,
                "x_discussion_volume": 0,
                "top_bullish_posts": [],
                "top_bearish_posts": [],
                "sentiment_ratio": {"bullish": 0, "bearish": 0, "neutral": 0},
            }

    def _aggregate_sentiment(self, posts: List[Dict]) -> Dict:
        """
        聚集多個文章的情感
        計算加權平均情感分數
        """
        if not posts:
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "confidence": 0.0,
            }

        sentiment_scores = [p.get("sentiment_score", 0) for p in posts]
        confidence_scores = [p.get("sentiment_confidence", 0) for p in posts]

        avg_score = sum(sentiment_scores) / len(sentiment_scores)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

        if avg_score > 0.1:
            sentiment = "positive"
        elif avg_score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "score": round(avg_score, 2),
            "confidence": round(avg_confidence, 2),
        }

    def get_market_sentiment(self) -> Dict:
        """
        從 Reddit 獲取整體市場情感
        包括正面、負面和中立情感的分佈
        """
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


# 全球實例
# 新名稱：SocialMediaFetcher
social_media_fetcher = SocialMediaFetcher()

# 向後相容別名
reddit_fetcher = social_media_fetcher
RedditFetcher = SocialMediaFetcher  # 類別別名
