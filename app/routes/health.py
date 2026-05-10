"""Health and readiness check endpoint route handler."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from flask import Blueprint, jsonify, request

from app.services.openwebui_client import OpenWebUIClient

health_bp = Blueprint("health", __name__)
logger = logging.getLogger(__name__)


@health_bp.route("/health", methods=["GET"])
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
def readiness_check() -> Tuple[Dict[str, Any], int]:
    """
    Readiness check to verify backend connectivity.

    Verifies that the OpenWebUI backend is reachable before marking as ready.

    Returns:
        JSON response with readiness status.
    """
    logger.info("Readiness check requested")

    try:
        # Get the OpenWebUI client from app config
        client = OpenWebUIClient(
            base_url=request.app.config["OPENWEBUI_BASE_URL"],
            verify_ssl=request.app.config["OPENWEBUI_VERIFY_SSL"],
            readiness_timeout=request.app.config["READINESS_TIMEOUT"],
        )

        if client.check_readiness():
            logger.info("Backend OpenWebUI is reachable")
            return jsonify(
                {
                    "status": "ready",
                    "backend": "connected",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ), 200
        else:
            logger.warning("Backend returned non-200 status")
            return jsonify(
                {
                    "status": "not_ready",
                    "backend": "unhealthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ), 503

    except Exception as e:
        logger.error(f"Backend unreachable | error={str(e)}")
        return jsonify(
            {
                "status": "not_ready",
                "backend": "unreachable",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ), 503
