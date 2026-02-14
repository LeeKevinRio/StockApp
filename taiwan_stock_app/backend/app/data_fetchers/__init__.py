"""
Data fetchers for external APIs
"""
from .finmind_fetcher import FinMindFetcher
from .fugle_fetcher import FugleFetcher
from .twse_fetcher import TWSEFetcher
from .us_stock_fetcher import USStockFetcher
from .reddit_fetcher import RedditFetcher
from .global_news_fetcher import GlobalNewsFetcher
from .taiwan_social_fetcher import TaiwanSocialFetcher
from .macro_data_fetcher import MacroDataFetcher
from .fred_fetcher import FREDFetcher

__all__ = [
    "FinMindFetcher",
    "FugleFetcher",
    "TWSEFetcher",
    "USStockFetcher",
    "RedditFetcher",
    "GlobalNewsFetcher",
    "TaiwanSocialFetcher",
    "MacroDataFetcher",
    "FREDFetcher",
]
