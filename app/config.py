"""Configuration management for the OpenWebUI Proxy Server."""

import os


class Config:
    """Application configuration loaded from environment variables."""

    # OpenWebUI backend configuration
    OPENWEBUI_BASE_URL = os.environ.get(
        "OPENWEBUI_BASE_URL", "http://localhost:3000"
    )
    OPENWEBUI_VERIFY_SSL = os.environ.get(
        "OPENWEBUI_VERIFY_SSL", "true"
    ).lower() not in ("false", "0", "no")

    # Flask configuration
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.environ.get("FLASK_PORT", "5001"))

    # Logging configuration
    LOG_MAX_BYTES = int(os.environ.get("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
    LOG_BACKUP_COUNT = int(os.environ.get("LOG_BACKUP_COUNT", "5"))
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Request timeout configuration
    REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))
    CHAT_COMPLETION_TIMEOUT = int(os.environ.get("CHAT_COMPLETION_TIMEOUT", "120"))
    READINESS_TIMEOUT = int(os.environ.get("READINESS_TIMEOUT", "5"))

    # Rate limiting configuration
    RATE_LIMIT_GLOBAL = os.environ.get("RATE_LIMIT_GLOBAL", "100 per minute")
    RATE_LIMIT_MODELS = os.environ.get("RATE_LIMIT_MODELS", "30 per minute")
    RATE_LIMIT_CHAT = os.environ.get("RATE_LIMIT_CHAT", "30 per minute")
    RATE_LIMIT_STORAGE_URL = os.environ.get(
        "RATE_LIMIT_STORAGE_URL", "memory://"
    )

    # CORS configuration
    CORS_ENABLED = os.environ.get("CORS_ENABLED", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
    CORS_ALLOW_METHODS = os.environ.get(
        "CORS_ALLOW_METHODS", "GET, POST, PUT, DELETE, OPTIONS"
    )
    CORS_ALLOW_HEADERS = os.environ.get(
        "CORS_ALLOW_HEADERS", "Content-Type, Authorization"
    )
    CORS_ALLOW_CREDENTIALS = os.environ.get(
        "CORS_ALLOW_CREDENTIALS", "true"
    ).lower() in ("true", "1", "yes")
    CORS_MAX_AGE = int(os.environ.get("CORS_MAX_AGE", "3600"))
