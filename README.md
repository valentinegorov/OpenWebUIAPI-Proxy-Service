# OpenWebUI Proxy Server

## Overview

This proxy server translates requests from OpenAI-compatible endpoints to the OpenWebUI API, allowing seamless integration with applications designed for OpenAI APIs.

## Features

- **Seamless Integration**: Works with applications expecting OpenAI API responses.
- **Preserves Authorization**: Passes through the `Authorization` header for secure requests.
- **Timeout Handling**: Increased timeout settings to handle longer processing times.
- **Structured Logging**: Detailed logging with rotation for issue resolution and auditing.
- **Health & Readiness Checks**: Built-in endpoints for monitoring and orchestration.
- **Environment-Based Configuration**: Secure configuration via environment variables.
- **Production Ready**: Debug mode disabled by default, suitable for deployment.

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-username/openwebui-proxy-server.git
   cd openwebui-proxy-server
   ```

2. **Create and Activate Virtual Environment (Recommended)**

   Using a virtual environment isolates dependencies and prevents conflicts with other Python projects.

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

   With the virtual environment activated, install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the project root:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your OpenWebUI base URL:

   ```
   OPENWEBUI_BASE_URL=http://your-openwebui-url:3000
   FLASK_DEBUG=false
   ```

## Configuration

The proxy server is configured via environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENWEBUI_BASE_URL` | URL of your OpenWebUI backend | `http://localhost:3000` | No* |
| `FLASK_DEBUG` | Enable debug mode (`true`/`false`) | `false` | No |

*Required if your OpenWebUI instance is not on localhost:3000

**Note:** The configuration step above (creating `.env` file) is the recommended way to set these variables. Alternatively, you can export them directly in your shell before running the server.

## Running the Server

You can run the proxy server using Flask or Gunicorn for better performance.

**Using Flask:**

```bash
python main.py
```

**Using Gunicorn (Recommended for Production):**

```bash
gunicorn -w 1 -k gevent --timeout 300 main:app --bind 0.0.0.0:5001
```

**Deactivating Virtual Environment:**

When you're done working with the project, you can deactivate the virtual environment:

```bash
deactivate
```

To use the project again, simply navigate to the project directory and activate the virtual environment:

```bash
cd openwebui-proxy-server
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
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

Detailed logging is included to help diagnose and resolve issues. Logs are output to both console and file (`proxy_server.log`).

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
- Location: `proxy_server.log` in the project root

## Health Checks

The proxy server provides two endpoints for monitoring and orchestration:

### `/health` - Basic Health Check
Returns the current status of the proxy server itself.

```bash
curl http://localhost:5001/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### `/ready` - Readiness Probe
Verifies connectivity to the OpenWebUI backend.

```bash
curl http://localhost:5001/ready
```

**Response (Success):**
```json
{
  "status": "ready",
  "backend": "connected",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**Response (Failure):**
```json
{
  "status": "not_ready",
  "backend": "unreachable",
  "error": "Connection refused",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

These endpoints are useful for:
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring dashboards
- Automated restart policies

## Contributing

We welcome contributions to improve the functionality and robustness of this proxy server. Here’s how you can contribute:

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

4. **Commit and Push Your Changes**

   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

5. **Create a Pull Request**

   Visit the repository on GitHub and create a pull request.
