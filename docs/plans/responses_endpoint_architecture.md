# OpenWebUI Responses API Proxy – Updated Architecture Plan

## 1. Introduction

This document describes the architecture and implementation plan for a proxy service that exposes the **OpenAI Responses API** (`/v1/responses`) by forwarding requests to the **native Open Responses API** provided by OpenWebUI (available experimentally since v0.8.0, stabilized in v0.8.11+). The proxy adds authentication, rate limiting, observability, and optional caching while delegating the core response generation logic to OpenWebUI.

## 2. Current Status & Assumptions

- OpenWebUI implements an **Open Responses** endpoint (e.g., `/api/responses`) that closely follows the OpenAI Responses API specification.
- This endpoint supports:
  - Streaming and non‑streaming responses
  - Tool calls (functions, web search, file search)
  - Reasoning tokens and `reasoning_effort`
  - Conversation state via `previous_response_id`
  - Response storage and retrieval by ID (GET / DELETE)
- The proxy will act as a lightweight pass‑through, only transforming fields where OpenWebUI’s schema differs from OpenAI’s official specification.
- All authentication, RBAC, and rate limiting are inherited from the existing OpenWebUI proxy configuration.

## 3. High-Level Architecture

```
Client (OpenAI SDK)
       │
       ▼
Proxy Service (FastAPI)
├── Routes: /v1/responses
├── Middleware: Auth, Rate Limit, Logging, Idempotency
├── Service Layer: Request validation, response streaming, error mapping
├── Adapter: Minimal field mapping (OpenAI ↔ OpenWebUI)
└── HTTP Client: Async calls to OpenWebUI backend
       │
       ▼
OpenWebUI (native /api/responses endpoint)
```

## 4. Endpoints Implemented

| Method | Path                   | Description                                                                 |
|--------|------------------------|-----------------------------------------------------------------------------|
| POST   | `/v1/responses`        | Create a new response (streaming or non‑streaming).                         |
| GET    | `/v1/responses/{id}`   | Retrieve a previously stored response (if supported by OpenWebUI).         |
| DELETE | `/v1/responses/{id}`   | Delete a stored response (if supported).                                   |
| GET    | `/v1/responses`        | List responses (optional, may be omitted if not natively supported).       |

> **Note:** GET and DELETE endpoints rely on OpenWebUI’s ability to persist responses. If OpenWebUI does not support this, the proxy will return `501 Not Implemented` for those methods. A future enhancement could add an external store (Redis/PostgreSQL).

## 5. Request/Response Schemas

The proxy will use Pydantic models that mirror the **OpenAI Responses API** specification. Most fields will be passed through unchanged; the adapter will only modify fields where OpenWebUI uses a different name or type.

### 5.1 Supported Request Fields (OpenAI → OpenWebUI)

| OpenAI Field                | OpenWebUI Equivalent       | Transformation                                             |
|-----------------------------|----------------------------|------------------------------------------------------------|
| `model`                     | `model`                    | Pass‑through                                               |
| `input`                     | `input`                    | Pass‑through (supports string, list of messages, etc.)    |
| `instructions`              | `instructions`             | Pass‑through                                               |
| `temperature`               | `temperature`              | Pass‑through                                               |
| `max_output_tokens`         | `max_tokens`               | Rename field                                               |
| `top_p`                     | `top_p`                    | Pass‑through                                               |
| `stop`                      | `stop`                     | Pass‑through                                               |
| `stream`                    | `stream`                   | Pass‑through                                               |
| `tools`                     | `tools`                    | Pass‑through (OpenWebUI supports function, web_search, file_search) |
| `tool_choice`               | `tool_choice`              | Pass‑through                                               |
| `parallel_tool_calls`       | `parallel_tool_calls`      | Pass‑through                                               |
| `previous_response_id`      | `conversation_id` or `session_id` | Map to OpenWebUI’s conversation identifier (usually a `session_id`). The proxy stores the mapping in a local cache. |
| `store` (boolean)           | `store`                    | Pass‑through; if `true`, OpenWebUI must persist the response. |
| `metadata`                  | `metadata`                 | Pass‑through (stored alongside the response if OpenWebUI supports it). |
| `reasoning_effort`          | `reasoning_effort`         | Pass‑through (OpenWebUI must support reasoning models).   |
| `user`                      | `user`                     | Pass‑through (used for rate limiting / logging).          |

