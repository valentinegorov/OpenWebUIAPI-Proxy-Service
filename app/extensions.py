"""Shared Flask extensions for the OpenWebUI Proxy Server.

Extensions are instantiated here so they can be imported by both
the application factory and route blueprints without circular imports.
"""

from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _rate_limit_key() -> str:
    """Return the client IP for rate limiting, respecting X-Forwarded-For."""
    if request:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            # Take the first IP in the chain (original client)
            return forwarded.split(",")[0].strip()
    return get_remote_address()


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=[],  # default handled via create_app config
    storage_uri=None,  # defer to app.config["RATELIMIT_STORAGE_URI"]
)
