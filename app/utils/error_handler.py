"""Shared proxy error handling utilities."""

import logging
from typing import Any, Tuple

from flask import current_app, jsonify
from requests.exceptions import RequestException, Timeout, ConnectionError as RequestsConnectionError, SSLError

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
    # Get request ID for consistent error tracking
    from flask import g
    request_id = getattr(g, "request_id", "unknown")
    
    if isinstance(e, SSLError):
        logger.error(
            "SSL verification failed | endpoint=%s | request_id=%s",
            endpoint_name,
            request_id,
        )
        return jsonify({
            "error": "SSL verification failed",
            "request_id": request_id,
        }), 502
    
    if isinstance(e, RequestsConnectionError):
        logger.warning(
            "Backend unreachable | endpoint=%s | request_id=%s",
            endpoint_name,
            request_id,
        )
        return jsonify({
            "error": "Backend unreachable",
            "request_id": request_id,
        }), 503
    
    if isinstance(e, Timeout):
        logger.warning(
            "Timeout calling %s | request_id=%s",
            endpoint_name,
            request_id,
        )
        return jsonify({
            "error": "Request timed out",
            "request_id": request_id,
        }), 504

    status_code = 502
    if e.response is not None:
        status_code = getattr(e.response, "status_code", 502)

    logger.error(
        "Request failed | endpoint=%s | request_id=%s | error=%s",
        endpoint_name,
        request_id,
        e,
    )
    return jsonify({
        "error": f"{endpoint_name} request failed",
        "request_id": request_id,
    }), status_code
