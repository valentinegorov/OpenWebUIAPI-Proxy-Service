"""Tests for the OpenWebUI client service."""

import pytest
from unittest.mock import Mock, patch
import requests

from app.services.openwebui_client import OpenWebUIClient


class TestOpenWebUIClient:
    """Test cases for OpenWebUIClient service."""

    @pytest.fixture
    def client(self) -> OpenWebUIClient:
        """Create OpenWebUIClient instance for testing."""
        return OpenWebUIClient(
            base_url="http://test-openwebui:3000",
            verify_ssl=False,
            request_timeout=5,
            chat_completion_timeout=10,
            readiness_timeout=2,
        )

    @patch("app.services.openwebui_client.requests.get")
    def test_get_models_success(
        self, mock_get: Mock, client: OpenWebUIClient
    ) -> None:
        """Test successful models fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"id": "test-model"}]}
        mock_response.elapsed.total_seconds.return_value = 0.123
        mock_get.return_value = mock_response

        result = client.get_models(auth_header="Bearer test-token")

        assert result == {"models": [{"id": "test-model"}]}
        mock_get.assert_called_once()

    @patch("app.services.openwebui_client.requests.post")
    def test_chat_completions_success(
        self, mock_post: Mock, client: OpenWebUIClient
    ) -> None:
        """Test successful chat completion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}]
        }
        mock_response.elapsed.total_seconds.return_value = 0.456
        mock_post.return_value = mock_response

        result = client.chat_completions(
            model="test-model",
            messages=[{"role": "user", "content": "Hi"}],
            auth_header="Bearer test-token",
        )

        assert "choices" in result
        mock_post.assert_called_once()

    @patch("app.services.openwebui_client.requests.get")
    def test_check_readiness_success(
        self, mock_get: Mock, client: OpenWebUIClient
    ) -> None:
        """Test successful readiness check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = client.check_readiness()

        assert result is True

    @patch("app.services.openwebui_client.requests.get")
    def test_check_readiness_failure(
        self, mock_get: Mock, client: OpenWebUIClient
    ) -> None:
        """Test failed readiness check due to connection error."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        result = client.check_readiness()

        assert result is False

    @patch("app.services.openwebui_client.requests.get")
    def test_check_readiness_timeout(
        self, mock_get: Mock, client: OpenWebUIClient
    ) -> None:
        """Test failed readiness check due to timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        result = client.check_readiness()

        assert result is False
