"""Chat completions endpoint route handler."""

import logging
import re
from typing import Any, Dict, Tuple

from flask import Blueprint, current_app, jsonify, request
from requests.exceptions import RequestException

from app.extensions import limiter
from app.utils.error_handler import handle_proxy_error

chat_bp = Blueprint("chat", __name__)
logger = logging.getLogger(__name__)


@chat_bp.route("/v1/chat/completions", methods=["POST"])
@limiter.limit(lambda: current_app.config.get("RATE_LIMIT_CHAT", "30 per minute"))
def chat_completions() -> Tuple[Dict[str, Any], int]:
    """
    Handle POST /v1/chat/completions requests.

    Proxies the request to OpenWebUI's /api/chat/completions endpoint.

    Returns:
        JSON response with chat completion or error message.
    """
    auth_header = request.headers.get("Authorization")
    client_ip = request.remote_addr

    logger.info(
        "Request received | endpoint=/v1/chat/completions | method=POST | client_ip=%s",
        client_ip,
    )

    data = request.get_json()

    # Log request payload summary (avoid logging full messages for privacy)
    model_name = data.get("model", "unknown") if data else "unknown"
    message_count = len(data.get("messages", [])) if data else 0
    logger.info(
        "Request payload | model=%s | message_count=%s",
        model_name,
        message_count,
    )

    if not data or not data.get("model") or not data.get("messages"):
        logger.warning("Invalid request payload")
        return jsonify({"error": "Missing required fields: model, messages"}), 400

    # Validate model name to prevent injection or malformed requests
    model = data["model"]
    if not re.match(r'^[a-zA-Z0-9_\-.:/@+]+$', model):
        logger.warning("Invalid model name | model=%s", model)
        return jsonify({"error": "Invalid model name"}), 400

    try:
        client = current_app.openwebui_client

        response_data = client.chat_completions(
            model=model,
            messages=data["messages"],
            auth_header=auth_header,
        )
        logger.info("Successfully retrieved chat completion")
        return jsonify(response_data), 200

    except RequestException as e:
        return handle_proxy_error(e, endpoint_name="OpenWebUI chat")
