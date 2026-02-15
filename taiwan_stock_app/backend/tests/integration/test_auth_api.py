"""
Integration tests for authentication API
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthRegister:
    """Tests for user registration"""

    def test_register_new_user(self, client: TestClient):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with existing email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",  # Same as test_user
                "password": "anotherpassword123",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_any_string_as_email(self, client: TestClient):
        """Schema 允許任意字串作為帳號，不限 email 格式"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepassword123",
            },
        )
        # 目前 schema 不驗證 email 格式，應正常註冊
        assert response.status_code == 200

    def test_register_missing_fields(self, client: TestClient):
        """缺少必填欄位 → 422"""
        response = client.post(
            "/api/auth/register",
            json={"email": "valid@example.com"},
        )
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for user login"""

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )

        assert response.status_code == 401


class TestAuthProtectedRoutes:
    """Tests for authentication on protected routes"""

    def test_access_protected_route_without_token(self, client: TestClient):
        """Test accessing protected route without token"""
        response = client.get("/api/stocks/search?q=2330")

        assert response.status_code in (401, 403)

    def test_access_protected_route_with_invalid_token(self, client: TestClient):
        """Test accessing protected route with invalid token"""
        response = client.get(
            "/api/stocks/search?q=2330",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    def test_access_protected_route_with_valid_token(
        self, client: TestClient, auth_headers, sample_stocks
    ):
        """Test accessing protected route with valid token"""
        response = client.get(
            "/api/stocks/search?q=2330",
            headers=auth_headers,
        )

        assert response.status_code == 200
