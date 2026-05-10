"""Pytest fixtures and configuration for tests."""

import pytest
from flask import Flask

from app import create_app
from app.config import Config


class TestConfig(Config):
    """Test configuration with mocked values."""

    OPENWEBUI_BASE_URL = "http://test-openwebui:3000"
    OPENWEBUI_VERIFY_SSL = False
    FLASK_DEBUG = True
    FLASK_HOST = "localhost"
    FLASK_PORT = 5002
    REQUEST_TIMEOUT = 5
    CHAT_COMPLETION_TIMEOUT = 10
    READINESS_TIMEOUT = 2
    LOG_LEVEL = "DEBUG"


@pytest.fixture
def app() -> Flask:
    """Create application for testing."""
    config = TestConfig()
    application = create_app(config)
    application.config["TESTING"] = True
    yield application


@pytest.fixture
def client(app: Flask) -> Flask.test_client_class:
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app: Flask) -> Flask.cli_runner_class:
    """Create CLI runner."""
    return app.test_cli_runner()
