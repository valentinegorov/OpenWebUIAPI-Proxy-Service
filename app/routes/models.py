"""Models endpoint route handler."""

import logging
from datetime import datetime
from typing import Any, Dict, Tuple

from flask import Blueprint, jsonify, request

from app.services.openwebui_client import OpenWebUIClient

models_bp = Blueprint("models", __name__)
logger = logging.getLogger(__name__)


@models_bp.route("/v1/models", methods=["GET"])
def get_models() -> Tuple[Dict[str, Any], int]:
    """
    Handle GET /v1/models requests.

    Proxies the request to OpenWebUI's /api/models endpoint.

    Returns:
        JSON response with models list or error message.
    """
    auth_header = request.headers.get("Authorization")
    client_ip = request.remote_addr

    logger.info(
        f"Request received | endpoint=/v1/models | method=GET | client_ip={client_ip}"
    )

    try:
        # Get the OpenWebUI client from app config
        client = OpenWebUIClient(
            base_url=request.app.config["OPENWEBUI_BASE_URL"],
            verify_ssl=request.app.config["OPENWEBUI_VERIFY_SSL"],
            request_timeout=request.app.config["REQUEST_TIMEOUT"],
        )

        response_data = client.get_models(auth_header)
        logger.info("Successfully retrieved models")
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Request failed | error={str(e)}")
        error_response = {"error": str(e)}
        status_code = 502

        if "timeout" in str(e).lower():
            logger.error("Request timed out | endpoint=/api/models")
            error_response = {"error": "Request timed out"}
            status_code = 504
        elif hasattr(e, "response") and e.response is not None:
            status_code = e.response.status_code
            error_response = {"error": "Failed to retrieve models"}

        return jsonify(error_response), status_code
