"""Request ID middleware for tracking requests across logs."""

import logging
from typing import Any

from flask import Flask, g, request

from app.utils.logging_config import generate_request_id, set_request_id


logger = logging.getLogger(__name__)


def init_request_id_middleware(app: Flask) -> None:
    """
    Initialize request ID middleware for the Flask application.
    
    This middleware generates a unique request ID at the start of each request
    and makes it available throughout the request lifecycle for logging purposes.
    
    Args:
        app: Flask application instance.
    """
    
    @app.before_request
    def before_request_setup() -> None:
        """Generate and store request ID before processing the request."""
        # Check if request already has an ID (e.g., from X-Request-ID header)
        request_id = request.headers.get("X-Request-ID") or generate_request_id()
        
        # Store in Flask's g object for access in views
        g.request_id = request_id
        
        # Set in context var for logging
        set_request_id(request_id)
        
        logger.info(
            "Request started | id=%s | method=%s | path=%s",
            request_id,
            request.method,
            request.path,
        )
    
    @app.after_request
    def after_request_teardown(response: Any) -> Any:
        """Log request completion with status code."""
        request_id = getattr(g, "request_id", "unknown")
        
        logger.info(
            "Request completed | id=%s | status=%s",
            request_id,
            response.status_code,
        )
        
        # Add request ID to response headers for client-side tracking
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    @app.teardown_request
    def teardown_request_cleanup(exception: Exception | None = None) -> None:
        """Clean up request context after request completes."""
        request_id = getattr(g, "request_id", "unknown")
        
        if exception:
            logger.error(
                "Request failed with exception | id=%s | error=%s",
                request_id,
                str(exception),
            )
