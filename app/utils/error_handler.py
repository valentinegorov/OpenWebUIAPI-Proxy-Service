"""Shared proxy error handling utilities."""

import logging
from typing import Any, Tuple

from flask import jsonify
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)


def handle_proxy_error(
    e: RequestException, endpoint_name: str = "backend"
) -> Tuple[Any, int]:
    """Standardised error handling for proxied requests.

    Args:
        e: The caught exception.
        endpoint_name: Human-readable endpoint name for logs and responses.

    Returns:
        Tuple of (Flask response, HTTP status code).
    """
    if isinstance(e, Timeout):
        logger.warning("Timeout calling %s", endpoint_name)
        return jsonify({"error": "Request timed out"}), 504

    status_code = 502
    if e.response is not None:
        try:
            status_code = e.response.status_code
        except Exception:
            pass

    logger.error("Request failed | endpoint=%s | error=%s", endpoint_name, e)
    return jsonify({"error": f"{endpoint_name} request failed"}), status_code
