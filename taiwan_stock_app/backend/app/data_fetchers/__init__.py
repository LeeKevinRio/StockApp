"""
Data fetchers for external APIs
核心 fetcher 直接 import，新增的 fetcher 延遲載入避免影響啟動
"""
from .finmind_fetcher import FinMindFetcher
from .fugle_fetcher import FugleFetcher
from .twse_fetcher import TWSEFetcher
from .us_stock_fetcher import USStockFetcher
from .global_news_fetcher import GlobalNewsFetcher
from .macro_data_fetcher import MacroDataFetcher
from .fred_fetcher import FREDFetcher

# 以下模組被大幅修改過，改為延遲載入避免 import 錯誤影響核心功能
# 使用方式：from app.data_fetchers.reddit_fetcher import RedditFetcher
# 使用方式：from app.data_fetchers.threads_fetcher import ThreadsFetcher
# 使用方式：from app.data_fetchers.taiwan_social_fetcher import TaiwanSocialFetcher
# 使用方式：from app.data_fetchers.enhanced_news_fetcher import EnhancedNewsFetcher

__all__ = [
    "FinMindFetcher",
    "FugleFetcher",
    "TWSEFetcher",
    "USStockFetcher",
    "GlobalNewsFetcher",
    "MacroDataFetcher",
    "FREDFetcher",
]
