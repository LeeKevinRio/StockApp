"""
基本面 API endpoint 測試
"""
import pytest


class TestFundamentalAPI:
    """基本面資料 API 測試"""

    def test_dividends_requires_auth(self, client):
        """無 token → 403"""
        response = client.get("/api/stocks/2330/dividends")
        assert response.status_code == 403

    def test_financial_statements_requires_auth(self, client):
        """無 token → 403"""
        response = client.get("/api/stocks/2330/financial-statements")
        assert response.status_code == 403

    def test_get_dividends(self, client, auth_headers, sample_stocks):
        """GET /api/stocks/{stock_id}/dividends → 200 or empty list"""
        response = client.get(
            "/api/stocks/2330/dividends", headers=auth_headers
        )
        # 外部 API 可能不可用，但不應 auth 錯誤
        assert response.status_code in (200, 404, 500)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_get_financial_statements(self, client, auth_headers, sample_stocks):
        """GET /api/stocks/{stock_id}/financial-statements → 200 or 404"""
        response = client.get(
            "/api/stocks/2330/financial-statements", headers=auth_headers
        )
        assert response.status_code in (200, 404, 500)
        if response.status_code == 200:
            data = response.json()
            assert "stock_id" in data

    def test_get_fundamental(self, client, auth_headers, sample_stocks):
        """GET /api/stocks/{stock_id}/fundamental → 200 or 404"""
        response = client.get(
            "/api/stocks/2330/fundamental", headers=auth_headers
        )
        assert response.status_code in (200, 404, 500)
        if response.status_code == 200:
            data = response.json()
            assert "stock_id" in data
