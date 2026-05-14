"""Test that the app-level OpenWebUIClient singleton is reused across requests."""

from flask import Flask


class TestSessionReuse:
    """Verify that the same OpenWebUIClient instance is used across all route calls."""

    def test_same_client_across_models_requests(
        self, client: Flask.test_client_class, app: Flask
    ) -> None:
        """The same app.openwebui_client object serves multiple /v1/models calls."""
        client_instance = app.openwebui_client
        assert client_instance is not None

        client_instance.get_models.return_value = {
            "data": [{"id": "gpt-4", "object": "model"}]
        }

        # First request
        response1 = client.get("/v1/models")
        assert response1.status_code == 200
        client_instance.get_models.assert_called_once()

        # Second request — must use the same object
        client_instance.get_models.reset_mock()
        response2 = client.get("/v1/models")
        assert response2.status_code == 200
        client_instance.get_models.assert_called_once()

        # Verify the object on the app hasn't been replaced
        assert app.openwebui_client is client_instance

    def test_same_client_across_different_endpoints(
        self, client: Flask.test_client_class, app: Flask
    ) -> None:
        """The same app.openwebui_client serves different endpoints."""
        client_instance = app.openwebui_client

        # Models endpoint
        client_instance.get_models.return_value = {
            "data": [{"id": "gpt-4"}]
        }
        response = client.get("/v1/models")
        assert response.status_code == 200

        # Chat endpoint
        client_instance.chat_completions.return_value = {
            "choices": [{"message": {"content": "Hello!"}}]
        }
        payload = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200

        # Readiness endpoint
        client_instance.check_readiness.return_value = True
        response = client.get("/ready")
        assert response.status_code == 200

        # All three endpoints used the same client instance
        assert app.openwebui_client is client_instance
