# Roadmap

## Phase 1: Foundation (Completed ✅)
- [x] Core Flask application setup
- [x] OpenWebUI HTTP client service
- [x] Basic route implementation (`/v1/models`, `/v1/chat/completions`)
- [x] Health and readiness endpoints
- [x] CORS middleware configuration
- [x] Environment-based configuration
- [x] Docker deployment setup
- [x] Basic test suite

## Phase 2: Stability & Observability (In Progress 🔄)
- [ ] Enhanced error handling and retry logic
- [ ] Structured logging improvements with request ID tracking
- [ ] Request/response logging for debugging
- [ ] Integration test coverage expansion
- [ ] OpenTelemetry metrics with Zabbix Prometheus exporter integration
- [ ] Documentation improvements

### Timeline: Q1 2025
### Priority: High

## Phase 3: Performance & Scalability (Planned 📋)
- [ ] Streaming response optimization
- [ ] Connection pooling for backend requests
- [ ] Caching layer for model listings
- [ ] Async request handling improvements
- [ ] Load testing and performance tuning
- [ ] CI/CD pipeline setup

### Timeline: Q2 2025
### Priority: Medium

## Phase 4: Advanced Features (Planned 📋)
- [ ] Simple fixed window rate limiting for local deployments (Decision locked - see CONTEXT.md)
- [ ] Optional authentication middleware
- [ ] Request transformation plugins
- [ ] Response filtering capabilities
- [ ] Multi-backend support

### Timeline: Q3 2025
### Priority: Low

## Phase 5: Production Readiness (Planned 📋)
- [ ] Distributed tracing integration
- [ ] Kubernetes deployment manifests
- [ ] Helm chart creation
- [ ] Comprehensive monitoring dashboards for Zabbix

### Timeline: Q4 2025
### Priority: Medium

---

## Current Sprint Focus
**Sprint**: Phase 2 - Stability & Observability
**Goal**: Complete observability enhancements and documentation improvements

### Sprint Tasks
1. Implement request ID tracking across logs
2. Add detailed error response formatting with request ID
3. Maintain integration test coverage at 85%+ (currently 93% ✅)
4. Improve documentation for advanced features
5. Implement OpenTelemetry metrics with Zabbix-compatible Prometheus export
6. Document fixed-window rate limiter configuration for local network use
7. Add retry logic with exponential backoff for backend calls
