# Improvement Roadmap — OpenWebUI Proxy Server

**Created**: 2026-05-10  
**Based on**: [Code Review — 2026-05-10](../reviews/code-review-2026-05-10.md)  
**Pylint baseline**: 7.68/10  
**Target pylint**: ≥ 9.0/10

---

## Overview

This roadmap addresses findings from the full codebase review, prioritised by severity and impact. The plan is organised into **4 phases** designed to minimise rebase conflicts: each phase fixes bugs first, then handles structural changes, and ends with quality-of-life improvements.

| Phase | Focus | Issues Addressed | Effort | Risk |
|:------|:------|:-----------------|:-------|:-----|
| **P1 — Critical Fix** | Deployment-breaking bug | #1 | ~30 min | None (pure fix) |
| **P2 — High Priority** | Logic errors & safety | #2, #3 | ~2 h | Low |
| **P3 — Code Health** | Deduplication & cleanup | #4, #5, #6, #10, #11 | ~3 h | Low |
| **P4 — Polish** | Performance, security, tests | #7, #8, #9, security notes | ~5 h | Medium (refactors) |

Every phase is self-contained and can be merged independently. Phases should be applied **in order** (P1 → P2 → P3 → P4).

---

## Phase 1 — Critical Fix (must ship immediately)

> **Goal**: Fix the Docker container crash-on-startup so any deployment can actually run.

### 1.1 Fix gunicorn entry point **[CRITICAL]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#1 — Dockerfile references `app.main:app` but `app.main` has no module-level `app`](#) |
| **Impact** | Container crashes with `AttributeError` on startup — **zero deployments work** |
| **Root cause** | `app/main.py` only defines `create_app()` and `main()`; the old root `main.py` has `app` but the Dockerfile points at the refactored package |
| **Fix** | Add a `wsgi.py` entry point and update the Dockerfile |

**Files to change**:

1. **Create** `docker/wsgi.py`:
```python
"""WSGI entry point for gunicorn."""
from app.main import create_app

app = create_app()
```

2. **Update** `docker/Dockerfile` — add `COPY docker/wsgi.py .` after the app source COPY, and change the CMD:
```dockerfile
COPY docker/wsgi.py .

CMD ["gunicorn", "-w", "4", "-k", "gevent", "--timeout", "300", "--bind", "0.0.0.0:5001", "wsgi:app"]
```

**Effort**: ~30 min (create file, edit Dockerfile, verify with `docker build`)  
**Verification**: `docker build -t proxy-test . && docker run --rm proxy-test` — container must start without `AttributeError`  
**Dependencies**: None

---

## Phase 2 — High-Priority Logic Fixes

> **Goal**: Eliminate the two high-severity logic errors that affect correctness and error visibility.

### 2.1 Fix `Authorization: None` sent as literal string **[HIGH]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#2 — Authorization header sent as literal `None` string when absent](#) |
| **Impact** | Wrong semantics; downstream OpenWebUI backend may reject or misinterpret `None` as a bearer token |
| **Root cause** | `headers["Authorization"] = auth_header` where `auth_header` can be `None` |

**Fix** — in `app/services/openwebui_client.py`, every method that builds headers (currently `get_models`, `chat_completions`, and any new endpoints):

```python
# Before (buggy):
headers = {
    "Authorization": auth_header,  # can be None -> "None"
    "Content-Type": "application/json",
}

# After (correct):
headers = {"Content-Type": "application/json"}
if auth_header is not None:
    headers["Authorization"] = auth_header
```

**Files to change**: `app/services/openwebui_client.py` (all methods that forward the `Authorization` header)  
**Effort**: ~30 min  
**Verification**: Unit test asserting that when `auth_header=None`, no `Authorization` key exists in the outgoing request headers  

### 2.2 Replace broad `except Exception` with targeted exception handling **[HIGH]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#3 — `except Exception` swallows programming errors and hides bugs](#) |
| **Impact** | Typos and logical errors become silent 502s instead of visible crashes; `hasattr(e, "response")` on bare `Exception` is type-unsafe |
| **Root cause** | Route handlers catch `Exception` instead of `requests.exceptions.RequestException` |

**Fix** — in all three route files (`app/routes/models.py`, `app/routes/chat.py`, `app/routes/health.py`):

```python
from requests.exceptions import RequestException, Timeout

try:
    result = ...
except Timeout:
    return jsonify({"error": "Request timed out"}), 504
except RequestException as e:
    status_code = 502
    if e.response is not None:
        try:
            status_code = e.response.status_code
        except Exception:
            pass
    return jsonify({"error": "Backend request failed"}), status_code
```

