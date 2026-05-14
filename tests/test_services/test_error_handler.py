"""Tests for error handler functionality."""

from unittest.mock import Mock, patch

import pytest
from flask import Flask, g
from requests.exceptions import RequestException, Timeout, ConnectionError as RequestsConnectionError, SSLError

from app import create_app
from app.config import Config
from app.utils.error_handler import handle_proxy_error


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
def app():
    """Create application for testing."""
    config = TestConfig()
    application = create_app(config)
    application.config["TESTING"] = True
    yield application


class TestErrorHandler:
    """Test cases for the error handler."""

    def test_timeout_returns_504(self, app):
        """Test that Timeout exception returns 504 status code."""
        with app.app_context():
            g.request_id = "test-123"
            e = Timeout("Request timed out")
            response, status_code = handle_proxy_error(e)
            
            assert status_code == 504
            json_data = response.get_json()
            assert json_data["error"] == "Request timed out"
            assert json_data["request_id"] == "test-123"

    def test_connection_error_returns_503(self, app):
        """Test that ConnectionError returns 503 status code."""
        with app.app_context():
            g.request_id = "test-123"
            e = RequestsConnectionError("Backend unreachable")
            response, status_code = handle_proxy_error(e)
            
            assert status_code == 503
            json_data = response.get_json()
            assert json_data["error"] == "Backend unreachable"
            assert json_data["request_id"] == "test-123"

    def test_ssl_error_returns_502(self, app):
        """Test that SSLError returns 502 status code."""
        with app.app_context():
            g.request_id = "test-123"
            e = SSLError("SSL verification failed")
            response, status_code = handle_proxy_error(e)
            
            assert status_code == 502
            json_data = response.get_json()
            assert json_data["error"] == "SSL verification failed"
            assert json_data["request_id"] == "test-123"

    def test_generic_request_exception_returns_502(self, app):
        """Test that generic RequestException without response returns 502."""
        with app.app_context():
            g.request_id = "test-123"
            e = RequestException("Generic error")
            response, status_code = handle_proxy_error(e)
            
            assert status_code == 502
            json_data = response.get_json()
            assert "request failed" in json_data["error"]
            assert json_data["request_id"] == "test-123"

    def test_error_with_response_status_code(self, app):
        """Test that backend response status codes are propagated."""
        with app.app_context():
            g.request_id = "test-123"
            e = RequestException("Rate limited")
            mock_response = Mock()
            mock_response.status_code = 429
            e.response = mock_response
            
            response, status_code = handle_proxy_error(e)
            
            assert status_code == 429

    def test_request_id_in_response(self, app):
        """Test that request_id is included in error response."""
        with app.app_context():
            g.request_id = "test-123"
            e = RequestException("Error")
            response, status_code = handle_proxy_error(e, endpoint_name="test")
            
            json_data = response.get_json()
            assert "request_id" in json_data
            assert isinstance(json_data["request_id"], str)
