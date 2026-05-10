# OpenWebUI Proxy Server

**Version 1.2.0** — Proxy server that translates OpenAI-compatible API requests to the OpenWebUI backend.

## Overview

This proxy server translates requests from OpenAI-compatible endpoints to the OpenWebUI API, allowing seamless integration with applications designed for OpenAI APIs. It supports CORS configuration, SSL verification control, structured logging, health checks, and multiple deployment options.

## Features

- **Seamless Integration**: Works with applications expecting OpenAI API responses
- **OpenAI-Compatible Endpoints**: `/v1/models`, `/v1/chat/completions`, `/v1/responses` (architecture planned)
- **CORS Support**: Configurable CORS with secure defaults via `flask-cors`
- **SSL Verification Control**: Enable/disable SSL certificate verification for self-signed certificates
- **Authorization Passthrough**: Passes through the `Authorization` header for secure requests
- **Structured Logging**: Rotating file and console logging with structured format
- **Health & Readiness Checks**: Built-in endpoints for monitoring and orchestration
- **Environment-Based Configuration**: Secure configuration via environment variables
- **Modular Architecture**: Flask application factory with blueprints, services layer, and utilities
- **Docker Support**: Containerized deployment via Dockerfile and docker-compose
- **Cross-Platform Setup Scripts**: Setup scripts for both Windows and Linux/macOS
- **Production Ready**: Debug mode disabled by default, Gunicorn/gevent support

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Quick Start

1. **Clone the Repository**

   ```bash
   git clone https://github.com/uwzis/openwebuiapi-proxy-service.git
   cd openwebuiapi-proxy-service
   ```

2. **Create and Activate Virtual Environment (Recommended)**

   **On Linux/macOS:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **On Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   You should see `(venv)` prefix in your terminal prompt, indicating the virtual environment is active.

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your OpenWebUI base URL:

   ```ini
   OPENWEBUI_BASE_URL=http://your-openwebui-url:3000
   FLASK_DEBUG=false
   ```

5. **Run the Server**

   ```bash
   python main.py
   ```

## Configuration

The proxy server is configured via environment variables (`.env` file or system environment):

### General Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENWEBUI_BASE_URL` | URL of your OpenWebUI backend | `http://localhost:3000` | No* |
| `OPENWEBUI_VERIFY_SSL` | Verify SSL certificates (`true`/`false`) | `true` | No |
| `FLASK_DEBUG` | Enable debug mode (`true`/`false`) | `false` | No |
| `FLASK_HOST` | Flask server bind address | `0.0.0.0` | No |
| `FLASK_PORT` | Flask server port | `5001` | No |

*\*Required if your OpenWebUI instance is not on localhost:3000*

### Timeout Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `REQUEST_TIMEOUT` | General request timeout (seconds) | `30` |
| `CHAT_COMPLETION_TIMEOUT` | Chat completion timeout (seconds) | `120` |
| `READINESS_TIMEOUT` | Readiness check timeout (seconds) | `5` |

### Logging Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `LOG_MAX_BYTES` | Maximum log file size before rotation (bytes) | `10485760` (10 MB) |
| `LOG_BACKUP_COUNT` | Number of rotated log files to keep | `5` |

### CORS Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ENABLED` | Enable CORS support (`true`/`false`) | `true` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed origins | `*` |
| `CORS_ALLOW_METHODS` | Comma-separated list of allowed HTTP methods | `GET, POST, PUT, DELETE, OPTIONS` |
| `CORS_ALLOW_HEADERS` | Comma-separated list of allowed headers | `Content-Type, Authorization` |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials (`true`/`false`) | `true` |
| `CORS_MAX_AGE` | CORS preflight cache duration (seconds) | `3600` |

### Rate Limiting

