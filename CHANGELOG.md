# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-05-10

### Added
- Rate limiting via `Flask-Limiter` with configurable per-endpoint and global limits
- Rate limit configuration in `app/extensions.py` with `X-Forwarded-For` aware client identification
- Environment variables `RATE_LIMIT_GLOBAL`, `RATE_LIMIT_MODELS`, `RATE_LIMIT_CHAT` for granular control
- Rate limiting configuration documented in `README.md`
- CORS and rate limiting variables added to `.env` and `.env.example`

## [1.1.0] - 2026-05-10

### Added
- CORS enable/disable support via `flask-cors` dependency
- CORS configuration in `app/config.py` with secure defaults and safe integer conversion
- New CORS middleware module `app/middleware/cors.py` with initialization logic and security checks
- CORS initialization during application startup in `app/main.py`
- CORS configuration documentation in `README.md` with security guidelines
- Comprehensive test suite in `tests/test_middleware/test_cors.py` covering various CORS scenarios
- `.env.example` updated with CORS configuration examples and security notes

### Changed
- Architecture plan revised for OpenWebUI Responses API (endpoint specifications, request/response formats, implementation details)

## [1.0.1] - 2026-05-10

### Added
- Architecture plan document `responses_endpoint_architecture.md` for OpenAI API `/v1/responses` endpoint
  - POST, GET, and DELETE methods with request/response formats
  - Route handlers, Pydantic models, service layer, and OpenWebUI adapter
  - Non-streaming and streaming request handling flows
  - Error handling, testing strategy, security considerations, and rollout phases
  - Monitoring, observability requirements, and future enhancements

## [1.0.0] - 2026-05-10

### Added
- CHANGELOG.md with initial release entry and project version tracking
- Project version constant (`__version__ = "1.0.0"`) in `main.py` for release tracking

### Fixed
- AttributeError in chat route where Request object was missing `app` attribute
- Flask test runner fixture reference in `conftest.py`
- Added comprehensive logging output to `proxy_server.log` showing error patterns and service calls

### Changed
- Updated `.gitignore` with comprehensive file patterns for various build artifacts and temporary files
- Clarified file inclusion policy for source code files in `.gitignore`
- Updated `app` package initialization to properly import `create_app` function

## [0.4.0] - 2026-05-10

### Added
- `app/__init__.py`: Package initialization with version
- `app/config.py`: Configuration management with environment variables
- `app/main.py`: Flask application factory pattern with logging setup
- `app/routes/`: Route handlers for models, chat, and health endpoints with proper error handling
- `app/services/openwebui_client.py`: OpenWebUI API client with timeout configurations
- `app/utils/logging_config.py`: Rotating file logging system implementation
- `docker/`: Dockerfile and docker-compose.yml for containerized deployment
- `scripts/`: Cross-platform setup scripts for Windows and Linux/macOS
- `tests/`: Comprehensive test suite with pytest fixtures and unit tests
- `.env.example`: Complete configuration options and defaults
- `.gitignore`: Expanded ignore patterns including coverage and temporary files
- `requirements.txt`: Testing dependencies and gevent for production deployment

### Changed
- Established proper Flask application structure with robust configuration management
- Comprehensive logging, health checks, and full test coverage
- Multiple deployment options through Docker and setup scripts

## [0.3.0] - 2026-05-10

### Added
- `OPENWEBUI_VERIFY_SSL` environment variable support for SSL certificate verification
- SSL certificate verification documentation in `README.md` and `DEPLOYMENT.md` with security warnings
- `proxy_server.log` as new log file for structured logging output
- Production-ready SSL verification capabilities and security best practices in documentation

### Changed
- Updated `main.py` implements `OPENWEBUI_VERIFY_SSL` environment variable handling for request verification
- Updated `.gitignore` adds `proxy_server.log` to ignored files and refactors log file patterns

## [0.2.0] - 2026-05-10

### Added
- Comprehensive virtual environment setup instructions with platform-specific activation commands
- Environment variable configuration loading via `python-dotenv`
- Structured logging with rotation (logging to file and stdout)
- Health/readiness endpoints for monitoring
- Request/response logging middleware
- `.env.example` with `OPENWEBUI_BASE_URL` and `FLASK_DEBUG` settings
- `DEPLOYMENT.md`: Detailed production deployment guide covering environment variables, logging, health checks, and security considerations
- `requirements.txt`: Added `python-dotenv` dependency

### Changed
- Updated `.gitignore` with Python virtual environment directories (`venv/`, `.venv/`)

## [0.1.0] - 2025-02-24

### Added
- Initial proxy service implementation
- Basic README with project overview
- Core proxy functionality between OpenAI-compatible clients and OpenWebUI
- Initial project files and structure
