"""OpenWebUI API client service."""

import logging
from typing import Any, Dict, Optional

import requests


class OpenWebUIClient:
    """Client for interacting with the OpenWebUI API."""

    def __init__(
        self,
        base_url: str,
        verify_ssl: bool = True,
        request_timeout: int = 30,
        chat_completion_timeout: int = 120,
        readiness_timeout: int = 5,
    ):
        """
        Initialize the OpenWebUI client.

        Args:
            base_url: Base URL of the OpenWebUI instance.
            verify_ssl: Whether to verify SSL certificates.
            request_timeout: Default timeout for API requests.
            chat_completion_timeout: Timeout for chat completion requests.
            readiness_timeout: Timeout for readiness checks.
        """
        self.base_url = base_url.rstrip("/")
        self.verify_ssl = verify_ssl
        self.request_timeout = request_timeout
        self.chat_completion_timeout = chat_completion_timeout
        self.readiness_timeout = readiness_timeout
        self.logger = logging.getLogger(__name__)

    def get_models(self, auth_header: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch available models from OpenWebUI.

        Args:
            auth_header: Authorization header value.

        Returns:
            Response data containing models.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
        }

        self.logger.info("Fetching models from OpenWebUI")
        response = requests.get(
            f"{self.base_url}/api/models",
            headers=headers,
            timeout=self.request_timeout,
            verify=self.verify_ssl,
        )
        self.logger.info(
            f"Models response | status={response.status_code} | latency_ms={response.elapsed.total_seconds() * 1000:.2f}"
        )

        response.raise_for_status()
        return response.json()

    def chat_completions(
        self, model: str, messages: list, auth_header: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenWebUI.

        Args:
            model: Model name to use.
            messages: List of message dictionaries.
            auth_header: Authorization header value.

        Returns:
            Response data containing chat completion.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
        }

        payload = {"model": model, "messages": messages}

        self.logger.info(f"Sending chat completion | model={model} | message_count={len(messages)}")
        response = requests.post(
            f"{self.base_url}/api/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.chat_completion_timeout,
            verify=self.verify_ssl,
        )
        self.logger.info(
            f"Chat completion response | status={response.status_code} | latency_ms={response.elapsed.total_seconds() * 1000:.2f}"
        )

        response.raise_for_status()
        return response.json()

    def check_readiness(self) -> bool:
        """
        Check if the OpenWebUI backend is reachable.

        Returns:
            True if backend is reachable, False otherwise.
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/models",
                timeout=self.readiness_timeout,
                verify=self.verify_ssl,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Backend unreachable | error={str(e)}")
            return False
