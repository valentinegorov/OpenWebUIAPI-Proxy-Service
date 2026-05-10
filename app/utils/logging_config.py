"""Logging configuration for the OpenWebUI Proxy Server."""

import logging
import sys
from logging.handlers import RotatingFileHandler



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
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
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
    except (PermissionError, OSError) as e:
        # Fallback to console-only logging if file logging fails
        print(f"Warning: Could not create log file {log_file}: {e}")
        file_handler = None

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(level)

    # Configure app logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)

    if file_handler:
        app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)

    return app_logger
