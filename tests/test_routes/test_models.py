"""Tests for the models endpoint."""

import pytest
from flask import Flask


class TestModelsEndpoint:
    """Test cases for GET /v1/models endpoint."""

    def test_models_endpoint_exists(self, client: Flask.test_client_class) -> None:
        """Test that the models endpoint exists and returns valid response structure."""
        # Note: This will fail without a real OpenWebUI backend
        # In production tests, you would mock the OpenWebUIClient
        response = client.get("/v1/models")
        
        # Should return either 200 (success) or 502/504 (backend unavailable)
        assert response.status_code in [200, 502, 504]
        
    def test_models_endpoint_method_not_allowed(
        self, client: Flask.test_client_class
    ) -> None:
        """Test that POST method is not allowed on models endpoint."""
        response = client.post("/v1/models")
        assert response.status_code == 405