### 5.2 Response Fields (OpenWebUI → OpenAI)

The adapter will map OpenWebUI’s response JSON to the official OpenAI format:

| OpenWebUI Field            | OpenAI Field                | Notes                                             |
|----------------------------|-----------------------------|---------------------------------------------------|
| `id`                       | `id`                        | Response ID                                       |
| `object` (e.g., "response")| `object`                    | Fixed to `"response"`                             |
| `created_at`               | `created_at`                | Unix timestamp                                    |
| `model`                    | `model`                     | Pass‑through                                      |
| `status`                   | `status`                    | e.g., `"completed"`, `"in_progress"`             |
| `output`                   | `output`                    | List of output items (messages, tool calls)      |
| `usage`                    | `usage`                     | Token usage (prompt_tokens, completion_tokens, total_tokens) |
| `metadata`                 | `metadata`                  | Pass‑through                                      |
| `error`                    | `error`                     | Pass‑through (if any)                             |

## 6. Streaming Events

OpenWebUI’s native Responses API emits SSE events that are **already compatible** with the OpenAI specification (or very close). The proxy will forward these events almost unchanged, only performing necessary field renames (e.g., `response.output_text.delta` → `response.output_text.delta` – same). The event types supported:

- `response.created`
- `response.in_progress`
- `response.completed`
- `response.output_item.added`
- `response.output_item.done`
- `response.content_part.added`
- `response.content_part.done`
- `response.output_text.delta`
- `response.reasoning_text.delta`
- `response.function_call_arguments.delta`

If OpenWebUI emits a non‑standard event, the proxy may either drop it or map it to the closest OpenAI event.

## 7. Conversation State Management

OpenAI’s `previous_response_id` allows a client to continue a multi‑turn conversation. OpenWebUI’s native Responses API expects a `conversation_id` or `session_id`.

The proxy will:

1. Maintain a **short‑lived cache** (Redis or in‑memory) that maps OpenAI `previous_response_id` → OpenWebUI `conversation_id`.
2. When a request contains `previous_response_id`, the proxy looks up the mapped `conversation_id` and injects it into the forwarded request.
3. When a response is created, the proxy stores the reverse mapping (`conversation_id` → new `response_id`) to allow subsequent requests to reference it.
4. The mapping TTL is configurable (default 1 hour). After TTL expiry, the proxy returns a `404 Not Found` for that `response_id`.

If OpenWebUI already stores the conversation ID in its own response object (e.g., returns `conversation_id`), the proxy can use that directly without an extra cache.

## 8. Error Handling

The proxy translates OpenWebUI error responses into OpenAI‑compatible error objects.

| OpenWebUI HTTP Status | OpenWebUI Error Type           | Proxy Output (OpenAI format)                            |
|-----------------------|--------------------------------|----------------------------------------------------------|
| 400                   | `invalid_request_error`        | `{ "error": { "type": "invalid_request_error", "message": ... } }` |
| 401                   | `authentication_error`         | `{ "error": { "type": "authentication_error", "message": "Invalid API key" } }` |
| 429                   | `rate_limit_error`             | `{ "error": { "type": "rate_limit_error", "message": "Rate limit exceeded" } }` |
| 500                   | `api_error`                    | `{ "error": { "type": "api_error", "message": "OpenWebUI internal error" } }` |

The proxy also adds its own errors for validation failures (Pydantic) or when OpenWebUI is unreachable (`503 Service Unavailable`).

## 9. Caching and Idempotency

### 9.1 Idempotency Keys

The proxy will support the `Idempotency-Key` header as per OpenAI’s specification:

- Use an in‑memory or Redis store to map `Idempotency-Key` → `response_id` for 24 hours.
- If the same key is received within TTL, return the stored response (cached) without calling OpenWebUI again.

### 9.2 Response Caching (Optional)

For non‑streaming identical requests (same `input`, `model`, `temperature`, etc.) the proxy may cache responses for a short period (e.g., 5 minutes) to reduce load. This is disabled by default and configurable.

## 10. Authentication & Rate Limiting

