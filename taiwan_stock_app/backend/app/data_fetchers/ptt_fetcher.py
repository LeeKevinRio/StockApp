"""
PTT 爬蟲服務
從 PTT Stock 看板獲取股票討論
"""
import aiohttp
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


class PTTFetcher:
    """PTT 爬蟲"""

    def __init__(self):
        self.base_url = "https://www.ptt.cc"
        self.stock_board = "/bbs/Stock/index.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': 'over18=1'  # 確認已滿18歲
        }
        # 台股代碼正則
        self.stock_pattern = re.compile(r'\b(\d{4})\b')

    async def fetch_recent_posts(self, pages: int = 3) -> List[Dict]:
        """
        獲取最近的貼文

        Args:
            pages: 要爬取的頁數

        Returns:
            貼文列表
        """
        posts = []

        try:
            async with aiohttp.ClientSession() as session:
                # 獲取最新頁面
                current_url = self.base_url + self.stock_board

                for _ in range(pages):
                    page_posts, prev_url = await self._fetch_page(session, current_url)
                    posts.extend(page_posts)

                    if not prev_url:
                        break
                    current_url = self.base_url + prev_url

        except Exception as e:
            print(f"PTT 爬取錯誤: {e}")

        return posts

    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> tuple:
        """獲取單頁貼文"""
        posts = []
        prev_url = None

        try:
            async with session.get(url, headers=self.headers, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # 獲取上一頁連結
                    paging = soup.find('div', class_='btn-group-paging')
                    if paging:
                        prev_link = paging.find_all('a')[1]  # 上頁
                        if prev_link and 'href' in prev_link.attrs:
                            prev_url = prev_link['href']

                    # 解析貼文列表
                    entries = soup.find_all('div', class_='r-ent')

                    for entry in entries:
                        try:
                            post = self._parse_entry(entry)
                            if post:
                                posts.append(post)
                        except Exception:
                            continue

        except Exception as e:
            print(f"頁面解析錯誤: {e}")

        return posts, prev_url

    def _parse_entry(self, entry) -> Optional[Dict]:
        """解析單個貼文條目"""
        title_elem = entry.find('div', class_='title')
        if not title_elem:
            return None

        link = title_elem.find('a')
        if not link:
            return None

        title = link.get_text(strip=True)
        url = self.base_url + link['href']

        # 提取推/噓數
        nrec = entry.find('div', class_='nrec')
        push_count = 0
        if nrec:
            nrec_text = nrec.get_text(strip=True)
            if nrec_text == '爆':
                push_count = 100
            elif nrec_text.startswith('X'):
                push_count = -10
            elif nrec_text.isdigit():
                push_count = int(nrec_text)

        # 提取作者
        author_elem = entry.find('div', class_='author')
        author = author_elem.get_text(strip=True) if author_elem else None

        # 提取日期
        date_elem = entry.find('div', class_='date')
        posted_at = None
        if date_elem:
            date_str = date_elem.get_text(strip=True)
            try:
                # PTT 日期格式: "1/24" (月/日)
                month, day = map(int, date_str.split('/'))
                year = datetime.now().year
                posted_at = datetime(year, month, day)
            except Exception:
                pass

        # 提取提及的股票代碼
        mentioned_stocks = self._extract_stock_ids(title)

        # 分析情緒
        sentiment_result = self._analyze_sentiment(title)

        return {
            'platform': 'ptt',
            'board': 'Stock',
            'title': title,
            'url': url,
            'author': author,
            'push_count': max(push_count, 0),
            'boo_count': abs(min(push_count, 0)),
            'mentioned_stocks': mentioned_stocks,
            'sentiment': sentiment_result['sentiment'],
            'sentiment_score': sentiment_result['score'],
            'posted_at': posted_at,
        }

    def _extract_stock_ids(self, text: str) -> List[str]:
        """從文字中提取股票代碼"""
        matches = self.stock_pattern.findall(text)
        # 過濾掉不太可能是股票代碼的數字
        valid_ids = [m for m in matches if 1000 <= int(m) <= 9999]
        return list(set(valid_ids))

    def _analyze_sentiment(self, text: str) -> Dict:
        """簡單的情緒分析"""
        positive_keywords = [
            '多', '漲', '噴', '飆', '買', '進場', '看好', '利多',
            '突破', '強勢', '紅', '賺', '爽', '讚', '推',
        ]
        negative_keywords = [
            '空', '跌', '崩', '殺', '賣', '出場', '看壞', '利空',
            '跌破', '弱勢', '綠', '賠', '慘', '爛', '噓',
        ]

        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)

        if positive_count > negative_count:
            return {'sentiment': 'positive', 'score': min(positive_count * 0.2, 1.0)}
        elif negative_count > positive_count:
            return {'sentiment': 'negative', 'score': -min(negative_count * 0.2, 1.0)}
        else:
            return {'sentiment': 'neutral', 'score': 0.0}

    async def fetch_stock_discussions(self, stock_id: str, limit: int = 20) -> List[Dict]:
        """
        獲取特定股票的討論

        Args:
            stock_id: 股票代碼
            limit: 返回數量限制

        Returns:
            相關貼文列表
        """
        all_posts = await self.fetch_recent_posts(pages=5)

        # 過濾包含該股票代碼的貼文
        stock_posts = [
            post for post in all_posts
            if stock_id in post.get('mentioned_stocks', []) or stock_id in post.get('title', '')
        ]

        return stock_posts[:limit]

    async def get_hot_stocks(self, limit: int = 10) -> List[Dict]:
        """
        獲取熱門討論股票

        Returns:
            熱門股票列表
        """
        all_posts = await self.fetch_recent_posts(pages=5)

        # 統計股票提及次數
        stock_mentions = {}
        stock_sentiments = {}

        for post in all_posts:
            for stock_id in post.get('mentioned_stocks', []):
                if stock_id not in stock_mentions:
                    stock_mentions[stock_id] = 0
                    stock_sentiments[stock_id] = []
                stock_mentions[stock_id] += 1
                if post.get('sentiment_score') is not None:
                    stock_sentiments[stock_id].append(post['sentiment_score'])

        # 排序並返回
        hot_stocks = []
        for stock_id, count in sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)[:limit]:
            scores = stock_sentiments.get(stock_id, [])
            avg_score = sum(scores) / len(scores) if scores else 0

            sentiment = 'positive' if avg_score > 0.1 else ('negative' if avg_score < -0.1 else 'neutral')

            hot_stocks.append({
                'stock_id': stock_id,
                'mention_count': count,
                'sentiment_score': round(avg_score, 2),
                'sentiment': sentiment,
            })

        return hot_stocks


# 單例
ptt_fetcher = PTTFetcher()