Key changes:
- Catch `Timeout` specifically → returns 504  
- Catch `RequestException` → returns 502 (with upstream status if available)  
- **Remove** the bare `except Exception` block — let programming errors propagate to Flask's error handler  
- **Remove** `hasattr(e, "response")` — no longer needed because `RequestException.response` is a documented attribute  

**Files to change**: `app/routes/models.py`, `app/routes/chat.py`, `app/routes/health.py`  
**Effort**: ~1 h  
**Verification**: All existing tests still pass; new test injecting a `NameError` should NOT be caught and should result in a 500 from Flask's handler  

---

## Phase 3 — Code Health & Deduplication

> **Goal**: Remove duplicate code, clean up unused imports, eliminate the dual-entry-point confusion, and stop leaking internal error details to clients.

### 3.1 Extract shared error handler utility **[MEDIUM]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#6 — Identical error-handling code duplicated in `models.py` and `chat.py`](#) |
| **Impact** | Maintenance burden; any change to error handling must be repeated in N places |
| **Root cause** | Copy-paste between route files |

**Fix** — create `app/utils/error_handler.py`:

```python
"""Shared proxy error handling utilities."""
from flask import jsonify
import logging
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

def handle_proxy_error(e: RequestException, endpoint_name: str = "backend"):
    """Standardised error handling for proxied requests."""
    if isinstance(e, Timeout):
        logger.warning(f"Timeout calling {endpoint_name}")
        return jsonify({"error": "Request timed out"}), 504

    status_code = 502
    if e.response is not None:
        try:
            status_code = e.response.status_code
        except Exception:
            pass

    logger.error(f"Request failed | endpoint={endpoint_name} | error={e}")
    return jsonify({"error": f"{endpoint_name} request failed"}), status_code
```

Then in route files, use:

```python
from app.utils.error_handler import handle_proxy_error

try:
    result = client.get_models(...)
except RequestException as e:
    return handle_proxy_error(e, endpoint_name="OpenWebUI models")
```

**Files to change**:  
- **Create** `app/utils/error_handler.py`  
- **Update** `app/routes/models.py`, `app/routes/chat.py`, `app/routes/health.py` to use the utility  

**Effort**: ~1 h  
**Verification**: Error response format unchanged; all existing tests pass  

### 3.2 Resolve dual entry points — deprecate root `main.py` **[MEDIUM]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#4 — Two app versions coexist: root `main.py` (monolithic) vs `app/main.py` (factory pattern)](#) |
| **Impact** | Developers may edit the wrong file; root `main.py` uses deprecated `datetime.utcnow()`; inconsistent logging configs |
| **Root cause** | Refactoring created `app/` without removing the original |

**Options**:

| Option | Description | Recommendation |
|:-------|:------------|:---------------|
| A | Delete root `main.py` entirely | **Recommended** — the `app/` package is the canonical version; Dockerfile and tests both use it |
| B | Move to `legacy/main.py.old` | Safer transition if there are unknown dependents |
| C | Add deprecation warning at top of root `main.py` | Band-aid |

**Recommended fix** (Option A):
1. Verify no imports reference root `main.py` (check `grep -r "from main import"` and `grep -r "import main"`)
2. Delete `main.py` from project root
3. If the root `main.py` `if __name__ == "__main__"` block is useful for development, add equivalent logic to `app/main.py`:

```python
if __name__ == "__main__":
    app = create_app()
    app.run(host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", 5001)),
            debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
```

**Files to change**: Delete `main.py`; update `app/main.py` with dev runner if needed  
**Effort**: ~30 min  
**Verification**: All tests pass; `python -m app.main` starts the dev server  

### 3.3 Remove unused imports **[LOW]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#10 — Unused imports in two files](#) |
| **Pylint** | W0611 |
| **Effort** | ~5 min |

**Files to change**:
- `app/routes/models.py:4` — remove `import datetime`  
- `app/utils/logging_config.py:6` — remove `Optional` from `typing` import  

### 3.4 Fix `no-else-return` in health check **[LOW]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#11 — Unnecessary `else` after `return` in `app/routes/health.py:51`](#) |
| **Pylint** | R1705 |
| **Effort** | ~5 min |

Remove the `else` keyword and de-indent the block (cosmetic only, no behaviour change).

### 3.5 Sanitise error messages — don't leak `str(e)` to clients **[MEDIUM]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#5 — Error responses leak internal exception details (hostnames, IPs, tracebacks)](#) |
| **Impact** | Information disclosure to potential attackers |
| **Fix** | This is automatically resolved by Phase 3.1 — the shared `handle_proxy_error` already logs the detail server-side and returns a generic message to the client |

No additional work needed after 3.1 is implemented.

