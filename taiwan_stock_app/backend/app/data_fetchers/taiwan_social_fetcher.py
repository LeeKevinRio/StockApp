"""
Taiwan Social Media Stock Sentiment Fetcher
Fetches discussions from multiple Taiwan social platforms:
- PTT (Stock, Option, Foreign_Inv boards)
- Dcard (stock, investment topics)
- Mobile01 (investment forum)
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
import time
import random


class TaiwanSocialFetcher:
    """
    Taiwan Social Media Fetcher for Stock Discussions

    Platforms:
    - PTT: Stock, Option, Foreign_Inv boards
    - Dcard: stock, investment forums
    - Mobile01: Investment forum
    """

    # Sentiment keywords (Traditional Chinese)
    POSITIVE_KEYWORDS = [
        "多", "看多", "漲", "噴", "爆", "強", "買", "進場", "加碼", "利多",
        "突破", "起飛", "紅", "賺", "獲利", "上漲", "創高", "大漲", "飆",
        "牛", "做多", "翻倍", "好消息", "利好", "推", "正", "發大財",
        "財報好", "營收增", "毛利增", "上車", "all in", "梭哈",
    ]

    NEGATIVE_KEYWORDS = [
        "空", "看空", "跌", "崩", "慘", "弱", "賣", "出場", "減碼", "利空",
        "跌破", "破底", "綠", "賠", "虧損", "下跌", "創低", "大跌", "殺",
        "熊", "做空", "腰斬", "壞消息", "利空", "噓", "負", "套牢",
        "財報差", "營收減", "毛利減", "下車", "跑", "逃",
    ]

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    ]

    def __init__(self):
        self.session = requests.Session()
        # Disable SSL verification for PTT (some environments have SSL issues)
        self.session.verify = False
        self.last_request_time = 0
        self.request_interval = 2.0
        self._update_headers()

        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _update_headers(self):
        """Update session headers"""
        self.session.headers.update({
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
        })

    def _rate_limit(self):
        """Simple rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _request_with_retry(self, url: str, max_retries: int = 3, **kwargs) -> Optional[requests.Response]:
        """HTTP 請求 + 重試機制（指數退避）"""
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                self._update_headers()
                response = self.session.get(url, timeout=kwargs.get('timeout', 10), **{k: v for k, v in kwargs.items() if k != 'timeout'})
                if response.status_code == 200:
                    return response
                if response.status_code == 403:
                    print(f"  403 Forbidden (attempt {attempt+1}): {url}")
                elif response.status_code == 429:
                    print(f"  429 Rate limited (attempt {attempt+1}): {url}")
                else:
                    print(f"  HTTP {response.status_code} (attempt {attempt+1}): {url}")
            except requests.exceptions.RequestException as e:
                print(f"  Request error (attempt {attempt+1}): {e}")

            if attempt < max_retries - 1:
                wait = (2 ** attempt) + random.uniform(0.5, 1.5)
                time.sleep(wait)

        return None

    def _extract_stock_ids(self, text: str) -> List[str]:
        """Extract Taiwan stock IDs from text"""
        # Pattern: 4-6 digit numbers that look like stock IDs
        pattern = r'\b(\d{4,6})\b'
        matches = re.findall(pattern, text)

        # Filter to valid Taiwan stock ID ranges
        valid_ids = []
        for match in matches:
            num = int(match)
            # Common Taiwan stock ID ranges
            if (1000 <= num <= 9999) or (10000 <= num <= 99999):
                valid_ids.append(match)

        return list(set(valid_ids))

    def _analyze_sentiment(self, text: str, push_count: int = 0, boo_count: int = 0) -> Dict:
        """Analyze sentiment of Chinese text"""
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text)

        # Also consider push/boo counts
        total_reactions = push_count + boo_count
        if total_reactions > 0:
            reaction_score = (push_count - boo_count) / total_reactions
        else:
            reaction_score = 0

        total = positive_count + negative_count
        if total == 0:
            text_score = 0
        else:
            text_score = (positive_count - negative_count) / total

        # Combine text sentiment and reactions
        score = (text_score * 0.6) + (reaction_score * 0.4)

        if score > 0.15:
            sentiment = "positive"
        elif score < -0.15:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {"sentiment": sentiment, "score": round(score, 2)}

    # ============== PTT Fetcher ==============

    def fetch_ptt_board(self, board: str, pages: int = 2) -> List[Dict]:
        """Fetch posts from a PTT board (with retry)"""
        # PTT requires age verification cookie
        self.session.cookies.set("over18", "1", domain=".ptt.cc")

        posts = []
        base_url = f"https://www.ptt.cc/bbs/{board}/index.html"

        try:
            # Get the latest page with retry
            response = self._request_with_retry(base_url, max_retries=3)
            if response is None:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all article entries
            entries = soup.find_all('div', class_='r-ent')

            for entry in entries:
                try:
                    title_elem = entry.find('div', class_='title')
                    if not title_elem or not title_elem.find('a'):
                        continue

                    link = title_elem.find('a')
                    title = link.get_text(strip=True)
                    href = link.get('href', '')

                    # Skip announcements
                    if title.startswith('[公告]') or title.startswith('Fw:'):
                        continue

                    # Get push count
                    push_elem = entry.find('div', class_='nrec')
                    push_text = push_elem.get_text(strip=True) if push_elem else '0'

                    if push_text == '爆':
                        push_count = 100
                    elif push_text.startswith('X'):
                        push_count = -int(push_text[1:]) if len(push_text) > 1 else -10
                    else:
                        try:
                            push_count = int(push_text) if push_text else 0
                        except:
                            push_count = 0

                    # Get author
                    author_elem = entry.find('div', class_='author')
                    author = author_elem.get_text(strip=True) if author_elem else ''

                    # Get date
                    date_elem = entry.find('div', class_='date')
                    date_text = date_elem.get_text(strip=True) if date_elem else ''

                    # Extract stock IDs
                    stock_ids = self._extract_stock_ids(title)
                    sentiment_data = self._analyze_sentiment(title, max(push_count, 0), max(-push_count, 0))

                    posts.append({
                        "id": href.split('/')[-1].replace('.html', '') if href else '',
                        "platform": "ptt",
                        "board": board,
                        "title": title,
                        "content": "",
                        "author": author,
                        "url": f"https://www.ptt.cc{href}" if href else "",
                        "mentioned_stocks": stock_ids,
                        "sentiment": sentiment_data["sentiment"],
                        "sentiment_score": sentiment_data["score"],
                        "push_count": max(push_count, 0),
                        "boo_count": max(-push_count, 0),
                        "comment_count": 0,
                        "posted_at": None,
                    })
                except Exception as e:
                    continue

        except Exception as e:
            print(f"PTT fetch error for {board}: {e}")

        return posts

    # ============== Dcard Fetcher ==============

    def fetch_dcard_forum(self, forum: str = "stock", limit: int = 30) -> List[Dict]:
        """Fetch posts from Dcard forum (API → Web scraping fallback)"""
        # 嘗試 API
        posts = self._fetch_dcard_api(forum, limit)
        if posts:
            return posts

        # API 失敗，改用 Web scraping fallback
        print(f"Dcard API failed, trying web scraping fallback for {forum}")
        return self._fetch_dcard_web(forum, limit)

    def _fetch_dcard_api(self, forum: str, limit: int) -> List[Dict]:
        """Dcard API 方式"""
        url = f"https://www.dcard.tw/service/api/v2/forums/{forum}/posts?limit={limit}"

        try:
            headers = {
                "User-Agent": random.choice(self.USER_AGENTS),
                "Accept": "application/json",
                "Referer": f"https://www.dcard.tw/f/{forum}",
            }

            response = self._request_with_retry(url, max_retries=2, headers=headers)
            if response is None:
                return []

            data = response.json()
            return self._parse_dcard_posts(data, forum)
        except Exception as e:
            print(f"Dcard API error: {e}")
            return []

    def _fetch_dcard_web(self, forum: str, limit: int) -> List[Dict]:
        """Dcard Web scraping fallback（當 API 403 時）"""
        url = f"https://www.dcard.tw/f/{forum}"

        try:
            response = self._request_with_retry(url, max_retries=2)
            if response is None:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            posts = []

            # 嘗試從 HTML 提取文章列表
            articles = soup.find_all('article') or soup.find_all('div', {'data-key': True})
            for article in articles[:limit]:
                try:
                    title_elem = article.find('h2') or article.find('a')
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    if not title:
                        continue

                    link = article.find('a', href=True)
                    href = link.get('href', '') if link else ''

                    stock_ids = self._extract_stock_ids(title)
                    sentiment_data = self._analyze_sentiment(title)

                    posts.append({
                        "id": href.split('/')[-1] if href else '',
                        "platform": "dcard",
                        "board": f"Dcard-{forum}",
                        "title": title,
                        "content": "",
                        "author": "匿名",
                        "url": f"https://www.dcard.tw{href}" if href and not href.startswith('http') else href,
                        "mentioned_stocks": stock_ids,
                        "sentiment": sentiment_data["sentiment"],
                        "sentiment_score": sentiment_data["score"],
                        "push_count": 0,
                        "boo_count": 0,
                        "comment_count": 0,
                        "posted_at": None,
                    })
                except Exception:
                    continue

            return posts
        except Exception as e:
            print(f"Dcard web scraping error: {e}")
            return []

    def _parse_dcard_posts(self, data: list, forum: str) -> List[Dict]:
        """解析 Dcard API 回傳的文章列表"""
        posts = []
        for post in data:
            title = post.get("title", "")
            excerpt = post.get("excerpt", "")
            full_text = f"{title} {excerpt}"

            stock_ids = self._extract_stock_ids(full_text)
            like_count = post.get("likeCount", 0)
            comment_count = post.get("commentCount", 0)

            sentiment_data = self._analyze_sentiment(full_text, like_count, 0)

            created_at = post.get("createdAt", "")
            posted_at = None
            if created_at:
                try:
                    posted_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    pass

            posts.append({
                "id": str(post.get("id", "")),
                "platform": "dcard",
                "board": f"Dcard-{forum}",
                "title": title,
                "content": excerpt[:500] if excerpt else "",
                "author": post.get("school", "匿名"),
                "url": f"https://www.dcard.tw/f/{forum}/p/{post.get('id', '')}",
                "mentioned_stocks": stock_ids,
                "sentiment": sentiment_data["sentiment"],
                "sentiment_score": sentiment_data["score"],
                "push_count": like_count,
                "boo_count": 0,
                "comment_count": comment_count,
                "posted_at": posted_at.isoformat() if posted_at else None,
            })
        return posts

    # ============== Mobile01 Fetcher ==============

    def fetch_mobile01_forum(self, forum_id: int = 291, limit: int = 30) -> List[Dict]:
        """
        Fetch posts from Mobile01 investment forum
        Forum IDs: 291 = 投資與理財
        """
        self._rate_limit()

        url = f"https://www.mobile01.com/topiclist.php?f={forum_id}"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            posts = []

            # Find topic list
            topics = soup.find_all('div', class_='c-listTableTd__title')

            for topic in topics[:limit]:
                try:
                    link = topic.find('a')
                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    href = link.get('href', '')

                    stock_ids = self._extract_stock_ids(title)
                    sentiment_data = self._analyze_sentiment(title)

                    posts.append({
                        "id": href.split('t=')[-1].split('&')[0] if 't=' in href else '',
                        "platform": "mobile01",
                        "board": "Mobile01-投資理財",
                        "title": title,
                        "content": "",
                        "author": "",
                        "url": f"https://www.mobile01.com/{href}" if not href.startswith('http') else href,
                        "mentioned_stocks": stock_ids,
                        "sentiment": sentiment_data["sentiment"],
                        "sentiment_score": sentiment_data["score"],
                        "push_count": 0,
                        "boo_count": 0,
                        "comment_count": 0,
                        "posted_at": None,
                    })
                except Exception as e:
                    continue

        except Exception as e:
            print(f"Mobile01 fetch error: {e}")

        return posts

    # ============== Stock-Specific Search ==============

    def fetch_stock_discussions(self, stock_id: str, limit: int = 30) -> List[Dict]:
        """
        Fetch discussions about a specific stock from all platforms
        """
        all_posts = []

        # Fetch from all platforms
        all_platform_posts = self.fetch_all_platforms(limit_per_platform=30)

        # Filter posts that mention this stock
        for post in all_platform_posts:
            mentioned = post.get("mentioned_stocks", [])
            title = post.get("title", "")

            # Match by stock ID in mentioned_stocks list or in title
            if stock_id in mentioned or stock_id in title:
                all_posts.append(post)

        # If still no posts, try searching PTT specifically
        if len(all_posts) < 5:
            # Try searching in PTT Stock board
            try:
                search_url = f"https://www.ptt.cc/bbs/Stock/search?q={stock_id}"
                self._rate_limit()
                response = self.session.get(search_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    entries = soup.find_all('div', class_='r-ent')

                    for entry in entries[:limit]:
                        try:
                            title_elem = entry.find('div', class_='title')
                            if not title_elem or not title_elem.find('a'):
                                continue

                            link = title_elem.find('a')
                            title = link.get_text(strip=True)
                            href = link.get('href', '')

                            if title.startswith('[公告]'):
                                continue

                            push_elem = entry.find('div', class_='nrec')
                            push_text = push_elem.get_text(strip=True) if push_elem else '0'
                            if push_text == '爆':
                                push_count = 100
                            elif push_text.startswith('X'):
                                push_count = -int(push_text[1:]) if len(push_text) > 1 else -10
                            else:
                                try:
                                    push_count = int(push_text) if push_text else 0
                                except:
                                    push_count = 0

                            sentiment_data = self._analyze_sentiment(title, max(push_count, 0), max(-push_count, 0))

                            all_posts.append({
                                "id": href.split('/')[-1].replace('.html', '') if href else '',
                                "platform": "ptt",
                                "board": "Stock",
                                "title": title,
                                "content": "",
                                "author": "",
                                "url": f"https://www.ptt.cc{href}" if href else "",
                                "mentioned_stocks": [stock_id],
                                "sentiment": sentiment_data["sentiment"],
                                "sentiment_score": sentiment_data["score"],
                                "push_count": max(push_count, 0),
                                "boo_count": max(-push_count, 0),
                                "comment_count": 0,
                                "posted_at": None,
                            })
                        except Exception:
                            continue
            except Exception as e:
                print(f"PTT search error: {e}")

        return all_posts[:limit]

    # ============== Aggregation Methods ==============

    def fetch_all_platforms(self, limit_per_platform: int = 20) -> List[Dict]:
        """Fetch posts from all Taiwan social platforms"""
        all_posts = []

        # PTT boards
        ptt_boards = ["Stock", "Option", "Foreign_Inv"]
        for board in ptt_boards:
            posts = self.fetch_ptt_board(board)
            all_posts.extend(posts[:limit_per_platform])

        # Dcard
        dcard_posts = self.fetch_dcard_forum("stock", limit_per_platform)
        all_posts.extend(dcard_posts)

        # Mobile01 (optional - may be slower)
        try:
            m01_posts = self.fetch_mobile01_forum(291, limit_per_platform // 2)
            all_posts.extend(m01_posts)
        except:
            pass

        return all_posts

    def get_hot_stocks(self, limit: int = 20) -> List[Dict]:
        """Get trending Taiwan stocks from social media"""
        all_posts = self.fetch_all_platforms(limit_per_platform=25)

        # Aggregate by stock ID
        stock_data = {}

        for post in all_posts:
            for stock_id in post.get("mentioned_stocks", []):
                if stock_id not in stock_data:
                    stock_data[stock_id] = {
                        "stock_id": stock_id,
                        "mention_count": 0,
                        "sentiment_sum": 0.0,
                        "posts": [],
                    }

                stock_data[stock_id]["mention_count"] += 1
                stock_data[stock_id]["sentiment_sum"] += post.get("sentiment_score", 0)

                if len(stock_data[stock_id]["posts"]) < 5:
                    stock_data[stock_id]["posts"].append({
                        "platform": post["platform"],
                        "board": post["board"],
                        "title": post["title"],
                        "url": post["url"],
                        "author": post.get("author", ""),
                        "push_count": post.get("push_count", 0),
                        "boo_count": post.get("boo_count", 0),
                        "mentioned_stocks": post.get("mentioned_stocks", []),
                        "sentiment": post["sentiment"],
                        "sentiment_score": post.get("sentiment_score", 0),
                        "posted_at": post.get("posted_at"),
                    })

        # Calculate results
        hot_stocks = []
        for stock_id, data in stock_data.items():
            if data["mention_count"] >= 1:
                avg_sentiment = data["sentiment_sum"] / data["mention_count"]

                if avg_sentiment > 0.1:
                    sentiment = "positive"
                elif avg_sentiment < -0.1:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

                hot_stocks.append({
                    "stock_id": stock_id,
                    "stock_name": None,  # Need to lookup from DB
                    "mention_count": data["mention_count"],
                    "sentiment": sentiment,
                    "sentiment_score": round(avg_sentiment, 2),
                    "sample_posts": data["posts"],
                })

        # Sort by mention count
        hot_stocks.sort(key=lambda x: x["mention_count"], reverse=True)

        return hot_stocks[:limit]

    def get_market_sentiment(self) -> Dict:
        """Get overall Taiwan market sentiment"""
        all_posts = self.fetch_all_platforms(limit_per_platform=30)

        if not all_posts:
            return {
                "overall": "neutral",
                "score": 0.0,
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "sources": ["PTT", "Dcard", "Mobile01"],
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
            "sources": ["PTT", "Dcard", "Mobile01"],
        }


# Global instance
taiwan_social_fetcher = TaiwanSocialFetcher()
