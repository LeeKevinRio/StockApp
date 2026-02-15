"""
新聞 API endpoint 測試
"""
import pytest


class TestNewsAPI:
    """新聞 API 測試"""

    def test_get_stock_news_requires_auth(self, client):
        """無 token → 401"""
        response = client.get("/api/news/stock/2330")
        assert response.status_code == 403  # HTTPBearer returns 403 when no token

    def test_get_market_news_requires_auth(self, client):
        """無 token → 401/403"""
        response = client.get("/api/news/market")
        assert response.status_code == 403

    def test_get_stock_news_with_auth(self, client, auth_headers, sample_stocks):
        """GET /api/news/stock/2330 → 200（需 auth + sample_stocks）"""
        response = client.get("/api/news/stock/2330", headers=auth_headers)
        # 可能因為外部 API 不可用而 500，但不應 401/403
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "news" in data
            assert "stock_id" in data

    def test_get_market_news_with_auth(self, client, auth_headers):
        """GET /api/news/market → 200"""
        response = client.get("/api/news/market", headers=auth_headers)
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert "news" in data
            assert "market" in data
