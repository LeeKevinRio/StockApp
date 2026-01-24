"""
新聞資料爬蟲
從多個來源獲取台股相關新聞
"""
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup

# 設置日誌
logger = logging.getLogger(__name__)


class NewsFetcher:
    """新聞爬蟲服務"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    async def fetch_stock_news(self, stock_id: str, limit: int = 10) -> List[Dict]:
        """
        獲取個股新聞
        使用多個來源確保可用性
        """
        news_list = []

        # 優先順序：鉅亨網搜尋 > 鉅亨網分類 > Yahoo
        sources = [
            ('鉅亨網搜尋', self._fetch_cnyes_search_news),
            ('鉅亨網分類', self._fetch_cnyes_news),
            ('Yahoo', self._fetch_yahoo_news),
        ]

        for source_name, fetch_func in sources:
            try:
                source_news = await fetch_func(stock_id, limit)
                if source_news:
                    logger.info(f"從 {source_name} 獲取到 {len(source_news)} 條新聞")
                    news_list.extend(source_news)
            except Exception as e:
                logger.warning(f"{source_name} 新聞獲取失敗: {e}")

        if not news_list:
            logger.warning(f"所有新聞來源都失敗，股票代碼: {stock_id}")

        # 去重並排序
        seen_titles = set()
        unique_news = []
        for news in news_list:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                unique_news.append(news)

        # 按發布時間排序
        unique_news.sort(key=lambda x: x.get('published_at') or datetime.now(), reverse=True)

        return unique_news[:limit]

    async def fetch_market_news(self, limit: int = 20) -> List[Dict]:
        """
        獲取市場總體新聞
        """
        news_list = []

        try:
            # 市場概況新聞
            market_news = await self._fetch_market_overview_news(limit)
            news_list.extend(market_news)
        except Exception as e:
            logger.error(f"市場新聞獲取失敗: {e}")

        return news_list[:limit]

    async def _fetch_cnyes_search_news(self, stock_id: str, limit: int) -> List[Dict]:
        """從鉅亨網搜尋 API 獲取新聞（最可靠的方式）"""
        news_list = []

        # 使用搜尋 API
        url = "https://api.cnyes.com/media/api/v1/search"
        params = {
            'q': stock_id,
            'limit': limit * 2,  # 多獲取一些以備過濾
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    logger.info(f"鉅亨網搜尋 API 響應狀態: {response.status}")

                    if response.status == 200:
                        data = await response.json()

                        # 嘗試多種數據路徑
                        items = []
                        if 'items' in data and 'data' in data['items']:
                            items = data['items']['data']
                        elif 'data' in data:
                            items = data['data']
                        elif isinstance(data, list):
                            items = data

                        logger.info(f"鉅亨網搜尋返回 {len(items)} 條新聞")

                        for item in items[:limit]:
                            news_id = item.get('newsId') or item.get('id', '')
                            publish_at = item.get('publishAt') or item.get('publish_at', 0)

                            news_list.append({
                                'title': item.get('title', ''),
                                'summary': item.get('summary', item.get('content', '')[:200] if item.get('content') else ''),
                                'source': '鉅亨網',
                                'source_url': f"https://news.cnyes.com/news/id/{news_id}" if news_id else '',
                                'published_at': datetime.fromtimestamp(publish_at) if publish_at else None,
                                'content': None,
                                'sentiment': None,
                            })
                    else:
                        logger.warning(f"鉅亨網搜尋 API 請求失敗: {response.status}")

        except asyncio.TimeoutError:
            logger.error("鉅亨網搜尋 API 請求超時")
        except Exception as e:
            logger.error(f"鉅亨網搜尋新聞解析錯誤: {e}")

        return news_list

    async def _fetch_cnyes_news(self, stock_id: str, limit: int) -> List[Dict]:
        """從鉅亨網分類 API 獲取新聞"""
        news_list = []

        # 鉅亨網分類 API
        url = f"https://api.cnyes.com/media/api/v1/newslist/category/tw_stock_{stock_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    logger.info(f"鉅亨網分類 API 響應狀態: {response.status}")

                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', {}).get('data', [])

                        logger.info(f"鉅亨網分類返回 {len(items)} 條新聞")

                        for item in items[:limit]:
                            news_list.append({
                                'title': item.get('title', ''),
                                'summary': item.get('summary', ''),
                                'source': '鉅亨網',
                                'source_url': f"https://news.cnyes.com/news/id/{item.get('newsId', '')}",
                                'published_at': datetime.fromtimestamp(item.get('publishAt', 0)) if item.get('publishAt') else None,
                                'content': None,
                                'sentiment': None,
                            })
        except asyncio.TimeoutError:
            logger.error("鉅亨網分類 API 請求超時")
        except Exception as e:
            logger.error(f"鉅亨網分類新聞解析錯誤: {e}")

        return news_list

    async def _fetch_yahoo_news(self, stock_id: str, limit: int) -> List[Dict]:
        """從 Yahoo 財經獲取新聞"""
        news_list = []

        # Yahoo 台股新聞頁面
        url = f"https://tw.stock.yahoo.com/quote/{stock_id}.TW/news"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    logger.info(f"Yahoo 新聞頁面響應狀態: {response.status}")

                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # 嘗試多種選擇器
                        selectors = [
                            ('li', {'class_': re.compile(r'.*StreamMegaItem.*')}),
                            ('div', {'class_': re.compile(r'Py\(14px\)')}),
                            ('li', {'class_': re.compile(r'js-stream-content')}),
                            ('div', {'data-test-locator': 'mega'}),
                        ]

                        news_items = []
                        for tag, attrs in selectors:
                            news_items = soup.find_all(tag, **attrs)
                            if news_items:
                                logger.info(f"Yahoo 使用選擇器 {tag} 找到 {len(news_items)} 條新聞")
                                break

                        if not news_items:
                            logger.warning("Yahoo 所有選擇器都未找到新聞")

                        for item in news_items[:limit]:
                            try:
                                title_elem = item.find('h3') or item.find('a')
                                link_elem = item.find('a')
                                time_elem = item.find('time')

                                if title_elem:
                                    href = link_elem.get('href', '') if link_elem else ''
                                    if href and not href.startswith('http'):
                                        href = f"https://tw.stock.yahoo.com{href}"

                                    news_list.append({
                                        'title': title_elem.get_text(strip=True),
                                        'source': 'Yahoo財經',
                                        'source_url': href,
                                        'published_at': self._parse_relative_time(time_elem.get_text(strip=True) if time_elem else ''),
                                        'content': None,
                                        'sentiment': None,
                                    })
                            except Exception as e:
                                logger.debug(f"Yahoo 解析單條新聞失敗: {e}")
                                continue

        except asyncio.TimeoutError:
            logger.error("Yahoo 新聞頁面請求超時")
        except Exception as e:
            logger.error(f"Yahoo 新聞解析錯誤: {e}")

        return news_list

    async def _fetch_market_overview_news(self, limit: int) -> List[Dict]:
        """獲取市場概況新聞"""
        news_list = []

        # 鉅亨網台股焦點
        url = "https://api.cnyes.com/media/api/v1/newslist/category/tw_stock"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', {}).get('data', [])

                        for item in items[:limit]:
                            news_list.append({
                                'title': item.get('title', ''),
                                'summary': item.get('summary', ''),
                                'source': '鉅亨網',
                                'source_url': f"https://news.cnyes.com/news/id/{item.get('newsId', '')}",
                                'published_at': datetime.fromtimestamp(item.get('publishAt', 0)) if item.get('publishAt') else None,
                                'content': None,
                                'sentiment': None,
                            })
        except Exception as e:
            logger.error(f"市場新聞解析錯誤: {e}")

        return news_list

    def _parse_relative_time(self, time_str: str) -> Optional[datetime]:
        """解析相對時間字串"""
        if not time_str:
            return None

        now = datetime.now()

        try:
            if '分鐘前' in time_str:
                match = re.search(r'(\d+)', time_str)
                if match:
                    minutes = int(match.group(1))
                    return now - timedelta(minutes=minutes)
            elif '小時前' in time_str:
                match = re.search(r'(\d+)', time_str)
                if match:
                    hours = int(match.group(1))
                    return now - timedelta(hours=hours)
            elif '天前' in time_str:
                match = re.search(r'(\d+)', time_str)
                if match:
                    days = int(match.group(1))
                    return now - timedelta(days=days)
            elif '昨天' in time_str:
                return now - timedelta(days=1)
        except Exception:
            pass

        return None

    def analyze_sentiment_simple(self, title: str, content: str = None) -> Dict:
        """
        簡單的情緒分析
        基於關鍵詞判斷
        """
        text = f"{title} {content or ''}"

        positive_keywords = [
            '漲', '飆', '攀升', '突破', '創新高', '利多', '看好', '樂觀',
            '成長', '獲利', '營收', '增加', '超預期', '強勢', '買進',
            '紅盤', '反彈', '回升', '上揚', '衝高'
        ]

        negative_keywords = [
            '跌', '崩', '下挫', '暴跌', '創新低', '利空', '看壞', '悲觀',
            '虧損', '下滑', '減少', '低於預期', '弱勢', '賣出',
            '綠盤', '下跌', '重挫', '走低', '殺低'
        ]

        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)

        if positive_count > negative_count:
            sentiment = 'positive'
            score = min(positive_count / (positive_count + negative_count + 1), 1.0)
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = -min(negative_count / (positive_count + negative_count + 1), 1.0)
        else:
            sentiment = 'neutral'
            score = 0.0

        return {
            'sentiment': sentiment,
            'score': round(score, 2)
        }


# 單例
news_fetcher = NewsFetcher()