---

## Phase 4 — Polish & Hardening

> **Goal**: Performance improvements, security hardening, test quality, and pylint score improvement.

### 4.1 Add `requests.Session` for connection reuse **[LOW-PERF]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#7 — `OpenWebUIClient` instantiated per-request with no connection pooling](#) |
| **Impact** | Marginal performance loss under load (no connection reuse, fresh TCP per request) |
| **Note** | Only address if profiling shows a bottleneck |

**Fix**: Add a `requests.Session` to `OpenWebUIClient.__init__` and use `self.session.get/post/…` instead of `requests.get/post/…`:

```python
import requests

class OpenWebUIClient:
    def __init__(self, ...):
        self.session = requests.Session()
        self.session.verify = verify_ssl
        # Optionally configure connection pooling:
        # adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20)
        # self.session.mount("https://", adapter)
```

Close the session in a `close()` method or `__del__`.

**Effort**: ~1 h  
**Verification**: Existing tests pass; new test verifies that multiple calls reuse the same session  

### 4.2 Reduce `OpenWebUIClient.__init__` parameter count **[LOW]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#8 — 6 parameters exceeds recommended limit of 5](#) |
| **Pylint** | R0913 / R0917 |

**Fix** — use keyword-only arguments (Python 3.8+):

```python
def __init__(
    self,
    base_url: str,
    *,
    verify_ssl: bool = True,
    request_timeout: int = 30,
    chat_completion_timeout: int = 120,
    readiness_timeout: int = 5,
):
```

This is the simplest fix and preserves the API. If timeout parameters grow further, introduce a `@dataclass`:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ClientTimeouts:
    request: int = 30
    chat_completion: int = 120
    readiness: int = 5
```

**Effort**: ~30 min  

### 4.3 Fix f-string logging (lazy evaluation) **[LOW]**

| Field | Detail |
|:------|:-------|
| **Issue** | [#9 — f-strings in logging calls eagerly evaluate](#) |
| **Pylint** | W1203 (10 occurrences) |

**Fix** — replace all `logger.info(f"...")` with `logger.info("... %s ...", var)`:

```python
# Before:
logger.info(f"Request received | endpoint={endpoint}")