- The proxy reuses the existing OpenWebUI authentication mechanism (API key validation via middleware).
- Rate limits are enforced at the proxy level, separate from OpenWebUI’s limits:
  - Configurable per `user` / API key.
  - Default: 500 requests per minute, 10,000 tokens per minute.
  - Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

## 11. Logging & Observability

### 11.1 Logging

- Structured JSON logs (using `structlog`).
- Log only metadata: `method`, `path`, `status_code`, `response_id`, `duration_ms`, `input_tokens`, `output_tokens`, `stream`, `user`.
- **Never log** the full request/response body, API keys, or user messages in production.
- For debugging, an optional `X-Debug-Request-Id` header enables full payload logging for that request only.

### 11.2 Metrics (Prometheus)

| Metric Name                             | Type      | Labels                          |
|-----------------------------------------|-----------|---------------------------------|
| `responses_requests_total`              | Counter   | `method`, `endpoint`, `status`  |
| `responses_request_duration_seconds`    | Histogram | `method`, `endpoint`            |
| `responses_streaming_connections`       | Gauge     | –                               |
| `responses_cache_hits_total`            | Counter   | `cache_type` (idempotency/response) |
| `responses_openwebui_errors_total`      | Counter   | `error_type`                    |

## 12. Implementation Phases

### Phase 1: Core Proxy (Week 1–2)

- Implement POST `/v1/responses` with pass‑through to OpenWebUI’s `/api/responses`.
- Support both streaming and non‑streaming.
- Basic field mapping (`max_tokens` rename).
- Idempotency key support (in‑memory).
- Error translation middleware.
- Unit & integration tests.

### Phase 2: Conversation State (Week 3)

- Add `previous_response_id` ↔ `conversation_id` mapping with Redis/in‑memory store.
- Handle `store: true` (rely on OpenWebUI persistence).
- Implement GET `/v1/responses/{id}` if OpenWebUI supports retrieval (otherwise return `501`).
- Add DELETE endpoint if supported.

### Phase 3: Observability & Production Readiness (Week 4)

- Prometheus metrics.
- Structured logging.
- Configurable rate limiting (token bucket / sliding window).
- Health check endpoint (`/health/responses`).
- OpenAPI (Swagger) documentation.

### Phase 4: Advanced Features (optional, Week 5+)

- Full response caching (Redis).
- Support for file uploads (OpenWebUI’s file API).
- Detailed metrics per tool call.
- Chaos testing & performance benchmarks.

## 13. Testing Strategy

| Test Type          | Scope                                                                 |
|--------------------|-----------------------------------------------------------------------|
| Unit tests         | Field mapping, idempotency cache, error translation, validation.     |
| Integration tests  | Proxy ↔ OpenWebUI (mock or real instance), streaming event fidelity. |
| Contract tests     | Verify that the proxy’s responses match OpenAI’s official spec using `pact-python` or similar. |
| End‑to‑end tests   | Run a real OpenAI SDK client against the proxy and compare outputs with direct OpenWebUI calls. |
| Performance tests  | Load test with 100 concurrent streaming requests; measure TTFT and throughput. |

## 14. Risks & Mitigations

| Risk                                                                 | Mitigation                                                                                  |
|----------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| OpenWebUI’s native Responses API is unstable or incomplete.         | Phase 0: Validate OpenWebUI’s endpoint (v0.8.11+) with a small POC before full development. |
| GET/DELETE endpoints not implemented in OpenWebUI.                  | Return `501 Not Implemented` for those endpoints; store externally if needed.              |
| Streaming event types differ from OpenAI spec.                      | Implement a mapping layer; drop unknown events with warning logs.                          |
| `previous_response_id` mapping cache becomes inconsistent.          | Store mapping in Redis with TTL; handle missing keys gracefully (`404`).                   |
| High latency due to caching layer.                                   | Use local in‑memory cache (e.g., `aiocache`) for idempotency keys; Redis only for conversation mapping. |

## 15. Success Criteria

- The proxy passes the OpenAI Responses API compatibility test suite (to be defined).
- Streaming responses emit correctly formatted SSE events.
- Idempotency keys prevent duplicate processing.
- Metrics and logs provide clear visibility into errors and performance.
- A client using the official OpenAI Python SDK can send requests through the proxy without code changes.

---

*Version 2.0 – Updated to leverage OpenWebUI’s native Open Responses API (requires OpenWebUI ≥0.8.11)*
