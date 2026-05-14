# Phase 2: Stability & Observability — Research

## Current State Analysis

### Already Implemented ✅

#### 1. Request ID Tracking
- **File**: `app/middleware/request_id.py`
- **Pattern**: Flask `before_request`/`after_request`/`teardown_request` hooks
- **Mechanism**: UUID generated per request, stored in `g.request_id` + `ContextVar`
- **Logging**: Request ID appears in all log statements via `RequestIDFilter`
- **Response headers**: `X-Request-ID` returned in every response
- **Error responses**: All error responses include `request_id` field

#### 2. Retry Logic with Exponential Backoff
- **File**: `app/services/openwebui_client.py`
- **Pattern**: `requests.adapters.Retry` mounted on `requests.Session`
- **Configuration**: `retry_max_attempts=3`, `retry_backoff_factor=0.5`, statuses=[502,503,504]
- **Session pooling**: `pool_connections=10`, `pool_maxsize=20` via `HTTPAdapter`
- **Config-driven**: `RETRY_MAX_ATTEMPTS`, `RETRY_BACKOFF_FACTOR`, `RETRY_STATUSES` in `app/config.py`

#### 3. Metrics Endpoint with OpenTelemetry + Prometheus
- **Files**: `app/utils/metrics.py` (instrumentation), `app/routes/metrics.py` (route)
- **Pattern**: OpenTelemetry SDK with `PrometheusMetricReader` for Prometheus export
- **Metrics**: `request_latency` (histogram), `request_count` (counter), `error_count` (counter)
- **Route**: `GET /metrics` (exempt from rate limiting)
- **Initialization**: Called in `create_app()` via `setup_metrics()`
- **Shutdown**: Registered with `atexit.register(shutdown_metrics)`

### Partially Implemented 🔄

#### 4. Request/Response Logging
- Request start/complete already logged in `init_request_id_middleware`
- Backend call latencies logged in `openwebui_client.py`
- **Gap**: No verbosity toggle to enable/disable detailed request/response body logging
- **Gap**: No config option for request/response payload logging

#### 5. Error Handler
- **File**: `app/utils/error_handler.py` — covers `Timeout` and general `RequestException`
- **Coverage**: ~79% (gap: exception handling in `status_code` extraction — bare `try/except Exception: pass`)
- **Gap**: No distinction between different error types beyond timeout vs generic
- **Gap**: No handling for `ConnectionError`, `SSLError`, or other specific exception types

#### 6. CONTEXT.md Status Tracking
- Lists some items as "Done" but some are no longer accurate
- Needs update to reflect actual implementation status

### Not Started ⬜

#### 7. Documentation Updates
- Monitoring setup with Zabbix — not started
- Rate limiting configuration — not started
- Debugging with request IDs — not started
- New configuration options (retry, logging, metrics) — not started

## Technical Approaches

### Approach A: Request/Response Logging Toggle

**Pattern**: Add a `LOG_REQUEST_DETAIL` config flag + middleware toggle.

**Existing analog**: The `init_request_id_middleware` function already follows the Flask hook pattern. Add a new middleware function (or extend existing) that conditionally logs request/response bodies based on config.

**Implementation sketch**:
1. Add `LOG_REQUEST_BODY` and `LOG_RESPONSE_BODY` to `Config` class (default: `false`)
2. Create `init_request_logging_middleware(app)` in a new or existing middleware file
3. In `before_request`: log method, path, headers (optional), body (if enabled)
4. In `after_request`: log status, response body (if enabled), latency
5. Wire into `create_app()` in `app/main.py`

**Risk**: Logging request/response bodies can leak sensitive data (auth tokens, user messages). Must be opt-in and include a warning.

### Approach B: Error Handler Expansion

**Pattern**: Expand `handle_proxy_error` to handle specific exception types.

**Existing analog**: The function already handles `Timeout` and `RequestException`. Add handlers for `ConnectionError`, `SSLError`, and fix the bare `try/except`.

**Implementation sketch**:
1. Remove the bare `except Exception: pass` in status code extraction
2. Add handling for `ConnectionError` → 503 "Backend unreachable"
3. Add handling for `SSLError` → 502 "SSL verification failed"  
4. Return distinct error messages for each type for easier debugging

**Testing**: `test_error_handler.py` — test each exception type returns correct status code and error message. Current test coverage gap is lines 30-33.

### Approach C: Documentation Updates

**Pattern**: Create monitoring and configuration docs in `docs/` directory.

**Required documents**:
1. `docs/monitoring.md` — Zabbix Prometheus integration guide
2. `docs/rate-limiting.md` — Rate limiting configuration
3. `docs/debugging.md` — Using request IDs for debugging
4. Update `README.md` with new configuration options

**Existing analog**: `docs/deployment.md` (check existence and style)

### Approach D: Test Coverage Expansion

**Pattern**: Add tests following existing patterns in `tests/conftest.py`.

**Required tests**:
1. `test_routes/test_metrics.py` — Test metrics endpoint returns 200 and Prometheus format
2. Test error handler with each exception type
3. Test request ID middleware with custom `X-Request-ID` header
4. Test retry logic behavior

## Codebase Patterns

### Flask Hook Pattern (for middleware)
```
@app.before_request / @app.after_request / @app.teardown_request
```
Used in `app/middleware/request_id.py`. Any new middleware should follow this same pattern.

### Config-Driven Feature Toggle Pattern
```
class Config:
    FEATURE_ENABLED = os.environ.get("FEATURE_ENABLED", "false").lower() in (...)
```
Used throughout `app/config.py`. New toggles should follow this EXACT pattern.

### Blueprint Registration Pattern
```
bp = Blueprint("name", __name__)
@bp.route("/path", methods=["GET"])
```
Registered in `app/routes/__init__.py` and wired in `app/main.py::create_app()`.

### Test Pattern
```
@pytest.fixture
def client(app): return app.test_client()

def test_endpoint(client):
    response = client.get("/path")
    assert response.status_code == 200
```
Mock the `OpenWebUIClient` via `conftest.py::mock_openwebui_client`.

## Dependencies and Risks

| Dependency | Risk | Mitigation |
|------------|------|------------|
| opentelemetry-api >= 1.20 | Version compatibility | Already installed and working |
| opentelemetry-sdk >= 1.20 | Same | Already installed and working |
| opentelemetry-instrumentation-flask >= 0.40b0 | Added but may conflict with manual instrumentation | Test with pytest |
| prometheus-client >= 0.19 | Already installed and working | — |

**Performance risk**: Logging request/response bodies adds I/O overhead. Mitigation: disabled by default.

## Validation Architecture

| Feature | Validation Method | Acceptance Criteria |
|---------|------------------|-------------------|
| Metrics endpoint | `client.get("/metrics")` | Returns 200 with `text/plain; version=0.0.4` content type |
| Error handler | Unit tests per exception type | Each returns correct status code + `request_id` in response |
| Request/response logging | Integration test + log capture | Body logged when toggle is on, not logged when toggle is off |
| Documentation | Manual review | README and docs reflect new options |

## Specific Recommendations for Planning

1. **Plan 1: Error Handler Expansion** — Fix coverage gap in `error_handler.py`, add specific exception types. Test each.
2. **Plan 2: Request/Response Logging Toggle** — Add config option + middleware for body logging. Test both on/off states.
3. **Plan 3: CONTEXT.md Update** — Update to reflect actual implementation status.
4. **Plan 4: Documentation** — Write monitoring, rate limiting, and debugging docs. Update README.
5. **Plan 5: Test Coverage** — Add tests for metrics endpoint and request ID middleware.

All plans should maintain test coverage at 85%+ (currently 93%).
