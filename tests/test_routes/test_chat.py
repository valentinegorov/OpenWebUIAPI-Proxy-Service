"""Tests for the chat completions endpoint."""

import pytest
from flask import Flask


class TestChatCompletionsEndpoint:
    """Test cases for POST /v1/chat/completions endpoint."""

    def test_chat_completions_endpoint_exists(
        self, client: Flask.test_client_class
    ) -> None:
        """Test that the chat completions endpoint exists."""
        payload = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        response = client.post("/v1/chat/completions", json=payload)
        
        # Should return either 200 (success) or 502/504 (backend unavailable)
        assert response.status_code in [200, 502, 504]

    def test_chat_completions_missing_fields(
        self, client: Flask.test_client_class
    ) -> None:
        """Test that missing required fields returns 400 error."""
        # Missing model
        payload = {"messages": [{"role": "user", "content": "Hello"}]}
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 400

        # Missing messages
        payload = {"model": "test-model"}
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 400

    def test_chat_completions_method_not_allowed(
        self, client: Flask.test_client_class
    ) -> None:
        """Test that GET method is not allowed on chat completions endpoint."""
        response = client.get("/v1/chat/completions")
        assert response.status_code == 405