Rate limits use the [Flask-Limiter](https://flask-limiter.readthedocs.io/) notation (`"N per second/minute/hour/day"`).

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_GLOBAL` | Default rate limit for all endpoints | `100 per minute` |
| `RATE_LIMIT_MODELS` | Rate limit for `/v1/models` | `30 per minute` |
| `RATE_LIMIT_CHAT` | Rate limit for `/v1/chat/completions` | `30 per minute` |

Requests are identified by client IP (supporting `X-Forwarded-For` for proxied deployments).

### SSL Certificate Verification

By default, the proxy server verifies SSL certificates when connecting to the OpenWebUI backend. If your OpenWebUI instance uses a self-signed certificate, you can disable SSL verification:

```bash
OPENWEBUI_VERIFY_SSL=false
```

> ⚠️ **Warning:** Disabling SSL verification should only be used in development environments or when you trust the network. In production, use properly signed SSL certificates.

## Running the Server

### Using Flask (Development)

```bash
python main.py
```

### Using Gunicorn (Recommended for Production)

```bash
gunicorn -w 1 -k gevent --timeout 300 main:app --bind 0.0.0.0:5001
```

### Using Flask Application Factory

```bash
python -c "from app.main import create_app; app = create_app(); app.run()"
```

### Using Docker

```bash
docker-compose -f docker/docker-compose.yml up --build
```

## Usage

### Example Requests

#### GET /v1/models

```bash
curl -X GET http://localhost:5001/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

#### POST /v1/chat/completions

```bash
curl -X POST http://localhost:5001/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ytm-website",
    "messages": [{"role": "user", "content": "Why is the sky blue?"}]
  }'
```

## Logging

Detailed logging is included to help diagnose and resolve issues. Logs are output to both console and file (`logs/proxy_server.log`).

**Log Format:**
```
YYYY-MM-DD HH:MM:SS | LEVEL | LOGGER_NAME | MESSAGE
```

**Example Log Entries:**
```
2024-01-15 10:30:45 | INFO | main | Request received | endpoint=/v1/models | method=GET | client_ip=192.168.1.100
2024-01-15 10:30:45 | INFO | main | Response from OpenWebUI | status=200 | latency_ms=125.34
2024-01-15 10:30:45 | INFO | main | Successfully retrieved models
```

**Log Rotation:**
- Maximum file size: 10 MB
- Backup count: 5 rotated files
- Location: `logs/proxy_server.log`

## Health Checks

The proxy server provides two endpoints for monitoring and orchestration:

### `/health` — Basic Health Check

Returns the current status of the proxy server itself.

```bash
curl http://localhost:5001/health
```

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### `/ready` — Readiness Probe

Verifies connectivity to the OpenWebUI backend.

```bash
curl http://localhost:5001/ready
```

```json
{
  "status": "ready",
  "backend": "connected",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

These endpoints are useful for:
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring dashboards
- Automated restart policies

## Project Structure

```
├── app/                    # Flask application package
│   ├── __init__.py         # Package init with version
│   ├── config.py           # Configuration management
│   ├── main.py             # Application factory
│   ├── middleware/         # Middleware modules
│   │   ├── __init__.py
│   │   └── cors.py         # CORS configuration
│   ├── routes/             # Route handlers (blueprints)
│   │   ├── __init__.py
│   │   ├── chat.py         # /v1/chat/completions
│   │   ├── health.py       # /health, /ready
│   │   └── models.py       # /v1/models
│   ├── services/           # Service layer
│   │   ├── __init__.py
│   │   └── openwebui_client.py  # OpenWebUI API client
│   └── utils/              # Utilities
│       ├── __init__.py
│       └── logging_config.py    # Logging setup
├── docker/                 # Docker deployment files
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/                   # Documentation
│   └── plans/              # Architecture plans
├── scripts/                # Cross-platform setup scripts
│   ├── setup.bat           # Windows setup
│   └── setup.sh            # Linux/macOS setup
├── tests/                  # Test suite
│   ├── test_routes/        # Route handler tests
│   ├── test_services/      # Service layer tests
│   └── conftest.py         # Pytest fixtures
├── main.py                 # Standalone entry point
├── .env.example            # Example environment config
├── requirements.txt        # Python dependencies
├── CHANGELOG.md            # Release history
├── DEPLOYMENT.md           # Deployment guide
├── LICENSE                 # License file
└── README.md               # This file
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/models` | List available models |
| `POST` | `/v1/chat/completions` | Create a chat completion |
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness probe |

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Deploy with Docker

```bash
# Build and start the service
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

## Contributing

We welcome contributions! Here's how:

1. **Fork the Repository**

   ```bash
   git clone https://github.com/uwzis/openwebuiapi-proxy-service.git
   cd openwebuiapi-proxy-service
   ```

2. **Create a New Branch**

   ```bash
   git checkout -b feature/new-feature
   ```

3. **Make Your Changes**

4. **Run Tests**

   ```bash
   pytest tests/
   ```

5. **Commit and Push**

   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

6. **Create a Pull Request**

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full release history.

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.