# After:
logger.info("Request received | endpoint=%s", endpoint)
```

**Files to change**: `app/main.py`, `app/routes/*.py`, `app/services/*.py`, `app/utils/*.py`  
**Effort**: ~30 min (search-and-replace across ~10 occurrences)  

### 4.4 Security hardening **[MEDIUM]**

The review flagged several security concerns. These are below the critical bug-fix line but important for production readiness.

| # | Item | Priority | Effort | Description |
|:--|:-----|:---------|:-------|:------------|
| 4.4a | Rate limiting | Medium | ~1 h | Add Flask-Limiter with configurable per-endpoint limits |
| 4.4b | Input validation | Low | ~1 h | Whitelist or sanitise forwarded fields (especially `model` name before forwarding) |
| 4.4c | Proxy authentication | Low | ~2 h | If the proxy should not be open to anyone with network access, add API-key or mTLS auth |

**4.4a — Rate limiting** (recommended for immediate):
```python
# In app/main.py or app/__init__.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])
limiter.init_app(app)
```

Add `requirements.txt` entry: `Flask-Limiter>=3.5.0`.

**4.4b — Input validation**:
```python
# In app/routes/chat.py, before forwarding
model = request.json.get("model", "")
if model and not re.match(r'^[a-zA-Z0-9_\-.:/]+$', model):
    return jsonify({"error": "Invalid model name"}), 400
```

**4.4c — Proxy authentication** (removed from scope):

The proxy uses a **transparent pass-through** model — `Authorization: Bearer <token>` is forwarded as-is to OpenWebUI, which handles all authentication. The proxy itself does not validate or inspect tokens. This is the intended design. If proxy-level authentication is ever needed (e.g., to protect the proxy from unauthorised network access), the simplest approach is **network-level security** (firewall rules, VPC, or mTLS) rather than adding application-layer auth to the proxy. If application-layer auth must be added later, it can be done by checking `PROXY_API_KEY` against incoming `Authorization` headers — but this is deliberately omitted from the current roadmap.

### 4.5 Test improvements **[MEDIUM]**

| Field | Detail |
|:------|:-------|
| **Issue** | Review flagged that route tests accept any of `[200, 502, 504]` — too permissive |
| **Impact** | Tests can pass even when behaviour is wrong |

**Recommended actions**:

1. Add `responses` or `httpretty` as a dev dependency for deterministic HTTP mocking  
2. Rewrite route tests to mock `OpenWebUIClient` (or `requests`) so tests don't depend on a running backend  
3. Add assertion for exact status codes when the mock is configured for success/failure/timeout  
4. Add tests for the new error cases introduced in Phase 2: `None` auth header, `Timeout` → 504, `RequestException` → 502  
5. Add a test verifying that unexpected exceptions (e.g., `NameError`) propagate as 500s (not swallowed)

**Effort**: ~2 h  

---

## Summary — Prioritised Task List

| Seq | Phase | Task | Priority | Effort | Pylint impact |
|:----|:------|:-----|:---------|:-------|:--------------|
| 1 | P1 | Create `docker/wsgi.py` + update Dockerfile | **Critical** | 30 min | — |
| 2 | P2 | Fix `Authorization: None` header bug (all client methods) | **High** | 30 min | — |
| 3 | P2 | Replace `except Exception` → `except RequestException` + `Timeout` in all route files | **High** | 1 h | Removes W0718 (3×), E1101 (4×) |
| 4 | P3 | Extract shared `handle_proxy_error()` into `app/utils/error_handler.py` | **Medium** | 1 h | Addresses R0801 |
| 5 | P3 | Delete root `main.py` (dual entry point) | **Medium** | 30 min | — |
| 6 | P3 | Remove unused imports (2 files) | **Low** | 5 min | Removes W0611 (2×) |
| 7 | P3 | Fix `no-else-return` in `health.py` | **Low** | 5 min | Removes R1705 |
| 8 | P4 | Add `requests.Session` to `OpenWebUIClient` | **Low** | 1 h | — |
| 9 | P4 | Keyword-only args for `OpenWebUIClient.__init__` | **Low** | 30 min | Removes R0913/R0917 |
| 10 | P4 | Fix f-string logging (10 occurrences → `%` format) | **Low** | 30 min | Removes W1203 (10×) |
| 11 | P4 | Add rate limiting (Flask-Limiter) | **Medium** | 1 h | — |
| 12 | P4 | Add input validation on forwarded fields | **Low** | 1 h | — |
| 13 | P4 | Improve tests (deterministic mocking, exact status codes) | **Medium** | 2 h | — |

**Total estimated effort**: ~10 hours (all phases)  
**Minimum viable**: ~2.5 hours (P1 + P2)  
**Recommended target**: ~6 hours (P1 + P2 + P3)  

---

## Pylint Score Projection

| Phase | Fixes | Removes | Est. score |
|:------|:------|:--------|:-----------|
| Baseline | — | — | 7.68 |
| P1 | Docker fix (no pylint impact) | — | 7.68 |
| P2 | W0718 ×3, E1101 ×4 | 7 warnings | ~8.20 |
| P3 | W0611 ×2, R0801, R1705 | 4 warnings | ~8.60 |
| P4 | W1203 ×10, R0913, C0301 ×2 | 13 warnings | ≥ 9.0 |

**Target**: ≥ 9.0/10 after Phase 4.

---

## Review Questions — Resolved Answers

| # | Question | Answer |
|:--|:---------|:-------|
| 1 | Should root `main.py` be kept? | **No.** Delete it. The `app/` package is canonical and all tooling (Docker, tests) points at it. |
| 2 | How does auth work with OpenAI-client Bearer tokens for OpenWebUI? | **Transparent pass-through.** The proxy reads `request.headers.get("Authorization")` and forwards it as-is to OpenWebUI via `OpenWebUIClient`. OpenWebUI itself authenticates the token. The proxy never inspects or transforms it. This is intentionally simple and keeps OpenWebUI as the single source of truth for auth. When the incoming request lacks an `Authorization` header entirely, the header should be **omitted** from the outbound request (see Phase 2.1 — the current `None` → `"None"` bug). |
| 3 | Plans for structured test mocking? | **Yes — Phase 4.5.** Add `responses` or `pytest-httpx` and rewrite route tests without depending on a live backend. |

---

## Appendix: Files Affected by Each Phase

| Phase | Files Created | Files Modified | Files Deleted |
|:------|:--------------|:---------------|:--------------|
| P1 | `docker/wsgi.py` | `docker/Dockerfile` | — |
| P2 | — | `app/services/openwebui_client.py`, `app/routes/models.py`, `app/routes/chat.py`, `app/routes/health.py` | — |
| P3 | `app/utils/error_handler.py` | `app/routes/models.py`, `app/routes/chat.py`, `app/routes/health.py`, `app/utils/logging_config.py`, `app/main.py` (dev runner) | `main.py` |
| P4 | — | `app/services/openwebui_client.py`, `app/routes/chat.py`, `app/__init__.py` or `app/main.py`, `requirements.txt`, test files | — |
