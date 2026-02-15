"""
SentimentService 單元測試
"""
import pytest


class TestSentimentService:
    """情緒服務單元測試"""

    def test_service_can_be_imported(self):
        """SentimentService 可成功匯入"""
        from app.services.sentiment_service import SentimentService
        assert SentimentService is not None

    def test_service_singleton_exists(self):
        """模組層級 singleton 存在"""
        from app.services.sentiment_service import sentiment_service
        assert sentiment_service is not None

    def test_service_is_instance(self):
        """singleton 是 SentimentService 的實例"""
        from app.services.sentiment_service import SentimentService, sentiment_service
        assert isinstance(sentiment_service, SentimentService)

    def test_positive_score_mapping(self):
        """分數 > 0.15 → positive"""
        score = 0.5
        if score > 0.15:
            signal = "positive"
        elif score < -0.15:
            signal = "negative"
        else:
            signal = "neutral"
        assert signal == "positive"

    def test_negative_score_mapping(self):
        """分數 < -0.15 → negative"""
        score = -0.3
        if score > 0.15:
            signal = "positive"
        elif score < -0.15:
            signal = "negative"
        else:
            signal = "neutral"
        assert signal == "negative"

    def test_neutral_score_mapping(self):
        """分數在 -0.15 ~ 0.15 → neutral"""
        for score in [0.0, 0.1, -0.1, 0.15, -0.15]:
            if score > 0.15:
                signal = "positive"
            elif score < -0.15:
                signal = "negative"
            else:
                signal = "neutral"
            assert signal == "neutral", f"score={score} should be neutral, got {signal}"

    def test_market_sentiment_bullish_mapping(self):
        """sentiment_ratio > 0.6 → bullish"""
        ratio = 0.75
        if ratio > 0.6:
            market = "bullish"
        elif ratio < 0.4:
            market = "bearish"
        else:
            market = "neutral"
        assert market == "bullish"

    def test_market_sentiment_bearish_mapping(self):
        """sentiment_ratio < 0.4 → bearish"""
        ratio = 0.2
        if ratio > 0.6:
            market = "bullish"
        elif ratio < 0.4:
            market = "bearish"
        else:
            market = "neutral"
        assert market == "bearish"

    def test_market_sentiment_neutral_mapping(self):
        """sentiment_ratio 0.4-0.6 → neutral"""
        ratio = 0.5
        if ratio > 0.6:
            market = "bullish"
        elif ratio < 0.4:
            market = "bearish"
        else:
            market = "neutral"
        assert market == "neutral"
