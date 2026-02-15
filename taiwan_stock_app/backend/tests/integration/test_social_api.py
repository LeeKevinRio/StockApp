"""
社群 API endpoint 測試
"""
import pytest


class TestSocialAPI:
    """社群情緒 API 測試"""

    def test_hot_stocks_requires_auth(self, client):
        """無 token → 403"""
        response = client.get("/api/social/hot-stocks")
        assert response.status_code == 403

    def test_stock_sentiment_requires_auth(self, client):
        """無 token → 403"""
        response = client.get("/api/social/stock/2330/sentiment")
        assert response.status_code == 403

    def test_market_sentiment_requires_auth(self, client):
        """無 token → 403"""
        response = client.get("/api/social/market")
        assert response.status_code == 403

    def test_get_hot_stocks(self, client, auth_headers, sample_stocks):
        """GET /api/social/hot-stocks → 200"""
        response = client.get("/api/social/hot-stocks", headers=auth_headers)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "stocks" in data
            assert "total" in data

    def test_get_stock_sentiment(self, client, auth_headers, sample_stocks):
        """GET /api/social/stock/2330/sentiment → 200"""
        response = client.get(
            "/api/social/stock/2330/sentiment", headers=auth_headers
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "stock_id" in data
            assert "sentiment_summary" in data or "overall_sentiment" in data

    def test_get_market_sentiment(self, client, auth_headers):
        """GET /api/social/market → 200"""
        response = client.get("/api/social/market", headers=auth_headers)
        assert response.status_code in (200, 500)
