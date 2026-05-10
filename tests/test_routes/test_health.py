"""Tests for the health and readiness endpoints."""

import pytest
from flask import Flask


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

    def test_readiness_check(self, client: Flask.test_client_class) -> None:
        """Test that readiness check returns valid response structure."""
        response = client.get("/ready")
        
        # Should return either 200 (ready) or 503 (not ready)
        assert response.status_code in [200, 503]
        data = response.get_json()
        assert "status" in data
        assert "timestamp" in data

    def test_readiness_method_not_allowed(
        self, client: Flask.test_client_class
    ) -> None:
        """Test that POST method is not allowed on readiness endpoint."""
        response = client.post("/ready")
        assert response.status_code == 405
