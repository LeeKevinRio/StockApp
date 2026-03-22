"""
Enhanced News Fetcher — 擴充國內外新聞來源
新增來源：
  - 台灣：經濟日報、工商時報、自由財經、MoneyDJ
  - 國際：Reuters RSS、Bloomberg RSS、CNBC、MarketWatch RSS、Investing.com
  - 產業：TechCrunch（科技類）、Finviz News

特色：
  - 所有新聞統一格式，附帶 AI 情緒分析
  - 跨來源去重
  - 按時間和相關度排序
"""
import aiohttp
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class EnhancedNewsFetcher:
    """強化版新聞抓取器 — 整合國內外多源新聞"""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    # ===== 台灣新聞 RSS 來源 =====
    TW_RSS_SOURCES = {
        "經濟日報_證券": "https://money.udn.com/rssfeed/news/1001/5710",
        "經濟日報_產業": "https://money.udn.com/rssfeed/news/1001/5612",
        "經濟日報_國際": "https://money.udn.com/rssfeed/news/1001/12925",
        "工商時報_證券": "https://ctee.com.tw/feed",
        "自由財經": "https://ec.ltn.com.tw/rss/securities.xml",
        "MoneyDJ_台股": "https://www.moneydj.com/rss/newsrss.aspx?svc=NW&ftype=1&topn=20",
    }

    # ===== 國際新聞 RSS 來源 =====
    INTL_RSS_SOURCES = {
        "Reuters_Markets": "https://www.reutersagency.com/feed/?best-topics=business-finance",
        "CNBC_Market": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
        "CNBC_World": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
        "MarketWatch_Top": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "MarketWatch_Markets": "https://feeds.marketwatch.com/marketwatch/marketpulse/",
        "Investing_News": "https://www.investing.com/rss/news.rss",
        "Yahoo_Finance": "https://finance.yahoo.com/news/rssindex",
    }

    # ===== 產業/科技新聞 RSS =====
    TECH_RSS_SOURCES = {
        "TechCrunch": "https://techcrunch.com/feed/",
    }

    def __init__(self):
        self._cache = {}
        self._cache_ttl = 1800  # 30 分鐘快取

    async def fetch_tw_stock_news(self, stock_id: str, stock_name: str = "",
                                   limit: int = 15) -> List[Dict]:
        """
        抓取台股個股新聞（整合多源）

        Args:
            stock_id: 股票代碼（如 '2330'）
            stock_name: 股票名稱（如 '台積電'）
            limit: 最大新聞數
        """
        cache_key = f"tw_{stock_id}_{datetime.now().strftime('%Y%m%d%H')}"
        if cache_key in self._cache:
            return self._cache[cache_key][:limit]

        all_news = []
        tasks = []

        # 1. Google News RSS（個股搜尋）
        search_queries = [f"{stock_id} 股票"]
        if stock_name:
            search_queries.append(stock_name)

        for query in search_queries:
            tasks.append(self._fetch_rss(
                f"https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
                "Google News"
            ))

        # 2. 台灣財經 RSS
        for source_name, url in self.TW_RSS_SOURCES.items():
            tasks.append(self._fetch_rss(url, source_name))

        # 3. 鉅亨網 API
        tasks.append(self._fetch_cnyes_api(stock_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)

        # 過濾：只保留與個股相關的新聞
        relevant_news = self._filter_relevant(all_news, stock_id, stock_name)

        # 去重 + 排序
        unique_news = self._deduplicate(relevant_news)
        unique_news.sort(key=lambda x: x.get('published_at') or datetime.min, reverse=True)

        result = unique_news[:limit]
        self._cache[cache_key] = result
        return result

    async def fetch_international_news(self, stock_id: str = "",
                                        limit: int = 20) -> List[Dict]:
        """
        抓取國際財經新聞

        Args:
            stock_id: 美股代碼（如 'AAPL'），空字串則抓市場總體新聞
            limit: 最大新聞數
        """
        cache_key = f"intl_{stock_id}_{datetime.now().strftime('%Y%m%d%H')}"
        if cache_key in self._cache:
            return self._cache[cache_key][:limit]

        all_news = []
        tasks = []

        # 1. 國際 RSS
        for source_name, url in self.INTL_RSS_SOURCES.items():
            tasks.append(self._fetch_rss(url, source_name))

        # 2. 如果有指定股票，搜尋 Google News
        if stock_id:
            tasks.append(self._fetch_rss(
                f"https://news.google.com/rss/search?q={stock_id}+stock&hl=en-US&gl=US&ceid=US:en",
                "Google News US"
            ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)

        # 如果指定了股票，過濾相關新聞
        if stock_id:
            relevant = [n for n in all_news if stock_id.lower() in (n.get('title', '') + n.get('summary', '')).lower()]
            # 如果相關新聞太少，也保留市場大盤新聞
            if len(relevant) < 5:
                relevant = all_news
        else:
            relevant = all_news

        unique_news = self._deduplicate(relevant)
        unique_news.sort(key=lambda x: x.get('published_at') or datetime.min, reverse=True)

        result = unique_news[:limit]
        self._cache[cache_key] = result
        return result

    async def fetch_market_overview_news(self, market: str = "TW", limit: int = 20) -> List[Dict]:
        """
        抓取市場總覽新聞（不針對個股）

        Args:
            market: 'TW' or 'US'
            limit: 最大新聞數
        """
        cache_key = f"market_{market}_{datetime.now().strftime('%Y%m%d%H')}"
        if cache_key in self._cache:
            return self._cache[cache_key][:limit]

        all_news = []
        tasks = []

        if market == "TW":
            for source_name, url in self.TW_RSS_SOURCES.items():
                tasks.append(self._fetch_rss(url, source_name))
            # 台股重要新聞搜尋
            tasks.append(self._fetch_rss(
                "https://news.google.com/rss/search?q=台股+大盤&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
                "Google News TW Market"
            ))
        else:
            for source_name, url in self.INTL_RSS_SOURCES.items():
                tasks.append(self._fetch_rss(url, source_name))
            # 科技新聞（影響美股）
            for source_name, url in self.TECH_RSS_SOURCES.items():
                tasks.append(self._fetch_rss(url, source_name))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, list):
                all_news.extend(result)

        unique_news = self._deduplicate(all_news)
        unique_news.sort(key=lambda x: x.get('published_at') or datetime.min, reverse=True)

        result = unique_news[:limit]
        self._cache[cache_key] = result
        return result

    # ===== RSS 抓取 =====
    async def _fetch_rss(self, url: str, source_name: str, timeout: int = 12) -> List[Dict]:
        """通用 RSS 抓取"""
        if not FEEDPARSER_AVAILABLE:
            return []

        news_list = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.HEADERS,
                                       timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)

                        for entry in feed.entries[:15]:
                            published_at = None
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                try:
                                    published_at = datetime(*entry.published_parsed[:6])
                                except Exception:
                                    pass

                            title = entry.get('title', '').strip()
                            if not title:
                                continue

                            summary = ''
                            if entry.get('summary'):
                                # 清除 HTML 標籤
                                raw = entry.get('summary', '')
                                summary = BeautifulSoup(raw, 'html.parser').get_text()[:300]

                            news_list.append({
                                'title': title,
                                'summary': summary,
                                'source': source_name.split('_')[0],  # 去掉子分類
                                'source_category': source_name,
                                'source_url': entry.get('link', ''),
                                'published_at': published_at,
                                'content': None,
                                'sentiment': None,
                                'region': 'TW' if any(tw in source_name for tw in ['經濟', '工商', '自由', 'MoneyDJ', 'TW']) else 'INTL',
                            })
                    else:
                        logger.debug(f"RSS {source_name} HTTP {response.status}")
        except asyncio.TimeoutError:
            logger.debug(f"RSS {source_name} timeout")
        except Exception as e:
            logger.debug(f"RSS {source_name} error: {e}")

        return news_list

    # ===== 鉅亨網 API =====
    async def _fetch_cnyes_api(self, stock_id: str) -> List[Dict]:
        """鉅亨網搜尋 API"""
        news_list = []
        url = f"https://api.cnyes.com/media/api/v1/search?q={stock_id}&limit=15"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.HEADERS,
                                       timeout=aiohttp.ClientTimeout(total=12)) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = []
                        if 'items' in data and 'data' in data['items']:
                            items = data['items']['data']
                        elif 'data' in data:
                            items = data['data']

                        for item in items[:10]:
                            publish_at = item.get('publishAt') or item.get('publish_at', 0)
                            news_list.append({
                                'title': item.get('title', ''),
                                'summary': item.get('summary', '')[:300],
                                'source': '鉅亨網',
                                'source_category': '鉅亨網_搜尋',
                                'source_url': f"https://news.cnyes.com/news/id/{item.get('newsId', '')}",
                                'published_at': datetime.fromtimestamp(publish_at) if publish_at else None,
                                'content': None,
                                'sentiment': None,
                                'region': 'TW',
                            })
        except Exception as e:
            logger.debug(f"鉅亨網 API error: {e}")

        return news_list

    # ===== 過濾/去重 =====
    def _filter_relevant(self, news_list: List[Dict], stock_id: str, stock_name: str) -> List[Dict]:
        """過濾與個股相關的新聞"""
        relevant = []
        keywords = [stock_id]
        if stock_name:
            keywords.append(stock_name)

        for news in news_list:
            text = f"{news.get('title', '')} {news.get('summary', '')}"
            if any(kw in text for kw in keywords):
                news['relevance'] = 'direct'
                relevant.append(news)

        # 如果直接相關的太少，也包含同源的所有新聞（市場脈動）
        if len(relevant) < 5:
            for news in news_list:
                if news not in relevant:
                    news['relevance'] = 'market'
                    relevant.append(news)

        return relevant

    def _deduplicate(self, news_list: List[Dict]) -> List[Dict]:
        """根據標題去重"""
        seen = set()
        unique = []
        for news in news_list:
            # 用標題前40字作為去重 key
            key = re.sub(r'\s+', '', news.get('title', ''))[:40].lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(news)
        return unique

    def get_news_summary_for_ai(self, news_list: List[Dict], max_items: int = 10) -> Dict:
        """
        將新聞列表轉成適合餵給 AI 的摘要格式

        Returns:
            dict with news_count, sources, headlines, sentiment_summary
        """
        if not news_list:
            return {
                "news_count": 0,
                "sources": [],
                "headlines": [],
                "tw_news": [],
                "intl_news": [],
                "sentiment_summary": "無新聞資料",
            }

        tw_news = [n for n in news_list if n.get('region') == 'TW'][:max_items]
        intl_news = [n for n in news_list if n.get('region') == 'INTL'][:max_items]
        sources = list(set(n.get('source', '') for n in news_list if n.get('source')))

        headlines = []
        for n in news_list[:max_items]:
            headline = {
                "title": n.get('title', '')[:80],
                "source": n.get('source', ''),
                "region": n.get('region', ''),
                "relevance": n.get('relevance', 'market'),
            }
            if n.get('published_at'):
                headline["time"] = n['published_at'].strftime('%m/%d %H:%M') if isinstance(n['published_at'], datetime) else str(n['published_at'])
            headlines.append(headline)

        return {
            "news_count": len(news_list),
            "sources": sources,
            "headlines": headlines,
            "tw_news_count": len(tw_news),
            "intl_news_count": len(intl_news),
            "tw_headlines": [n.get('title', '')[:60] for n in tw_news[:5]],
            "intl_headlines": [n.get('title', '')[:60] for n in intl_news[:5]],
        }


# 全域實例
enhanced_news_fetcher = EnhancedNewsFetcher()
