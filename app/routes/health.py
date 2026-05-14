"""Health and readiness check endpoint route handler."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from flask import Blueprint, current_app, jsonify
from requests.exceptions import RequestException, Timeout

from app.extensions import limiter

health_bp = Blueprint("health", __name__)
logger = logging.getLogger(__name__)


@health_bp.route("/health", methods=["GET"])
@limiter.exempt
def health_check() -> Tuple[Dict[str, Any], int]:
    """
    Health check endpoint for monitoring and load balancer probes.

    Returns the current status of the proxy server itself.

    Returns:
        JSON response with health status.
    """
    logger.info("Health check requested")
    return jsonify(
        {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
    ), 200


@health_bp.route("/ready", methods=["GET"])
@limiter.exempt
def readiness_check() -> Tuple[Dict[str, Any], int]:
    """
    Readiness check to verify backend connectivity.

    Verifies that the OpenWebUI backend is reachable before marking as ready.

    Returns:
        JSON response with readiness status.
    """
    logger.info("Readiness check requested")

    try:
        client = current_app.openwebui_client

        if client.check_readiness():
            logger.info("Backend OpenWebUI is reachable")
            return jsonify(
                {
                    "status": "ready",
                    "backend": "connected",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ), 200

        logger.warning("Backend returned non-200 status")
        return jsonify(
            {
                "status": "not_ready",
                "backend": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ), 503

    except Timeout:
        logger.error("Backend unreachable | reason=timeout")
        return jsonify(
            {
                "status": "not_ready",
                "backend": "unreachable",
                "error": "Request timed out",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ), 503
    except RequestException as e:
        logger.error("Backend unreachable | error=%s", e)
        return jsonify(
            {
                "status": "not_ready",
                "backend": "unreachable",
                "error": "Backend request failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ), 503
