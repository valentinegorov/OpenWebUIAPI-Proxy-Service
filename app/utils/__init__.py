"""Utility modules for the OpenWebUI Proxy Server."""

from app.utils.error_handler import handle_proxy_error
from app.utils.logging_config import setup_logging

__all__ = ["handle_proxy_error", "setup_logging"]
