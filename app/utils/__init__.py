"""Utility modules for the OpenWebUI Proxy Server."""

from app.utils.error_handler import handle_proxy_error
from app.utils.logging_config import setup_logging
from app.utils.metrics import (
    setup_metrics,
    get_metrics_response,
    record_request_latency,
    increment_request_count,
    increment_error_count,
    shutdown_metrics,
)

__all__ = [
    "handle_proxy_error",
    "setup_logging",
    "setup_metrics",
    "get_metrics_response",
    "record_request_latency",
    "increment_request_count",
    "increment_error_count",
    "shutdown_metrics",
]
