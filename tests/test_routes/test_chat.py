"""Tests for the chat completions endpoint."""

import pytest
from flask import Flask
from requests.exceptions import RequestException, Timeout


class TestChatCompletionsEndpoint:
    """Test cases for POST /v1/chat/completions endpoint."""

    @pytest.fixture(autouse=True)
    def mock_client(self, mock_openwebui_client):
        """Inject the app-level mock client for test access."""
        self.mock_client_instance = mock_openwebui_client
        yield

    def _set_response(self, body=None):
        """Configure the mock client to return a specific chat response."""
        if body is None:
            body = {"choices": [{"message": {"content": "Hello!"}}]}
        self.mock_client_instance.chat_completions.return_value = body

    def test_chat_completions_success(self, client: Flask.test_client_class) -> None:
        """Test successful chat completion returns 200."""
        self._set_response()
        payload = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert "choices" in data

    def test_chat_completions_missing_fields(self, client: Flask.test_client_class) -> None:
        """Test that missing required fields returns 400."""
        # Missing model
        payload = {"messages": [{"role": "user", "content": "Hello"}]}
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 400

        # Missing messages
        payload = {"model": "test-model"}
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 400

    def test_chat_completions_backend_timeout(self, client: Flask.test_client_class) -> None:
        """Test that backend timeout returns 504."""
        self.mock_client_instance.chat_completions.side_effect = Timeout("Timed out")
        payload = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 504
        data = response.get_json()
        assert "error" in data

    def test_chat_completions_backend_error(self, client: Flask.test_client_class) -> None:
        """Test that backend RequestException returns 502."""
        self.mock_client_instance.chat_completions.side_effect = RequestException("Backend error")
        payload = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 502
        data = response.get_json()
        assert "error" in data

    def test_chat_completions_unexpected_error_500(self, client: Flask.test_client_class) -> None:
        """Test that unexpected exceptions (not RequestException) propagate as 500s.

        In Flask's TESTING mode, the test client re-raises the exception rather
        than catching and returning a 500 response. This verifies that the
        exception is NOT silently swallowed by a bare except block.
        """
        # pylint: disable=undefined-variable
        self.mock_client_instance.chat_completions.side_effect = NameError("Undefined variable")
        payload = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        with pytest.raises(NameError, match="Undefined variable"):
            client.post("/v1/chat/completions", json=payload)

    def test_chat_completions_method_not_allowed(
        self, client: Flask.test_client_class
    ) -> None:
        """Test that GET method is not allowed on chat completions endpoint."""
        response = client.get("/v1/chat/completions")
        assert response.status_code == 405

    def test_chat_completions_invalid_model_name(self, client: Flask.test_client_class) -> None:
        """Test that invalid model names return 400."""
        payload = {
            "model": "evil<script>alert(1)</script>",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid model name" in data["error"]

    def test_chat_completions_special_chars_model(self, client: Flask.test_client_class) -> None:
        """Test that model names with allowed special chars (/ : . @ +) are accepted."""
        self._set_response()
        payload = {
            "model": "openai/gpt-4:latest@v1.0+special",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200
