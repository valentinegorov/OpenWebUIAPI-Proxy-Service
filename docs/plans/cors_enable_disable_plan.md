# Plan: Support CORS Enable/Disable in OpenWebUI Proxy Server

## Overview
Add configurable CORS (Cross-Origin Resource Sharing) support to the Flask proxy server, allowing users to enable/disable CORS and customize allowed origins, methods, and headers via environment variables.

## Implementation Plan

### 1. Add Flask-CORS Dependency
**File:** `requirements.txt`
- Add `flask-cors>=4.0.0` to the dependencies
- This provides robust CORS handling for Flask applications

### 2. Update Configuration Class
**File:** `app/config.py`
Add the following CORS-related configuration properties with secure defaults:

```python
import logging

logger = logging.getLogger(__name__)

def _safe_int(value: str, default: int) -> int:
    """Safely convert string to int with fallback."""
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid integer value '{value}', using default {default}")
        return default

# CORS configuration
CORS_ENABLED = os.environ.get("CORS_ENABLED", "false").lower() in ("true", "1", "yes")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "")  # Empty string = restrictive default
CORS_METHODS = os.environ.get("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS")
CORS_HEADERS = os.environ.get("CORS_HEADERS", "Content-Type,Authorization")
CORS_ALLOW_CREDENTIALS = os.environ.get("CORS_ALLOW_CREDENTIALS", "false").lower() in ("true", "1", "yes")
CORS_MAX_AGE = _safe_int(os.environ.get("CORS_MAX_AGE", "3600"), 3600)
```

### 3. Create CORS Middleware Module
**File:** `app/middleware/cors.py`
Create a new middleware module for CORS initialization:

```python
"""CORS middleware configuration."""

import logging
from typing import Optional
from flask import Flask
from app.config import Config


logger = logging.getLogger(__name__)


def init_cors(app: Flask, config: Config) -> None:
    """
    Initialize CORS for the Flask application.
    
    Args:
        app: Flask application instance
        config: Application configuration
    """
    if not config.CORS_ENABLED:
        logger.info("CORS is disabled")
        return
    
    # Check if flask-cors is installed
    try:
        from flask_cors import CORS
    except ImportError:
        logger.error("CORS_ENABLED=true but flask-cors is not installed. Please install it: pip install flask-cors")
        raise RuntimeError("flask-cors package is required when CORS_ENABLED=true")
    
    # Parse origins (support comma-separated list)
    origins = config.CORS_ORIGINS
    if not origins or origins.strip() == "":
        # Restrictive default: no origins specified means no CORS
        logger.warning("CORS_ENABLED=true but no origins specified. CORS will be restricted.")
        origins = []
    elif origins != "*":
        origins = [origin.strip() for origin in origins.split(",")]
    
    # Security check: wildcard with credentials is not allowed
    if origins == "*" and config.CORS_ALLOW_CREDENTIALS:
        logger.error("CORS_ORIGINS='*' cannot be used with CORS_ALLOW_CREDENTIALS=true")
        raise ValueError("Cannot use wildcard origins (*) with credentials enabled")
    
    # Parse methods
    methods = [method.strip() for method in config.CORS_METHODS.split(",")]
    
    # Parse headers
    headers = [header.strip() for header in config.CORS_HEADERS.split(",")]
    
    cors_config = {
        "resources": {r"/*": {"origins": origins}} if origins else {},
        "methods": methods,
        "allow_headers": headers,
        "supports_credentials": config.CORS_ALLOW_CREDENTIALS,
        "max_age": config.CORS_MAX_AGE,
    }
    
    # Only apply CORS if origins are specified
    if origins:
        CORS(app, **cors_config)
        logger.info(f"CORS enabled | origins={config.CORS_ORIGINS} | methods={config.CORS_METHODS}")
    else:
        logger.warning("CORS enabled but no valid origins configured. CORS headers will not be added.")
```

### 4. Update Application Factory
**File:** `app/main.py`
- Import the CORS initialization function
- Call `init_cors()` after creating the app and before registering blueprints
- Ensure all CORS config values are available to the app

```python
from app.middleware.cors import init_cors

# After loading configuration into app config
# (All CORS config values are already in the Config object)

# Initialize CORS (before registering blueprints)
init_cors(app, config)

# Register blueprints (after CORS initialization)
app.register_blueprint(models_bp)
...
```

