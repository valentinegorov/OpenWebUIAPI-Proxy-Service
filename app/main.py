"""Flask application factory and entry point."""

import atexit
import logging
from typing import Optional

from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import limiter
from app.routes import models_bp, chat_bp, health_bp
from app.services.openwebui_client import OpenWebUIClient
from app.utils.logging_config import setup_logging


def create_app(config: Optional[Config] = None) -> Flask:
    """
    Application factory for creating the Flask app.

    Args:
        config: Configuration object. If None, uses default Config.

    Returns:
        Configured Flask application instance.
    """
    if config is None:
        config = Config()

    # Set up logging first
    logger = setup_logging(
        log_file="logs/proxy_server.log",
        max_bytes=config.LOG_MAX_BYTES,
        backup_count=config.LOG_BACKUP_COUNT,
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    )

    # Create and configure Flask app
    app = Flask(__name__)

    # Load configuration into app config
    app.config["OPENWEBUI_BASE_URL"] = config.OPENWEBUI_BASE_URL
    app.config["OPENWEBUI_VERIFY_SSL"] = config.OPENWEBUI_VERIFY_SSL
    app.config["REQUEST_TIMEOUT"] = config.REQUEST_TIMEOUT
    app.config["CHAT_COMPLETION_TIMEOUT"] = config.CHAT_COMPLETION_TIMEOUT
    app.config["READINESS_TIMEOUT"] = config.READINESS_TIMEOUT
    app.config["RATE_LIMIT_GLOBAL"] = config.RATE_LIMIT_GLOBAL
    app.config["RATE_LIMIT_MODELS"] = config.RATE_LIMIT_MODELS
    app.config["RATE_LIMIT_CHAT"] = config.RATE_LIMIT_CHAT

    # Set up rate limiting
    app.config["RATELIMIT_DEFAULT"] = config.RATE_LIMIT_GLOBAL
    app.config["RATELIMIT_STORAGE_URI"] = config.RATE_LIMIT_STORAGE_URL
    limiter.init_app(app)

    # Create app-level OpenWebUIClient singleton for TCP connection reuse
    app.openwebui_client = OpenWebUIClient(
        base_url=config.OPENWEBUI_BASE_URL,
        verify_ssl=config.OPENWEBUI_VERIFY_SSL,
        request_timeout=config.REQUEST_TIMEOUT,
        chat_completion_timeout=config.CHAT_COMPLETION_TIMEOUT,
        readiness_timeout=config.READINESS_TIMEOUT,
    )
    atexit.register(app.openwebui_client.close)
    logger.info("OpenWebUIClient singleton created")

    # Register blueprints
    app.register_blueprint(models_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)

    # Set up CORS
    if config.CORS_ENABLED:
        CORS(
            app,
            origins=config.CORS_ALLOWED_ORIGINS,
            methods=config.CORS_ALLOW_METHODS,
            allow_headers=config.CORS_ALLOW_HEADERS,
            supports_credentials=config.CORS_ALLOW_CREDENTIALS,
            max_age=config.CORS_MAX_AGE,
        )
        logger.info("CORS enabled | origins=%s", config.CORS_ALLOWED_ORIGINS)

    logger.info("Application created | debug=%s", config.FLASK_DEBUG)
    logger.info("OpenWebUI backend URL: %s", config.OPENWEBUI_BASE_URL)

    return app


def main() -> None:
    """Main entry point for running the Flask development server."""
    config = Config()

    if config.FLASK_DEBUG:
        print("⚠️  Running in DEBUG mode - NOT suitable for production!")

    app = create_app(config)
    app.run(
        debug=config.FLASK_DEBUG,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
    )


if __name__ == "__main__":
    main()
