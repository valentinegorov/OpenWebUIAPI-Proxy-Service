# Architecture Plan: OpenAI API Responses Endpoint

## Overview
This document outlines the architecture for implementing the OpenAI API `/v1/responses` endpoint in the project. The Responses API is a newer OpenAI API that provides a simplified interface for generating AI responses, distinct from the traditional Chat Completions API.

## 1. Endpoint Specification

### Primary Endpoint
- **Path**: `/v1/responses`
- **Method**: `POST`
- **Content-Type**: `application/json`

### Optional Endpoint for Retrieving Responses
- **Path**: `/v1/responses/{response_id}`
- **Method**: `GET`

### Optional Endpoint for Deleting Responses
- **Path**: `/v1/responses/{response_id}`
- **Method**: `DELETE`

## 2. Request/Response Format

### Request Body (POST /v1/responses)
```json
{
  "model": "string",
  "input": "string | array",
  "temperature": "number (optional)",
  "max_output_tokens": "integer (optional)",
  "top_p": "number (optional)",
  "stream": "boolean (optional)",
  "metadata": "object (optional)",
  "tools": "array (optional)",
  "tool_choice": "string | object (optional)"
}
```

### Response Body (Success)
```json
{
  "id": "resp_abc123",
  "object": "response",
  "created_at": 1234567890,
  "status": "completed",
  "model": "model-name",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "Response text here"
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 10,
    "output_tokens": 20,
    "total_tokens": 30
  },
  "metadata": {}
}
```

### Streaming Response Format
For streaming requests (`stream: true`), the response will be Server-Sent Events (SSE):
```
data: {"type": "response.created", "response": {...}}

data: {"type": "response.output_item.added", "item": {...}}

data: {"type": "response.content_part.added", "part": {...}}

data: {"type": "response.output_text.delta", "delta": "text chunk"}

data: {"type": "response.completed", "response": {...}}

data: [DONE]
```

## 3. Architecture Components

### 3.1 Route Handler (`app/routes/responses.py`)
- **Responsibility**: Handle HTTP requests and responses for the `/v1/responses` endpoint
- **Features**:
  - Request validation using Pydantic models
  - Authentication/authorization checks
  - Stream vs non-stream request routing
  - Error handling and appropriate HTTP status codes

### 3.2 Request/Response Models (`app/schemas/responses.py`)
- **Responsibility**: Define Pydantic models for request/response validation
- **Models to Create**:
  - `ResponsesRequest`: Input validation for POST requests
  - `ResponsesResponse`: Output format for successful responses
  - `ResponsesStreamEvent`: Union type for streaming events
  - `ResponseObject`: Internal representation of a response object
  - `ResponseUsage`: Token usage tracking

### 3.3 Service Layer (`app/services/responses_service.py`)
- **Responsibility**: Business logic for processing responses
- **Features**:
  - Transform OpenAI Responses API format to OpenWebUI API format
  - Call OpenWebUI backend API
  - Transform OpenWebUI response back to OpenAI Responses format
  - Handle streaming responses with SSE
  - Manage response lifecycle (create, retrieve, delete)

### 3.4 OpenWebUI Adapter (`app/adapters/openwebui_responses_adapter.py`)
- **Responsibility**: Map between OpenAI Responses API and OpenWebUI API
- **Features**:
  - Convert `input` field to OpenWebUI message format
  - Map tool definitions between formats
  - Handle output format transformations
  - Manage conversation state if needed

## 4. Implementation Flow

### Non-Streaming Request Flow
```
Client Request 
  → Route Handler (/v1/responses)
  → Request Validation (Pydantic)
  → Responses Service
  → OpenWebUI Adapter (transform request)
  → OpenWebUI Backend API Call
  → OpenWebUI Adapter (transform response)
  → Responses Service
  → Route Handler
  → Client Response
```

### Streaming Request Flow
```
Client Request (stream=true)
  → Route Handler (/v1/responses)
  → Request Validation (Pydantic)
  → Responses Service
  → OpenWebUI Adapter (transform request)
  → OpenWebUI Backend API Call (streaming)
  → Event Stream Processing
    → Transform each event to OpenAI format
    → Yield SSE formatted events
  → Client receives stream of events
```

## 5. File Structure

```
app/
├── routes/
│   └── responses.py              # New: Route handlers for /v1/responses
├── schemas/
│   └── responses.py              # New: Pydantic models for responses API
├── services/
│   └── responses_service.py      # New: Business logic for responses
├── adapters/
│   └── openwebui_responses_adapter.py  # New: OpenWebUI API adapter
└── main.py                       # Modify: Register new routes
```

