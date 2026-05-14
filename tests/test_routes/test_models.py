"""Tests for the models endpoint."""

import pytest
from flask import Flask
from requests.exceptions import RequestException, Timeout


class TestModelsEndpoint:
    """Test cases for GET /v1/models endpoint."""

    @pytest.fixture(autouse=True)
    def mock_client(self, mock_openwebui_client):
        """Inject the app-level mock client for test access."""
        self.mock_client_instance = mock_openwebui_client
        yield

    def test_models_endpoint_success(self, client: Flask.test_client_class) -> None:
        """Test successful models fetch returns 200."""
        self.mock_client_instance.get_models.return_value = {
            "data": [{"id": "gpt-4", "object": "model"}]
        }
        response = client.get("/v1/models")
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data

    def test_models_endpoint_timeout(self, client: Flask.test_client_class) -> None:
        """Test that backend timeout returns 504."""
        self.mock_client_instance.get_models.side_effect = Timeout("Timed out")
        response = client.get("/v1/models")
        assert response.status_code == 504
        data = response.get_json()
        assert "error" in data

    def test_models_endpoint_backend_error(self, client: Flask.test_client_class) -> None:
        """Test that backend RequestException returns 502."""
        self.mock_client_instance.get_models.side_effect = RequestException("Backend error")
        response = client.get("/v1/models")
        assert response.status_code == 502
        data = response.get_json()
        assert "error" in data

    def test_models_endpoint_unexpected_error(self, client: Flask.test_client_class) -> None:
        """Test that unexpected exceptions propagate (not silently swallowed).

        In Flask's TESTING mode, the test client re-raises the exception rather
        than catching and returning a 500 response. This verifies that the
        exception is NOT silently swallowed by a bare except block.
        """
        # pylint: disable=undefined-variable
        self.mock_client_instance.get_models.side_effect = NameError("Undefined variable")
        with pytest.raises(NameError, match="Undefined variable"):
            client.get("/v1/models")

    def test_models_endpoint_method_not_allowed(
        self, client: Flask.test_client_class
    ) -> None:
        """Test that POST method is not allowed on models endpoint."""
        response = client.post("/v1/models")
        assert response.status_code == 405
