"""Tests for the OpenWebUI client service."""

from unittest.mock import Mock, patch

import pytest
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

    def test_get_models_success(self, client: OpenWebUIClient) -> None:
        """Test successful models fetch with session reuse."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"id": "test-model"}]}
        mock_response.elapsed.total_seconds.return_value = 0.123

        with patch.object(client.session, "get", return_value=mock_response) as mock_get:
            result = client.get_models(auth_header="Bearer test-token")

            assert result == {"models": [{"id": "test-model"}]}
            mock_get.assert_called_once()

    def test_chat_completions_success(self, client: OpenWebUIClient) -> None:
        """Test successful chat completion with session reuse."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}]
        }
        mock_response.elapsed.total_seconds.return_value = 0.456

        with patch.object(client.session, "post", return_value=mock_response) as mock_post:
            result = client.chat_completions(
                model="test-model",
                messages=[{"role": "user", "content": "Hi"}],
                auth_header="Bearer test-token",
            )

            assert "choices" in result
            mock_post.assert_called_once()

    def test_auth_header_omitted_when_none(self, client: OpenWebUIClient) -> None:
        """Test that Authorization header is omitted when auth_header is None."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_response.elapsed.total_seconds.return_value = 0.1

        with patch.object(client.session, "get", return_value=mock_response) as mock_get:
            client.get_models(auth_header=None)

            call_kwargs = mock_get.call_args.kwargs
            assert "Authorization" not in call_kwargs.get("headers", {})

    def test_chat_auth_header_omitted_when_none(self, client: OpenWebUIClient) -> None:
        """Test that Authorization header is omitted for chat when None."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_response.elapsed.total_seconds.return_value = 0.1

        with patch.object(client.session, "post", return_value=mock_response) as mock_post:
            client.chat_completions(
                model="test",
                messages=[{"role": "user", "content": "Hi"}],
                auth_header=None,
            )

            call_kwargs = mock_post.call_args.kwargs
            assert "Authorization" not in call_kwargs.get("headers", {})

    def test_check_readiness_success(self, client: OpenWebUIClient) -> None:
        """Test successful readiness check via session."""
        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(client.session, "get", return_value=mock_response):
            result = client.check_readiness()
            assert result is True

    def test_check_readiness_failure(self, client: OpenWebUIClient) -> None:
        """Test failed readiness check due to connection error."""
        exc = requests.exceptions.RequestException("Connection failed")
        with patch.object(client.session, "get", side_effect=exc):
            result = client.check_readiness()
            assert result is False

    def test_check_readiness_timeout(self, client: OpenWebUIClient) -> None:
        """Test failed readiness check due to timeout."""
        exc = requests.exceptions.Timeout("Request timed out")
        with patch.object(client.session, "get", side_effect=exc):
            result = client.check_readiness()
            assert result is False

    def test_session_close(self, client: OpenWebUIClient) -> None:
        """Test that close() properly closes the session."""
        with patch.object(client.session, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()

    def test_consecutive_calls_reuse_session(self, client: OpenWebUIClient) -> None:
        """Test that multiple calls reuse the same session object."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_response.elapsed.total_seconds.return_value = 0.1

        with patch.object(client.session, "get", return_value=mock_response) as mock_get:
            client.get_models()
            client.get_models()

            # Both calls should use the same session
            assert mock_get.call_count == 2

    def test_get_models_raises_on_http_error(self, client: OpenWebUIClient) -> None:
        """Test that get_models propagates HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        http_err = requests.exceptions.HTTPError("500 Server Error")
        mock_response.raise_for_status.side_effect = http_err
        mock_response.elapsed.total_seconds.return_value = 0.1

        with patch.object(client.session, "get", return_value=mock_response):
            with pytest.raises(requests.exceptions.HTTPError):
                client.get_models()
