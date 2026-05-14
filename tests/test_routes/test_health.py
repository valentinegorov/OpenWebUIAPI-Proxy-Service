"""Tests for the health and readiness endpoints."""

import pytest
from flask import Flask
from requests.exceptions import RequestException, Timeout


class TestHealthEndpoint:
    """Test cases for GET /health endpoint."""

    def test_health_check(self, client: Flask.test_client_class) -> None:
        """Test that health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_method_not_allowed(
        self, client: Flask.test_client_class
    ) -> None:
        """Test that POST method is not allowed on health endpoint."""
        response = client.post("/health")
        assert response.status_code == 405


class TestReadinessEndpoint:
    """Test cases for GET /ready endpoint."""

    @pytest.fixture(autouse=True)
    def mock_client(self, mock_openwebui_client):
        """Inject the app-level mock client for test access."""
        self.mock_client_instance = mock_openwebui_client
        yield

    def test_readiness_success(self, client: Flask.test_client_class) -> None:
        """Test that readiness returns 200 when backend is reachable."""
        self.mock_client_instance.check_readiness.return_value = True
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ready"
        assert data["backend"] == "connected"

    def test_readiness_backend_unhealthy(self, client: Flask.test_client_class) -> None:
        """Test that readiness returns 503 when backend returns non-200."""
        self.mock_client_instance.check_readiness.return_value = False
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "not_ready"

    def test_readiness_backend_timeout(self, client: Flask.test_client_class) -> None:
        """Test that readiness returns 503 when backend times out."""
        self.mock_client_instance.check_readiness.side_effect = Timeout("Timed out")
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "not_ready"
        assert data["backend"] == "unreachable"

    def test_readiness_backend_error(self, client: Flask.test_client_class) -> None:
        """Test that readiness returns 503 on backend error."""
        self.mock_client_instance.check_readiness.side_effect = RequestException("Error")
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "not_ready"

    def test_readiness_method_not_allowed(
        self, client: Flask.test_client_class
    ) -> None:
        """Test that POST method is not allowed on readiness endpoint."""
        response = client.post("/ready")
        assert response.status_code == 405
