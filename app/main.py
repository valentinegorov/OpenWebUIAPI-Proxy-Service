"""Flask application factory and entry point."""

import logging
from typing import Optional

from flask import Flask

from app.config import Config
from app.routes import models_bp, chat_bp, health_bp
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

    # Register blueprints
    app.register_blueprint(models_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)

    logger.info(f"Application created | debug={config.FLASK_DEBUG}")
    logger.info(f"OpenWebUI backend URL: {config.OPENWEBUI_BASE_URL}")

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
