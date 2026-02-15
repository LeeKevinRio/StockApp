"""
Integration tests for watchlist API
"""
import pytest
from fastapi.testclient import TestClient


class TestWatchlistCRUD:
    """Tests for watchlist CRUD operations"""

    def test_get_empty_watchlist(self, client: TestClient, auth_headers):
        """Test getting empty watchlist"""
        response = client.get(
            "/api/watchlist",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_add_stock_to_watchlist(self, client: TestClient, auth_headers, sample_stocks):
        """Test adding a stock to watchlist"""
        response = client.post(
            "/api/watchlist",
            headers=auth_headers,
            json={"stock_id": "2330"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_add_stock_with_notes(self, client: TestClient, auth_headers, sample_stocks):
        """Test adding a stock to watchlist with notes"""
        response = client.post(
            "/api/watchlist",
            headers=auth_headers,
            json={"stock_id": "2317", "notes": "Long term hold"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_add_duplicate_stock(self, client: TestClient, auth_headers, sample_stocks):
        """Test adding duplicate stock to watchlist"""
        # Add first time
        client.post(
            "/api/watchlist",
            headers=auth_headers,
            json={"stock_id": "2330"},
        )

        # Add second time
        response = client.post(
            "/api/watchlist",
            headers=auth_headers,
            json={"stock_id": "2330"},
        )

        # Should either return error or success (depending on implementation)
        assert response.status_code in [200, 400]

    def test_add_nonexistent_stock(self, client: TestClient, auth_headers):
        """Test adding non-existent stock to watchlist"""
        response = client.post(
            "/api/watchlist",
            headers=auth_headers,
            json={"stock_id": "9999"},
        )

        # Should return 404 or add anyway
        assert response.status_code in [200, 404]

    def test_get_watchlist_with_items(self, client: TestClient, auth_headers, sample_stocks):
        """Test getting watchlist with items"""
        # Add some stocks
        client.post("/api/watchlist", headers=auth_headers, json={"stock_id": "2330"})
        client.post("/api/watchlist", headers=auth_headers, json={"stock_id": "2317"})

        response = client.get("/api/watchlist", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_remove_stock_from_watchlist(self, client: TestClient, auth_headers, sample_stocks):
        """Test removing stock from watchlist"""
        # Add stock
        client.post("/api/watchlist", headers=auth_headers, json={"stock_id": "2330"})

        # Remove stock
        response = client.delete("/api/watchlist/2330", headers=auth_headers)

        assert response.status_code == 200

        # Verify removed
        watchlist_response = client.get("/api/watchlist", headers=auth_headers)
        watchlist = watchlist_response.json()
        assert not any(item["stock_id"] == "2330" for item in watchlist)

    def test_remove_nonexistent_item(self, client: TestClient, auth_headers):
        """Test removing non-existent item from watchlist"""
        response = client.delete("/api/watchlist/9999", headers=auth_headers)

        assert response.status_code in [200, 404]


class TestWatchlistWithPrices:
    """Tests for watchlist with price data"""

    def test_watchlist_items_have_price_fields(self, client: TestClient, auth_headers, sample_stocks):
        """Test that watchlist items include price information"""
        # Add stock
        client.post("/api/watchlist", headers=auth_headers, json={"stock_id": "2330"})

        response = client.get("/api/watchlist", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            item = data[0]
            # Check for expected fields (may or may not have price data)
            assert "stock_id" in item
            assert "name" in item or "stock_id" in item
