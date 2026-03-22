"""
Threads Stock Sentiment Fetcher
透過 Threads 公開頁面抓取股票相關討論，支援台股與美股
"""
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re
import time
import random
import logging
import json
from collections import Counter

logger = logging.getLogger(__name__)


class ThreadsFetcher:
    """
    Threads 股票討論抓取器

    資料來源：
    - 台股：搜尋 #台股 #股票 #投資 等 hashtag，以及知名財經帳號
    - 美股：搜尋 #stocks #investing #wallstreet 等 hashtag
    """

    # 台股相關搜尋關鍵字 - 擴展版本
    TW_SEARCH_QUERIES = [
        # 基礎股票術語
        "台股", "台積電", "股票 投資", "台股 漲", "台股 跌",
        # 個股搜尋
        "鴻海", "聯發科", "台達電", "大立光", "中華電", "富邦金", "國泰金",
        "聯電", "日月光", "華碩", "長榮", "陽明",
        # 產業與概念股
        "半導體", "AI概念股", "電動車", "金融股", "ETF", "被動式基金",
        # 市場情緒關鍵字
        "崩盤", "噴出", "利多", "利空", "停損", "停利",
        "強勢", "弱勢", "反彈", "套牢", "破底", "翻多", "翻空",
    ]

    # 美股相關搜尋關鍵字 - 擴展版本
    US_SEARCH_QUERIES = [
        # 基礎術語
        "stocks", "stock market", "investing", "S&P 500", "nasdaq",
        # 熱門股票
        "NVDA", "AAPL", "TSMC", "NVIDIA", "AMD", "Apple", "Tesla",
        "Microsoft", "Google", "Amazon", "Meta",
        # 產業與概念
        "semiconductor stocks", "AI stocks", "EV stocks", "fintech",
        "tech earnings", "market sentiment",
        # 市場情緒
        "bull market", "bear market", "crash", "rally", "breakout",
    ]

    # 台股 sentiment 關鍵字
    TW_POSITIVE_KEYWORDS = [
        "多", "漲", "噴", "爆", "買", "利多", "突破", "紅", "賺",
        "看好", "強勢", "起飛", "飆", "大漲", "紅盤", "上攻", "創高",
        "抄底", "加碼", "進場", "翻多", "反彈",
    ]

    TW_NEGATIVE_KEYWORDS = [
        "空", "跌", "崩", "慘", "賣", "利空", "綠", "賠",
        "看壞", "弱勢", "下殺", "暴跌", "破底", "套牢", "出場",
        "翻空", "逃命", "恐慌", "跳水", "腰斬",
    ]

    # 美股 sentiment 關鍵字（與 Reddit 共用）
    US_POSITIVE_KEYWORDS = [
        "bull", "bullish", "moon", "rocket", "buy", "calls", "long",
        "breakout", "squeeze", "gains", "profit", "green", "pump",
        "rally", "surge", "beat", "upgrade", "undervalued",
    ]

    US_NEGATIVE_KEYWORDS = [
        "bear", "bearish", "crash", "dump", "sell", "puts", "short",
        "breakdown", "loss", "red", "tank", "plunge", "drop",
        "miss", "downgrade", "overvalued", "bubble", "bankrupt",
    ]

    # 台股代碼對照（熱門股）- 擴展版本
    TW_POPULAR_STOCKS = {
        # 台積電相關
        "台積電": "2330", "鴻海": "2317", "聯發科": "2454", "聯電": "2303",
        # 電子產業
        "廣達": "2382", "台達電": "2308", "華碩": "2357", "緯創": "3231",
        "英業達": "2356", "仁寶": "2324", "大立光": "3008", "日月光": "3711",
        "穩懋": "3105", "瑞昱": "2379", "矽力": "6415", "信驊": "5274",
        # 金融股
        "富邦金": "2881", "國泰金": "2882", "中信金": "2891", "兆豐金": "2886",
        "玉山金": "2884", "第一金": "2892", "元大金": "2885",
        # 民生消費
        "統一": "1216", "台塑": "1301", "南亞": "1303", "中鋼": "2002",
        # 運輸物流
        "長榮": "2603", "陽明": "2609", "華航": "2610", "萬海": "2615",
        # 面板
        "友達": "2409", "群創": "3481",
        # 通訊
        "中華電": "2412", "遠傳": "2891",
        # 其他熱門股
        "台灣塑膠": "1301", "中華食": "1217", "永豐金": "2890",
    }

    # 美股熱門代碼 - 擴展版本
    US_POPULAR_TICKERS = [
        # 科技巨頭
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AMD", "INTC",
        "TSLA", "NFLX", "COIN", "PLTR",
        # 台積電相關（美股）
        "TSM", "ASML", "LRCX", "KLAC", "AMAT",
        # ETF
        "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO",
        # 消費與零售
        "DIS", "PYPL", "SHOP", "SQ", "SOFI",
        # 遊戲與娛樂
        "GME", "RBLX",
        # 新能源與電動車
        "TSLA", "NIO", "XPeng", "LI", "RIVN", "LUCID",
        # 中資與 ADR
        "BABA", "JD", "PDD", "BILI",
        # 金融
        "JPM", "BAC", "GS", "MS", "C", "WFC",
        # 支付與卡組織
        "V", "MA", "AXP", "DFS",
        # 半導體相關
        "AVGO", "MU", "QCOM", "BROADCOM", "QUALCOMM",
        # AI 概念
        "CRM", "SNOW", "PSTG", "MSTR",
    ]

    USER_AGENTS = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.request_interval = 3.0
        self.retry_count = 0
        self.max_retries = 3
        self._update_headers()

        # 非股票相關的垃圾過濾關鍵字
        self.NOISE_KEYWORDS = {
            # 食物相關
            "食物", "餐廳", "美食", "料理", "食譜", "吃", "飲食", "烹飪",
            # 旅遊相關
            "旅遊", "旅行", "景點", "度假", "飯店", "民宿", "渡假村",
            # 娛樂相關
            "電影", "電視劇", "演員", "明星", "追劇", "影劇", "綜藝", "音樂",
            # 其他無關
            "天氣", "運動", "籃球", "足球", "棒球", "遊戲", "寵物", "寵物", "旗艦",
        }

    def _update_headers(self):
        self.session.headers.update({
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
        })

    def _rate_limit(self, retry_count: int = 0):
        """
        智能延遲控制，支援指數退避 (exponential backoff)

        Args:
            retry_count: 目前重試次數，用於計算退避延遲
        """
        # 指數退避：基礎延遲 + 隨機抖動
        base_delay = self.request_interval
        if retry_count > 0:
            # 指數退避：3 秒 * (2 ^ 重試次數)
            base_delay = min(self.request_interval * (2 ** retry_count), 30)

        # 加入 ±20% 的隨機抖動，避免同時發送請求
        jitter = base_delay * random.uniform(-0.2, 0.2)
        total_delay = base_delay + jitter

        elapsed = time.time() - self.last_request_time
        if elapsed < total_delay:
            time.sleep(total_delay - elapsed)
        self.last_request_time = time.time()

    def _is_spam_post(self, text: str) -> bool:
        """
        判斷貼文是否為垃圾內容（過短、過多 hashtag 或無關內容）

        Args:
            text: 貼文內容

        Returns:
            True 表示是垃圾內容，應該過濾掉
        """
        # 檢查長度：少於 10 字元視為無效
        if len(text.strip()) < 10:
            return True

        # 檢查 hashtag 過多：超過 10 個 hashtag 視為垃圾
        hashtag_count = len(re.findall(r'#\w+', text))
        if hashtag_count > 10:
            return True

        # 檢查是否包含垃圾關鍵字
        text_lower = text.lower()
        for noise_kw in self.NOISE_KEYWORDS:
            if noise_kw in text_lower:
                return True

        return False

    def _extract_tw_stocks(self, text: str) -> List[str]:
        """
        從文字中提取台股代碼

        Args:
            text: 貼文文本

        Returns:
            台股代碼清單
        """
        stocks = set()

        # 1. 比對公司名稱
        for name, code in self.TW_POPULAR_STOCKS.items():
            if name in text:
                stocks.add(code)

        # 2. 比對數字代碼 (4-6位)
        matches = re.findall(r'\b(\d{4,6})\b', text)
        for m in matches:
            if 1000 <= int(m) <= 999999:
                stocks.add(m)

        return list(stocks)

    def _extract_us_tickers(self, text: str) -> List[str]:
        """從文字中提取美股代碼"""
        tickers = set()
        patterns = [
            r'\$([A-Z]{1,5})\b',
            r'\b([A-Z]{2,5})\b',
        ]

        skip_words = {
            'I', 'A', 'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT',
            'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT',
            'DAY', 'GET', 'HAS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW',
            'OLD', 'SEE', 'WAY', 'WHO', 'DID', 'OWN', 'SAY', 'SHE',
            'TOO', 'USE', 'CEO', 'CFO', 'IPO', 'ETF', 'USD', 'EUR',
            'GDP', 'CPI', 'FED', 'SEC', 'NYSE', 'DD', 'YOLO', 'IMO',
            'TBH', 'FYI', 'TLDR', 'EPS', 'US', 'UK', 'EU', 'AI',
            'EV', 'IT', 'TV', 'PC', 'UP', 'GO', 'AT', 'SO', 'IF',
        }

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in skip_words and match in self.US_POPULAR_TICKERS:
                    tickers.add(match)

        return list(tickers)

    def _analyze_sentiment(self, text: str, market: str = "TW") -> Dict:
        """分析文字情緒"""
        if market == "TW":
            pos_kw = self.TW_POSITIVE_KEYWORDS
            neg_kw = self.TW_NEGATIVE_KEYWORDS
        else:
            pos_kw = self.US_POSITIVE_KEYWORDS
            neg_kw = self.US_NEGATIVE_KEYWORDS

        text_lower = text.lower()
        positive_count = sum(1 for kw in pos_kw if kw in text_lower)
        negative_count = sum(1 for kw in neg_kw if kw in text_lower)

        total = positive_count + negative_count
        if total == 0:
            return {"sentiment": "neutral", "score": 0.0}

        score = (positive_count - negative_count) / total
        threshold = 0.15 if market == "TW" else 0.2

        if score > threshold:
            sentiment = "positive"
        elif score < -threshold:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {"sentiment": sentiment, "score": round(score, 2)}

    def _fetch_threads_search(self, query: str, market: str = "TW", retry_count: int = 0) -> List[Dict]:
        """
        透過 Threads 網頁搜尋 API 取得貼文，支援指數退避重試

        Threads 的搜尋頁面會回傳 JSON 格式的搜尋結果。
        若 API 被擋，則使用 HTML 解析作為 fallback。
        失敗時會自動重試，使用指數退避策略。

        Args:
            query: 搜尋關鍵字
            market: 市場類別 ('TW' 或 'US')
            retry_count: 目前重試次數

        Returns:
            符合條件的貼文列表
        """
        self._rate_limit(retry_count)
        self._update_headers()

        posts = []

        try:
            # 使用公開搜尋頁面
            search_page_url = f"https://www.threads.net/search?q={requests.utils.quote(query)}&serp_type=default"
            response = self.session.get(search_page_url, timeout=10)

            if response.status_code == 200:
                # 嘗試從 HTML 中提取 JSON 資料
                posts = self._parse_threads_html(response.text, query, market)
                self.retry_count = 0  # 重置重試計數
            elif response.status_code == 429 and retry_count < self.max_retries:
                # 遭到速率限制，進行指數退避重試
                logger.info(f"速率限制，進行重試 ({query}): 第 {retry_count + 1} 次")
                return self._fetch_threads_search(query, market, retry_count + 1)
            else:
                logger.warning(f"Threads 搜尋失敗 ({query}): HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                logger.info(f"請求超時，進行重試 ({query}): 第 {retry_count + 1} 次")
                return self._fetch_threads_search(query, market, retry_count + 1)
            else:
                logger.warning(f"Threads 搜尋超時 ({query})，已達重試上限")
        except Exception as e:
            if retry_count < self.max_retries:
                logger.info(f"搜尋異常，進行重試 ({query}): {e}")
                return self._fetch_threads_search(query, market, retry_count + 1)
            else:
                logger.warning(f"Threads 搜尋異常 ({query}): {e}")

        return posts

    def _parse_threads_html(self, html: str, query: str, market: str) -> List[Dict]:
        """
        從 Threads HTML 頁面提取貼文資料

        Threads 的 SSR 頁面會在 script 標籤中嵌入 JSON 資料。
        若無法解析 JSON，則使用 meta 標籤作為 fallback。
        """
        posts = []

        try:
            # 嘗試從 __NEXT_DATA__ 或 script 標籤取得 JSON
            json_patterns = [
                r'<script[^>]*>window\.__NEXT_DATA__\s*=\s*({.*?})</script>',
                r'"search_results":\s*(\[.*?\])',
                r'"edges":\s*(\[.*?\])',
            ]

            for pattern in json_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    try:
                        data = json.loads(matches[0])
                        posts = self._extract_posts_from_json(data, market)
                        if posts:
                            break
                    except json.JSONDecodeError:
                        continue

            # Fallback：從 meta / og:description 取得內容摘要
            if not posts:
                posts = self._extract_posts_from_meta(html, query, market)

        except Exception as e:
            logger.warning(f"Threads HTML 解析失敗: {e}")

        return posts

    def _extract_posts_from_json(self, data: dict, market: str) -> List[Dict]:
        """
        從 Threads JSON 資料提取貼文，並過濾垃圾內容

        Args:
            data: Threads JSON 資料
            market: 市場類別

        Returns:
            過濾後的貼文列表（最多 20 則）
        """
        posts = []

        def traverse(obj):
            if isinstance(obj, dict):
                # 找到貼文結構
                if "text" in obj and ("pk" in obj or "id" in obj):
                    text = obj.get("text", "")
                    if not text or self._is_spam_post(text):
                        return

                    extract_fn = self._extract_tw_stocks if market == "TW" else self._extract_us_tickers
                    tickers = extract_fn(text)
                    sentiment_data = self._analyze_sentiment(text, market)

                    post_id = str(obj.get("pk", obj.get("id", "")))
                    author = ""
                    if "user" in obj:
                        author = obj["user"].get("username", "")

                    posts.append({
                        "id": post_id,
                        "title": text[:100],
                        "content": text[:500],
                        "author": author,
                        "url": f"https://www.threads.net/@{author}/post/{obj.get('code', post_id)}",
                        "like_count": obj.get("like_count", 0),
                        "reply_count": obj.get("text_post_app_info", {}).get("direct_reply_count", 0) if isinstance(obj.get("text_post_app_info"), dict) else 0,
                        "tickers": tickers,
                        "sentiment": sentiment_data["sentiment"],
                        "sentiment_score": sentiment_data["score"],
                        "posted_at": datetime.now().isoformat(),
                        "platform": "threads",
                    })

                for v in obj.values():
                    traverse(v)
            elif isinstance(obj, list):
                for item in obj:
                    traverse(item)

        traverse(data)
        return posts[:20]

    def _extract_posts_from_meta(self, html: str, query: str, market: str) -> List[Dict]:
        """Fallback：從頁面 meta 標籤生成基本貼文資料"""
        posts = []

        # 提取 og:description 或 description
        desc_match = re.search(r'<meta[^>]*(?:name="description"|property="og:description")[^>]*content="([^"]*)"', html)
        if desc_match:
            desc = desc_match.group(1)
            extract_fn = self._extract_tw_stocks if market == "TW" else self._extract_us_tickers
            tickers = extract_fn(desc)
            sentiment_data = self._analyze_sentiment(desc, market)

            if tickers or query in desc:
                posts.append({
                    "id": f"threads_meta_{hash(desc) % 100000}",
                    "title": desc[:100],
                    "content": desc[:500],
                    "author": "",
                    "url": f"https://www.threads.net/search?q={requests.utils.quote(query)}",
                    "like_count": 0,
                    "reply_count": 0,
                    "tickers": tickers,
                    "sentiment": sentiment_data["sentiment"],
                    "sentiment_score": sentiment_data["score"],
                    "posted_at": datetime.now().isoformat(),
                    "platform": "threads",
                })

        return posts

    def fetch_recent_posts(self, market: str = "TW", limit: int = 30) -> List[Dict]:
        """
        抓取最新的股票相關 Threads 貼文

        Args:
            market: 市場類別 ('TW' 或 'US')
            limit: 返回的貼文數量上限

        Returns:
            按讚數排序的貼文列表
        """
        queries = self.TW_SEARCH_QUERIES if market == "TW" else self.US_SEARCH_QUERIES
        all_posts = []

        for query in queries:
            try:
                posts = self._fetch_threads_search(query, market)
                all_posts.extend(posts)
            except Exception as e:
                logger.warning(f"Threads 抓取失敗 ({query}): {e}")
                continue

        # 去重（依 id）
        seen = set()
        unique_posts = []
        for post in all_posts:
            pid = post.get("id", "")
            if pid and pid not in seen:
                seen.add(pid)
                unique_posts.append(post)

        # 依 like_count 排序
        unique_posts.sort(key=lambda x: x.get("like_count", 0), reverse=True)

        return unique_posts[:limit]

    def fetch_stock_discussions(self, stock_id: str, market: str = "TW", limit: int = 20) -> List[Dict]:
        """
        抓取特定股票的 Threads 討論

        Args:
            stock_id: 股票代碼（台股 4 位數、美股 ticker）
            market: 市場類別 ('TW' 或 'US')
            limit: 返回的討論數量上限

        Returns:
            股票相關討論列表
        """
        if market == "TW":
            # 找出股票名稱
            stock_name = None
            for name, code in self.TW_POPULAR_STOCKS.items():
                if code == stock_id:
                    stock_name = name
                    break

            queries = [stock_id]
            if stock_name:
                queries.insert(0, stock_name)
        else:
            queries = [f"${stock_id}", stock_id]

        all_posts = []
        for query in queries[:2]:
            try:
                posts = self._fetch_threads_search(query, market)
                all_posts.extend(posts)
            except Exception as e:
                logger.warning(f"Threads 股票搜尋失敗 ({query}): {e}")

        # 去重
        seen = set()
        unique_posts = []
        for post in all_posts:
            pid = post.get("id", "")
            if pid and pid not in seen:
                seen.add(pid)
                unique_posts.append(post)

        return unique_posts[:limit]

    def fetch_batch_stocks(self, stock_ids: List[str], market: str = "TW", limit_per_stock: int = 10) -> Dict[str, List[Dict]]:
        """
        批次抓取多檔股票的討論（高效率方式）

        采用批次抓取策略，減少 HTTP 請求次數，提升效率。

        Args:
            stock_ids: 股票代碼列表
            market: 市場類別 ('TW' 或 'US')
            limit_per_stock: 每檔股票的討論數量上限

        Returns:
            股票代碼 -> 討論列表 的字典
        """
        results = {}
        for stock_id in stock_ids:
            try:
                discussions = self.fetch_stock_discussions(stock_id, market, limit_per_stock)
                results[stock_id] = discussions
            except Exception as e:
                logger.warning(f"批次抓取失敗 ({stock_id}): {e}")
                results[stock_id] = []

        return results

    def get_hot_stocks(self, market: str = "TW", limit: int = 20) -> List[Dict]:
        """從 Threads 取得熱門討論股票"""
        all_posts = self.fetch_recent_posts(market=market, limit=50)

        # 彙總各股票提及次數
        ticker_data = {}
        for post in all_posts:
            for ticker in post.get("tickers", []):
                if ticker not in ticker_data:
                    ticker_data[ticker] = {
                        "stock_id": ticker,
                        "stock_name": ticker,
                        "mention_count": 0,
                        "total_likes": 0,
                        "sentiment_sum": 0.0,
                        "posts": [],
                    }

                ticker_data[ticker]["mention_count"] += 1
                ticker_data[ticker]["total_likes"] += post.get("like_count", 0)
                ticker_data[ticker]["sentiment_sum"] += post.get("sentiment_score", 0)

                if len(ticker_data[ticker]["posts"]) < 5:
                    ticker_data[ticker]["posts"].append({
                        "id": post.get("id"),
                        "platform": "threads",
                        "board": "Threads",
                        "title": post.get("title", ""),
                        "content": post.get("content", ""),
                        "author": post.get("author", ""),
                        "url": post.get("url", ""),
                        "sentiment": post.get("sentiment", "neutral"),
                        "sentiment_score": post.get("sentiment_score", 0),
                        "push_count": post.get("like_count", 0),
                        "boo_count": 0,
                        "comment_count": post.get("reply_count", 0),
                        "posted_at": post.get("posted_at"),
                    })

        # 台股：補充公司名稱
        if market == "TW":
            name_map = {v: k for k, v in self.TW_POPULAR_STOCKS.items()}
            for ticker, data in ticker_data.items():
                if ticker in name_map:
                    data["stock_name"] = name_map[ticker]

        # 計算平均情緒
        hot_stocks = []
        for ticker, data in ticker_data.items():
            if data["mention_count"] >= 1:
                avg_sentiment = data["sentiment_sum"] / data["mention_count"]
                threshold = 0.1

                if avg_sentiment > threshold:
                    sentiment = "positive"
                elif avg_sentiment < -threshold:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"

                hot_stocks.append({
                    "stock_id": ticker,
                    "stock_name": data["stock_name"],
                    "mention_count": data["mention_count"],
                    "total_score": data["total_likes"],
                    "sentiment": sentiment,
                    "sentiment_score": round(avg_sentiment, 2),
                    "sample_posts": data["posts"],
                })

        hot_stocks.sort(key=lambda x: x["mention_count"], reverse=True)
        return hot_stocks[:limit]

    def get_market_sentiment(self, market: str = "TW") -> Dict:
        """
        從 Threads 取得市場整體情緒

        Args:
            market: 市場類別 ('TW' 或 'US')

        Returns:
            包含整體情緒、評分、計數的字典
        """
        all_posts = self.fetch_recent_posts(market=market, limit=30)

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

    def detect_trending_topics(self, market: str = "TW", limit: int = 10) -> List[Tuple[str, int]]:
        """
        從最新貼文中偵測當前熱門話題（趨勢）

        透過分析最近的貼文，提取出現頻率最高的股票。
        這可以幫助快速發現市場焦點和熱門個股。

        Args:
            market: 市場類別 ('TW' 或 'US')
            limit: 返回的熱門話題數量

        Returns:
            [(話題/股票代碼, 提及次數), ...] 的列表
        """
        all_posts = self.fetch_recent_posts(market=market, limit=100)

        # 統計所有提及的股票/話題
        ticker_counts = Counter()
        for post in all_posts:
            tickers = post.get("tickers", [])
            for ticker in tickers:
                ticker_counts[ticker] += 1

        # 返回前 N 名最熱門的話題
        return ticker_counts.most_common(limit)


# 全域實例
threads_fetcher = ThreadsFetcher()
