"""
健康檢查 endpoint 測試（不需 auth）
"""
import pytest


class TestHealthEndpoints:
    """基礎健康檢查測試"""

    def test_root_returns_200_with_version(self, client):
        """GET / → 200 + version info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "message" in data

    def test_health_check(self, client):
        """GET /health → {"status": "healthy"}"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_docs_returns_200(self, client):
        """GET /docs → 200"""
        response = client.get("/docs")
        assert response.status_code == 200