### 5. Update Documentation
**File:** `README.md`
Add CORS configuration section to the configuration table:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CORS_ENABLED` | Enable CORS (`true`/`false`) | `false` | No |
| `CORS_ORIGINS` | Allowed origins (comma-separated or `*`). Empty = restrictive | `` (empty) | No |
| `CORS_METHODS` | Allowed HTTP methods | `GET,POST,PUT,DELETE,OPTIONS` | No |
| `CORS_HEADERS` | Allowed headers | `Content-Type,Authorization` | No |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials (`true`/`false`) | `false` | No |
| `CORS_MAX_AGE` | Cache preflight results (seconds) | `3600` | No |

Add usage examples:
```bash
# Enable CORS for all origins (not recommended for production with credentials)
CORS_ENABLED=true
CORS_ORIGINS=*

# Enable CORS for specific origins (recommended)
CORS_ENABLED=true
CORS_ORIGINS=https://example.com,https://app.example.com

# Enable CORS with credentials (requires specific origins, not wildcard)
CORS_ENABLED=true
CORS_ORIGINS=https://example.com
CORS_ALLOW_CREDENTIALS=true

# Disable CORS (default)
CORS_ENABLED=false
```

Add security notes:
- **Default**: CORS is disabled by default for maximum security
- **Wildcard Warning**: Never use `CORS_ORIGINS=*` with `CORS_ALLOW_CREDENTIALS=true`
- **Production**: Always specify explicit origins in production environments
- **Empty Origins**: If `CORS_ENABLED=true` but `CORS_ORIGINS` is empty, CORS will not add headers

### 6. Add Tests
**File:** `tests/test_middleware/test_cors.py` (new file)
Ensure test directory structure exists:
```bash
mkdir -p tests/test_middleware
```

Test cases:
- Test CORS disabled by default
- Test CORS enabled with wildcard origins
- Test CORS enabled with specific origins
- Test CORS methods and headers configuration
- Test CORS with credentials (and rejection of wildcard + credentials)
- Test OPTIONS preflight requests
- Test error handling when flask-cors is missing
- Test invalid integer values for CORS_MAX_AGE
- Test empty origins configuration

### 7. Update .env.example
Create or update `.env.example` file with CORS configuration examples:
```bash
# CORS Configuration
# Security Note: CORS is disabled by default. Enable only when needed.
CORS_ENABLED=false
CORS_ORIGINS=
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_HEADERS=Content-Type,Authorization
CORS_ALLOW_CREDENTIALS=false
CORS_MAX_AGE=3600

# Example: Enable for specific origins
# CORS_ENABLED=true
# CORS_ORIGINS=https://example.com,https://app.example.com

# Example: Enable for all origins (development only)
# CORS_ENABLED=true
# CORS_ORIGINS=*
```

## Security Considerations

1. **Default Disabled**: CORS is disabled by default for security
2. **Restrictive Default Origins**: Empty string default instead of wildcard
3. **Wildcard + Credentials Block**: Explicit validation prevents insecure configuration
4. **Origin Validation**: Support for specific origin lists to restrict access
5. **Missing Dependency Handling**: Clear error when flask-cors is not installed
6. **Production Guidance**: Documentation emphasizes explicit origins in production

## Testing Strategy

1. Unit tests for configuration parsing (including invalid values)
2. Integration tests for CORS headers in responses
3. Preflight request (OPTIONS) handling tests
4. Tests for various origin configurations (wildcard, specific, empty)
5. Verify CORS is truly disabled when `CORS_ENABLED=false`
6. Error handling tests (missing package, invalid config combinations)
7. Security tests (wildcard + credentials rejection)

## Files to Modify/Create

1. ✏️ `requirements.txt` - Add flask-cors dependency
2. ✏️ `app/config.py` - Add CORS configuration properties with safe defaults
3. ➕ `app/middleware/__init__.py` - Ensure middleware package exists
4. ➕ `app/middleware/cors.py` - New CORS middleware module with error handling
5. ✏️ `app/main.py` - Initialize CORS in app factory
6. ✏️ `README.md` - Document CORS configuration with security notes
7. ➕ `tests/test_middleware/__init__.py` - Ensure test package exists
8. ➕ `tests/test_middleware/test_cors.py` - New test file
9. ➕ `.env.example` - Example environment file with CORS settings

## Error Handling Improvements

1. **Safe Integer Conversion**: `_safe_int()` function prevents ValueError on invalid env vars
2. **Missing Package Detection**: Clear error message if flask-cors not installed
3. **Invalid Config Validation**: Reject wildcard + credentials combination
4. **Logging**: Comprehensive logging for debugging and audit trails
5. **Graceful Degradation**: Empty origins handled gracefully with warnings

This revised plan addresses all identified logical errors and contradictions while maintaining security best practices.
