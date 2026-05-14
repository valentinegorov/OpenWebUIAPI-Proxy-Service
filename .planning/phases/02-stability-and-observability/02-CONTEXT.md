# Context - Phase 2: Stability & Observability

## Locked Decisions

### 1. Rate Limiting Strategy
**Decision**: Simple Fixed Window Rate Limiting  
**Rationale**: 
- Deployment target: local network with small user groups
- Minimal overhead and complexity
- Easy to implement, debug, and maintain
- flask-limiter already integrated, uses fixed window by default

**Implementation Details**:
- Use flask-limiter with in-memory storage (default)
- Key function respects X-Forwarded-For header for proper client identification
- Default limits: 30 requests/minute for chat endpoint, configurable per endpoint
- No Redis dependency required for local deployments

### 2. Metrics & Telemetry Backend
**Decision**: OpenTelemetry + Zabbix Prometheus Exporter  
**Rationale**:
- Full compatibility with Zabbix 5.4+ via Prometheus exporter module
- OpenTelemetry provides vendor-neutral instrumentation
- Easy migration path to other monitoring systems if needed
- Minimal code changes required - uses standard Prometheus metrics format

**Implementation Details**:
- Use `opentelemetry-api` and `opentelemetry-sdk` packages
- Export metrics via Prometheus endpoint (`/metrics`)
- Zabbix collects metrics using zabbix-agent2 with Prometheus plugin or standalone Zabbix Prometheus exporter
- Key metrics: request count, latency histograms, error rates, active connections

### 3. CI/CD Pipeline
**Decision**: Deferred to Phase 3  
**Rationale**:
- Current focus on stability and observability fundamentals
- Local network deployment reduces immediate CI/CD urgency
- Allows more time to evaluate best-fit solution for team workflow

---

## Current State Analysis

### Test Coverage
- **Current**: 93% overall coverage
- **Target**: 85%+ ✅ (Already exceeded)
- **Gaps**: 
  - `app/utils/error_handler.py`: 76% (lines 30-33: exception handling in status code extraction)
  - `app/main.py`: 85% (lines 92-98, 106: main entry point, not critical for library usage)
  - `app/extensions.py`: 90% (line 18: X-Forwarded-For fallback branch)

### Error Handling Status
- Shared error handler exists in `app/utils/error_handler.py`
- Handles Timeout and general RequestException
- Returns standardized JSON error responses
- **Gap**: No retry logic for transient backend failures

### Logging Status
- Structured logging implemented with rotation
- Console and file handlers configured
- Format: `%(asctime)s | %(levelname)s | %(name)s | [%(request_id)s] | %(message)s`
- ✅ Request ID tracking implemented via context vars and middleware
- ✅ Request/response lifecycle logging with status codes
- ✅ Error responses include request_id for client-side correlation

### Observability Gaps
1. No distributed tracing (deferred)
2. No metrics endpoint (TODO: Phase 2 remaining work)
3. ✅ Request ID propagation implemented
4. ✅ Backend call latencies logged with timing information

---

## Technical Debt Summary

| Item | Priority | Effort | Status | Notes |
|------|----------|--------|--------|-------|
| Add request ID tracking | High | Low | ✅ Done | UUID per request, included in all log statements and error responses |
| Implement retry logic | High | Medium | ✅ Done | Exponential backoff for 5xx errors using requests.Retry adapter |
| Add metrics endpoint | High | Medium | TODO | Prometheus-compatible `/metrics` endpoint with OpenTelemetry |
| Expand error handler coverage | Medium | Low | Partial | Current: 79%, edge cases in status code extraction still uncovered |
| Request/response logging toggle | Medium | Low | Partial | Latency logging added, verbosity toggle pending |
| Documentation updates | Medium | Medium | TODO | API usage, configuration, monitoring setup |

---

## Dependencies Status

### Already Installed
- Flask >= 3.0
- flask-cors >= 4.0
- requests == 2.31.0
- Flask-Limiter >= 3.5.0
- pytest == 7.4.3
- pytest-cov == 4.1.0

### Required for Phase 2
- `opentelemetry-api` >= 1.20
- `opentelemetry-sdk` >= 1.20
- `opentelemetry-instrumentation-flask` >= 0.40b0
- `prometheus-client` >= 0.19 (for metrics export)

### Optional (Phase 3+)
- redis (for distributed rate limiting)
- opentelemetry-exporter-otlp (for OTLP export)

---

## File Structure Reference

```
/workspace
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py          # flask-limiter instance
│   ├── main.py                # Application factory
│   ├── middleware/
│   │   └── __init__.py        # CORS setup
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py            # /v1/chat/completions
│   │   ├── health.py          # /health, /ready
│   │   └── models.py          # /v1/models
│   ├── services/
│   │   ├── __init__.py
│   │   └── openwebui_client.py # HTTP client with session pooling
│   └── utils/
│       ├── __init__.py
│       ├── error_handler.py   # Shared error handling
│       └── logging_config.py  # Structured logging setup
├── tests/
│   ├── conftest.py
│   ├── test_routes/
│   │   ├── test_chat.py
│   │   ├── test_health.py
│   │   └── test_models.py
│   ├── test_services/
│   │   └── test_openwebui_client.py
│   └── test_session_reuse.py
├── .planning/
│   ├── PROJECT.md
│   ├── REQUIREMENTS.md
│   ├── ROADMAP.md
│   ├── STATE.md
│   └── config.json
├── logs/                      # Log file output directory
├── docker/
├── docs/
├── scripts/
├── requirements.txt
├── .env.example
└── README.md
```

---

## Success Criteria for Phase 2

1. ✅ Request ID tracking implemented and visible in all logs
2. ✅ Retry logic with exponential backoff for backend calls
3. ✅ Enhanced error responses with request ID for client debugging
4. ✅ Metrics endpoint (`/metrics`) exposing Prometheus-format metrics
5. ✅ Integration with Zabbix verified (documentation + test)
6. ✅ Test coverage maintained at 85%+ 
7. ✅ Documentation updated for:
   - Monitoring setup with Zabbix
   - Rate limiting configuration
   - Debugging with request IDs
   - New configuration options

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| OpenTelemetry version incompatibility | Medium | Low | Pin specific versions, test thoroughly |
| Performance overhead from metrics collection | Low | Low | Benchmark before/after, optimize if needed |
| Breaking changes to existing logging format | Low | Medium | Maintain backward compatibility, document changes |
| Zabbix integration complexity | Medium | Medium | Provide clear documentation and example configs |

---

## Next Steps

1. Create detailed implementation tasks
2. Set up development environment with new dependencies
3. Implement features in order of priority
4. Update documentation incrementally
5. Verify Zabbix integration with test deployment