## 6. Integration Points

### 6.1 Existing Components to Reuse
- **Authentication**: Reuse existing auth middleware from chat completions
- **HTTP Client**: Reuse existing async HTTP client for OpenWebUI calls
- **Error Handling**: Reuse existing error handling patterns
- **Logging**: Reuse existing logging configuration
- **Configuration**: Reuse existing config management for API endpoints

### 6.2 OpenWebUI API Mapping
The Responses API needs to map to OpenWebUI's existing endpoints:
- **Primary Mapping**: Use OpenWebUI's chat/completions endpoint internally
- **Alternative**: If OpenWebUI adds native Responses API support, adapt accordingly

**Mapping Strategy**:
- `input` (string) → Convert to messages array with single user message
- `input` (array) → Convert to messages array directly
- `output` → Extract from OpenWebUI's choices[0].message.content
- `tools` → Map to OpenWebUI's tools parameter
- `stream` → Enable streaming mode in OpenWebUI call

## 7. Error Handling

### Error Response Format
```json
{
  "error": {
    "message": "Error description",
    "type": "invalid_request_error",
    "param": "field_name",
    "code": "invalid_param"
  }
}
```

### Common Error Cases
- Invalid model name → 400 Bad Request
- Missing required fields → 400 Bad Request
- Authentication failure → 401 Unauthorized
- Rate limit exceeded → 429 Too Many Requests
- OpenWebUI backend error → 502 Bad Gateway
- Server error → 500 Internal Server Error

## 8. Testing Strategy

### Unit Tests
- Test request/response model validation
- Test service layer transformations
- Test adapter mappings
- Test error handling scenarios

### Integration Tests
- Test full request/response cycle
- Test streaming functionality
- Test with various input types
- Test tool integration

### End-to-End Tests
- Test with real OpenAI SDK clients
- Verify compatibility with OpenAI Responses API examples
- Test edge cases and error conditions

## 9. Performance Considerations

### Caching
- Consider caching response objects for GET /v1/responses/{id}
- Implement TTL for stored responses

### Streaming Optimization
- Use async generators for efficient streaming
- Minimize transformation overhead in stream path
- Buffer management for SSE events

### Rate Limiting
- Implement rate limiting consistent with existing endpoints
- Consider separate limits for Responses API

## 10. Security Considerations

### Input Validation
- Strict validation of all input fields
- Sanitize user input before forwarding to OpenWebUI
- Validate model names against allowed list

### Authentication
- Require valid API key for all requests
- Support multiple authentication methods if needed

### Data Privacy
- Don't log sensitive request/response content
- Implement data retention policies for stored responses

## 11. Documentation Requirements

### API Documentation
- Update OpenAPI/Swagger specs
- Add endpoint documentation to README
- Create usage examples

### Developer Documentation
- Document internal architecture decisions
- Create contribution guidelines for responses feature
- Document testing procedures

## 12. Rollout Plan

### Phase 1: Core Implementation
- Implement basic POST /v1/responses endpoint
- Support non-streaming requests
- Basic request/response transformation
- Unit tests for core functionality

### Phase 2: Streaming Support
- Implement streaming response handling
- Add SSE event formatting
- Test streaming with various scenarios

### Phase 3: Additional Features
- Implement GET /v1/responses/{id}
- Implement DELETE /v1/responses/{id}
- Add tool support
- Add metadata support

### Phase 4: Production Readiness
- Comprehensive testing
- Performance optimization
- Documentation completion
- Monitoring and alerting setup

## 13. Monitoring & Observability

### Metrics to Track
- Request latency (p50, p95, p99)
- Error rates by error type
- Streaming vs non-streaming request counts
- Token usage statistics
- OpenWebUI backend response times

### Logging
- Log request IDs for tracing
- Log errors with full context
- Avoid logging sensitive content
- Structured logging for easy parsing

### Alerting
- Alert on high error rates
- Alert on latency spikes
- Alert on OpenWebUI backend failures

## 14. Future Enhancements

### Potential Features
- Response editing/modification
- Multi-turn conversation support
- Advanced tool integration
- Custom response formats
- Webhook notifications for completed responses

### OpenWebUI Integration
- Monitor OpenWebUI for native Responses API support
- Adapt implementation if OpenWebUI adds native support
- Contribute back to OpenWebUI if applicable

---

## Appendix A: OpenAI Responses API Reference Links
- [OpenAI Responses API Documentation](https://platform.openai.com/docs/api-reference/responses)
- [Responses API Guide](https://platform.openai.com/docs/guides/responses)

## Appendix B: Example Requests/Responses
See OpenAI official documentation for comprehensive examples.
