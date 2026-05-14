"""Logging configuration for the OpenWebUI Proxy Server."""

import logging
import sys
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler


# Context variable to store request ID across the request lifecycle
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get the current request ID."""
    return _request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current request context."""
    _request_id_var.set(request_id)


def generate_request_id() -> str:
    """Generate a new unique request ID."""
    return str(uuid.uuid4())[:8]


class RequestIDFilter(logging.Filter):
    """Logging filter that adds request ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id attribute to log record."""
        record.request_id = get_request_id()
        return True


def setup_logging(
    log_file: str = "logs/proxy_server.log",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Set up structured logging with both file and console handlers.

    Args:
        log_file: Path to the log file.
        max_bytes: Maximum size of log file before rotation.
        backup_count: Number of backup log files to keep.
        level: Logging level (default: INFO).

    Returns:
        Configured logger instance.
    """
    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | [%(request_id)s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setFormatter(log_format)
        file_handler.setLevel(level)
        file_handler.addFilter(RequestIDFilter())
    except (PermissionError, OSError) as e:
        # Fallback to console-only logging if file logging fails
        print(f"Warning: Could not create log file {log_file}: {e}")
        file_handler = None

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(level)
    console_handler.addFilter(RequestIDFilter())

    # Configure app logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    # (e.g., during tests with repeated create_app calls)
    if app_logger.handlers:
        app_logger.handlers.clear()

    if file_handler:
        app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)

    return app_logger
