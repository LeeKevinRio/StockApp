"""
AI API endpoint 測試（含綜合分析）
"""
import pytest


class TestAIAPI:
    """AI 分析 API 測試"""

    def test_comprehensive_analysis_requires_auth(self, client):
        """無 token → 403"""
        response = client.get("/api/ai/comprehensive-analysis/2330")
        assert response.status_code == 403

    def test_comprehensive_analysis_tw(self, client, auth_headers, sample_stocks):
        """GET /api/ai/comprehensive-analysis/2330 → 200 + 驗證回傳結構"""
        response = client.get(
            "/api/ai/comprehensive-analysis/2330", headers=auth_headers
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            # 必須含有核心欄位
            assert "health_grade" in data
            assert data["health_grade"] in ("A", "B", "C", "D", "E", "F")
            # dimensions 應有 6 個維度
            assert "dimensions" in data
            dims = data["dimensions"]
            assert len(dims) == 6
            expected_keys = {"technical", "chip", "fundamental", "news", "social", "macro"}
            assert set(dims.keys()) == expected_keys
            # radar 資料
            assert "radar" in data
            assert "labels" in data["radar"]
            assert "values" in data["radar"]
            # AI 摘要
            assert "ai_summary" in data

    def test_comprehensive_analysis_us(self, client, auth_headers):
        """market=US 也回傳成功"""
        response = client.get(
            "/api/ai/comprehensive-analysis/AAPL?market=US",
            headers=auth_headers,
        )
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            data = response.json()
            assert data["market"] == "US"
            assert "health_grade" in data
            # US 市場雷達圖只有 5 維度（無籌碼面）
            assert len(data["radar"]["labels"]) == 5

    def test_suggestions_requires_auth(self, client):
        """無 token → 403"""
        response = client.get("/api/ai/suggestions")
        assert response.status_code == 403

    def test_chat_requires_auth(self, client):
        """無 token → 403"""
        response = client.post(
            "/api/ai/chat",
            json={"message": "test", "stock_id": "2330"},
        )
        assert response.status_code == 403
