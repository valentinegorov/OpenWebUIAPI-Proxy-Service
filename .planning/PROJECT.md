# OpenWebUI Proxy Server - Project Context

## Overview
**Project Name**: OpenWebUI Proxy Server  
**Version**: 1.2.0  
**Type**: Flask-based API Proxy  
**Purpose**: Translate OpenAI-compatible API requests to OpenWebUI backend

## Architecture
- **Framework**: Flask with application factory pattern
- **Deployment**: Docker with Gunicorn/gevent WSGI server
- **Configuration**: Environment-based via `app/config.py`
- **Structure**: Modular with blueprints, services, and utilities

## Core Components
| Component | Path | Description |
|-----------|------|-------------|
| Main App | `app/main.py` | Flask application factory |
| Config | `app/config.py` | Environment configuration |
| Routes | `app/routes/` | API endpoints (`/v1/models`, `/v1/chat/completions`, `/health`, `/ready`) |
| Services | `app/services/` | OpenWebUI HTTP client with SSL control |
| Utils | `app/utils/` | Structured logging with rotation |
| Middleware | `app/middleware/` | CORS configuration |
| Tests | `tests/` | Full test coverage |

## Key Features
- OpenAI API compatibility layer
- SSL verification control for backend connections
- CORS middleware configuration
- Rate limiting support
- Health and readiness endpoints
- Structured logging with file rotation

## Configuration (Environment Variables)
- `OPENWEBUI_BASE_URL`: Backend URL
- `OPENWEBUI_API_KEY`: Authentication key
- `CORS_ORIGINS`: Allowed origins
- `RATE_LIMIT_ENABLED`: Enable/disable rate limiting
- `SSL_VERIFY`: SSL verification toggle
- `REQUEST_TIMEOUT`: Timeout in seconds
- `LOG_LEVEL`: Logging verbosity

## Development Status
- ✅ Core proxy functionality implemented
- ✅ Docker deployment ready
- ✅ Test suite in place
- 🔄 Ongoing: Feature expansion and maintenance

## Next Steps
1. Extend model management capabilities
2. Add streaming response optimizations
3. Implement advanced rate limiting strategies
4. Enhance monitoring and observability
