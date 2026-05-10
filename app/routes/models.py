"""Models endpoint route handler."""

import logging
from typing import Any, Dict, Tuple

from flask import Blueprint, current_app, jsonify, request
from requests.exceptions import RequestException

from app.extensions import limiter
from app.services.openwebui_client import OpenWebUIClient
from app.utils.error_handler import handle_proxy_error

models_bp = Blueprint("models", __name__)
logger = logging.getLogger(__name__)


@models_bp.route("/v1/models", methods=["GET"])
@limiter.limit(lambda: current_app.config.get("RATE_LIMIT_MODELS", "30 per minute"))
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
        "Request received | endpoint=/v1/models | method=GET | client_ip=%s",
        client_ip,
    )

    try:
        # Get the OpenWebUI client from app config
        client = OpenWebUIClient(
            base_url=current_app.config["OPENWEBUI_BASE_URL"],
            verify_ssl=current_app.config["OPENWEBUI_VERIFY_SSL"],
            request_timeout=current_app.config["REQUEST_TIMEOUT"],
        )

        response_data = client.get_models(auth_header)
        logger.info("Successfully retrieved models")
        return jsonify(response_data), 200

    except RequestException as e:
        return handle_proxy_error(e, endpoint_name="OpenWebUI models")
