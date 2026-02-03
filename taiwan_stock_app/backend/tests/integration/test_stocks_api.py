"""
Integration tests for stocks API
"""
import pytest
from fastapi.testclient import TestClient


class TestStockSearch:
    """Tests for stock search API"""

    def test_search_by_stock_id(self, client: TestClient, auth_headers, sample_stocks):
        """Test searching by stock ID"""
        response = client.get(
            "/api/stocks/search?q=2330",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(s["stock_id"] == "2330" for s in data)

    def test_search_by_name(self, client: TestClient, auth_headers, sample_stocks):
        """Test searching by stock name"""
        response = client.get(
            "/api/stocks/search?q=台積電",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("台積電" in s["name"] for s in data)

    def test_search_partial_match(self, client: TestClient, auth_headers, sample_stocks):
        """Test searching with partial match"""
        response = client.get(
            "/api/stocks/search?q=23",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should find multiple stocks starting with 23
        assert len(data) >= 1

    def test_search_no_results(self, client: TestClient, auth_headers, sample_stocks):
        """Test searching with no matching results"""
        response = client.get(
            "/api/stocks/search?q=nonexistent999",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_empty_query(self, client: TestClient, auth_headers):
        """Test searching with empty query"""
        response = client.get(
            "/api/stocks/search?q=",
            headers=auth_headers,
        )

        # Should return empty or all stocks
        assert response.status_code == 200


class TestStockDetail:
    """Tests for stock detail API"""

    def test_get_stock_detail(self, client: TestClient, auth_headers, sample_stocks):
        """Test getting stock details"""
        response = client.get(
            "/api/stocks/2330",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stock_id"] == "2330"
        assert data["name"] == "台積電"
        assert "market" in data

    def test_get_nonexistent_stock(self, client: TestClient, auth_headers):
        """Test getting non-existent stock"""
        response = client.get(
            "/api/stocks/9999",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestStockHistory:
    """Tests for stock history API"""

    def test_get_history_default_params(self, client: TestClient, auth_headers, sample_stocks):
        """Test getting stock history with default parameters"""
        response = client.get(
            "/api/stocks/2330/history",
            headers=auth_headers,
        )

        # May return 200 with empty array or 404 depending on data availability
        assert response.status_code in [200, 404]

    def test_get_history_with_days_param(self, client: TestClient, auth_headers, sample_stocks):
        """Test getting stock history with days parameter"""
        response = client.get(
            "/api/stocks/2330/history?days=30",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

    def test_get_history_with_period_param(self, client: TestClient, auth_headers, sample_stocks):
        """Test getting stock history with period parameter"""
        for period in ["day", "week", "month"]:
            response = client.get(
                f"/api/stocks/2330/history?period={period}",
                headers=auth_headers,
            )

            assert response.status_code in [200, 404]


class TestStockIndicators:
    """Tests for stock indicators API"""

    def test_get_rsi(self, client: TestClient, auth_headers, sample_stocks):
        """Test getting RSI indicator"""
        response = client.get(
            "/api/stocks/2330/indicators/rsi",
            headers=auth_headers,
        )

        # May return 200 or 404 depending on data availability
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["stock_id"] == "2330"
            assert "data" in data

    def test_get_macd(self, client: TestClient, auth_headers, sample_stocks):
        """Test getting MACD indicator"""
        response = client.get(
            "/api/stocks/2330/indicators/macd",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

    def test_get_bollinger(self, client: TestClient, auth_headers, sample_stocks):
        """Test getting Bollinger Bands"""
        response = client.get(
            "/api/stocks/2330/indicators/bollinger",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

    def test_get_kd(self, client: TestClient, auth_headers, sample_stocks):
        """Test getting KD indicator"""
        response = client.get(
            "/api/stocks/2330/indicators/kd",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]

    def test_get_all_indicators(self, client: TestClient, auth_headers, sample_stocks):
        """Test getting all indicators"""
        response = client.get(
            "/api/stocks/2330/indicators/all",
            headers=auth_headers,
        )

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["stock_id"] == "2330"
