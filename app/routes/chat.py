"""Chat completions endpoint route handler."""

import logging
from typing import Any, Dict, Tuple

from flask import Blueprint, jsonify, request

from app.services.openwebui_client import OpenWebUIClient

chat_bp = Blueprint("chat", __name__)
logger = logging.getLogger(__name__)


@chat_bp.route("/v1/chat/completions", methods=["POST"])
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
        f"Request received | endpoint=/v1/chat/completions | method=POST | client_ip={client_ip}"
    )

    data = request.get_json()

    # Log request payload summary (avoid logging full messages for privacy)
    model_name = data.get("model", "unknown") if data else "unknown"
    message_count = len(data.get("messages", [])) if data else 0
    logger.info(f"Request payload | model={model_name} | message_count={message_count}")

    if not data or not data.get("model") or not data.get("messages"):
        logger.warning("Invalid request payload")
        return jsonify({"error": "Missing required fields: model, messages"}), 400

    try:
        # Get the OpenWebUI client from app config
        client = OpenWebUIClient(
            base_url=request.app.config["OPENWEBUI_BASE_URL"],
            verify_ssl=request.app.config["OPENWEBUI_VERIFY_SSL"],
            chat_completion_timeout=request.app.config["CHAT_COMPLETION_TIMEOUT"],
        )

        response_data = client.chat_completions(
            model=data["model"],
            messages=data["messages"],
            auth_header=auth_header,
        )
        logger.info("Successfully retrieved chat completion")
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Request failed | error={str(e)}")
        error_response = {"error": str(e)}
        status_code = 502

        if "timeout" in str(e).lower():
            logger.error("Request timed out | endpoint=/api/chat/completions")
            error_response = {"error": "Request timed out"}
            status_code = 504
        elif hasattr(e, "response") and e.response is not None:
            status_code = e.response.status_code
            error_response = {"error": "Failed to get chat completion"}

        return jsonify(error_response), status_code
