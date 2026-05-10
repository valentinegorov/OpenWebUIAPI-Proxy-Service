# OpenWebUI Proxy Server - Production Deployment Guide

## High-Priority Improvements Implemented

### 1. ✅ Environment Variable Configuration
- `OPENWEBUI_BASE_URL` is now loaded from environment variables
- Default fallback: `http://localhost:3000`
- Supports `.env` file via `python-dotenv`

**Usage:**
```bash
# Set via environment variable
export OPENWEBUI_BASE_URL=http://your-openwebui-url:3000

# Or create a .env file
cp .env.example .env
# Edit .env with your configuration
```

### 2. ✅ Debug Mode Disabled by Default
- Debug mode now controlled by `FLASK_DEBUG` environment variable
- Default: `false` (production-safe)
- Warning logged when debug mode is enabled

**Usage:**
```bash
# Development (debug enabled)
export FLASK_DEBUG=true

# Production (debug disabled - default)
export FLASK_DEBUG=false
```

### 3. ✅ Structured Logging
- Timestamp, level, logger name, and message format
- Dual output: console + rotating file handler
- File rotation: 10MB max, 5 backup files
- Log file: `proxy_server.log`

**Log Format:**
```
2024-01-15 10:30:45 | INFO | main | Request received | endpoint=/v1/models | method=GET | client_ip=192.168.1.1
2024-01-15 10:30:46 | INFO | main | Response from OpenWebUI | status=200 | latency_ms=245.32
```

### 4. ✅ Request/Response Logging
All endpoints now log:
- Incoming request details (endpoint, method, client IP)
- Request payload summary (model name, message count)
- Backend response status and latency
- Success/failure outcomes
- Error details with stack traces

**Privacy Note:** Full message content is NOT logged to protect user privacy.

### 5. ✅ Health Check Endpoints

#### `/health` - Basic Health Check
Returns server status without checking backend connectivity.
```bash
curl http://localhost:5001/health
# Response: {"status": "healthy", "timestamp": "2024-01-15T10:30:45.123456"}
```

#### `/ready` - Readiness Probe
Verifies backend OpenWebUI connectivity before marking as ready.
```bash
curl http://localhost:5001/ready
# Response (success): {"status": "ready", "backend": "connected", "timestamp": "..."}
# Response (failure): {"status": "not_ready", "backend": "unreachable", "error": "...", "timestamp": "..."}
```

**HTTP Status Codes:**
- `200`: Healthy/Ready
- `503`: Not Ready (backend unavailable)

---

## Quick Start

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your OpenWebUI URL

# Run the server
python main.py
```

### Production (with Gunicorn)
```bash
# Set environment variables
export OPENWEBUI_BASE_URL=https://openwebui.yourdomain.com
export FLASK_DEBUG=false
export FLASK_ENV=production

# Run with Gunicorn (recommended for production)
gunicorn --workers 4 --bind 0.0.0.0:5001 --access-logfile - --error-logfile - main:app
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY .env.example .env

ENV OPENWEBUI_BASE_URL=http://openwebui:3000
ENV FLASK_DEBUG=false

EXPOSE 5001

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5001", "main:app"]
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENWEBUI_BASE_URL` | Yes* | `http://localhost:3000` | OpenWebUI backend URL |
| `OPENWEBUI_VERIFY_SSL` | No | `true` | Verify SSL certificates (set to `false` for self-signed certs) |
| `FLASK_DEBUG` | No | `false` | Enable debug mode (⚠️ not for production) |
| `FLASK_ENV` | No | `production` | Flask environment mode |

*Required in production; default is suitable only for local development.

### SSL Certificate Verification

The `OPENWEBUI_VERIFY_SSL` environment variable controls whether the proxy server verifies SSL certificates when connecting to the OpenWebUI backend.

- **Default:** `true` (SSL verification enabled)
- **To trust self-signed certificates:** Set to `false`

```bash
# Development with self-signed certificate
export OPENWEBUI_VERIFY_SSL=false

# Production with valid SSL certificate (default)
export OPENWEBUI_VERIFY_SSL=true
```

⚠️ **Security Warning:** Disabling SSL verification (`OPENWEBUI_VERIFY_SSL=false`) should only be used in:
- Development environments
- Trusted internal networks
- Testing scenarios

In production environments, always use properly signed SSL certificates from a trusted Certificate Authority (CA).

---

## Monitoring & Observability

### Log Analysis
```bash
# View recent logs
tail -f proxy_server.log

# Search for errors
grep "ERROR" proxy_server.log

# Monitor latency
grep "latency_ms" proxy_server.log | awk -F'|' '{print $NF}'
```

### Kubernetes Probes
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 5001
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /ready
    port: 5001
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3
```

---

## Security Considerations

✅ **Implemented:**
- Debug mode disabled by default
- No sensitive data in logs (message content excluded)
- Structured logging for audit trails

⚠️ **Recommended Next Steps:**
- Add HTTPS/TLS termination (via reverse proxy)
- Implement rate limiting
- Add input validation
- Configure CORS policies
- Add authentication/authorization middleware

---

## Troubleshooting

### Server won't start
```bash
# Check if OPENWEBUI_BASE_URL is set correctly
echo $OPENWEBUI_BASE_URL

# Verify port 5001 is available
netstat -tlnp | grep 5001
```

### Backend connection failures
```bash
# Test backend connectivity directly
curl http://your-openwebui-url:3000/api/models

# Check readiness endpoint for details
curl http://localhost:5001/ready
```

### Logging issues
```bash
# Check log file permissions
ls -la proxy_server.log

# Verify disk space
df -h
```
