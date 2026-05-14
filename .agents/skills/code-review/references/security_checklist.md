# Security Review Checklist

Use this checklist during step 3 (manual review) of the code-review workflow.
Focus on the categories relevant to the language and context of the code under
review. Not every item applies to every review.

---

## 1. Injection Risks

- [ ] **SQL Injection**: Are queries built via string concatenation/interpolation?
  - Prefer parameterised queries / prepared statements.
  - For dynamic table/column/group-by names, use a whitelist map — never inject raw user input.
- [ ] **OS Command Injection**: Is user input passed to `exec`, `system`, `popen`, `subprocess`, or backticks?
  - Use `execFile`/`spawn` (Node), `subprocess.run` with `shell=False` (Python), or equivalent.
  - If shell is unavoidable, escape with the language's built-in escaping function — never hand-roll.
- [ ] **XSS (Cross-Site Scripting)**: Is user-supplied data rendered in HTML without escaping?
  - Use context-aware escaping (HTML entity, attribute, JS, CSS, URL).
  - Prefer framework auto-escaping (React JSX, Vue `{{ }}`, etc.).
- [ ] **LDAP / XPath / Template Injection**: Are external values injected into query languages or templates?
- [ ] **Log Injection**: Could user input containing newlines forge log entries?

## 2. Authentication & Authorisation

- [ ] Are auth checks performed on *every* protected endpoint/function (not just the UI)?
- [ ] Is there any route or branch that skips the auth middleware?
- [ ] Are API keys, JWTs, or session tokens validated correctly (signature, expiry, issuer)?
- [ ] Are authorisation decisions consistent? (e.g., can a user access another user's data by changing an ID?)
- [ ] Is there a confused-deputy risk? (a privileged component acting on behalf of an unprivileged caller)

## 3. Secrets & Sensitive Data

- [ ] **Hardcoded secrets**: API keys, passwords, tokens, private keys in source code.
- [ ] **Secrets in logs**: Are credentials or PII being logged at any level?
- [ ] **Secrets in error messages**: Do error responses leak stack traces, DB schemas, or internal paths?
- [ ] **Environment exposure**: Are `.env` files or config files with secrets committed?
- [ ] **Encryption at rest**: Are passwords hashed (bcrypt, argon2, scrypt)? Are tokens stored securely?

## 4. Input Validation & Output Encoding

- [ ] Is all external input validated for type, length, range, and format?
- [ ] Are file uploads checked for size, type (MIME magic bytes, not just extension), and path traversal?
- [ ] Are redirect URLs validated against a whitelist to prevent open redirect?
- [ ] Is XML parsed with entity expansion disabled (XXE prevention)?
- [ ] Are deserialisation sources trusted? (untrusted pickle/JSON.parse with reviver/YAML.load is dangerous)

## 5. Cryptography

- [ ] Are deprecated algorithms used? (MD5, SHA1 for security, DES, RC4)
- [ ] Are cipher modes correct? (AES-GCM or AES-CBC with HMAC; never ECB)
- [ ] Is randomness from a cryptographically secure source? (`os.urandom`, `crypto.randomBytes`, NOT `Math.random`)
- [ ] Are keys of adequate length? (RSA ≥ 2048, ECC ≥ 256, AES ≥ 128)

## 6. Session & Cookie Security

- [ ] Are session tokens generated with sufficient entropy?
- [ ] Cookie flags: `HttpOnly`, `Secure`, `SameSite` set appropriately?
- [ ] Is there session fixation protection? (regenerate ID after login)
- [ ] Are CSRF tokens present on state-changing requests?

## 7. Data Exposure & Privacy

- [ ] Are database queries over-fetching? (SELECT * when only a few columns are needed)
- [ ] Is PII being returned in API responses unnecessarily?
- [ ] Are pagination limits enforced to prevent mass data scraping?
- [ ] Is caching aware of sensitive data? (Cache-Control headers for authenticated pages)

## 8. Dependency & Supply Chain

- [ ] Are there dependencies with known vulnerabilities? (check advisories)
- [ ] Is the dependency pinned to a specific version or range that auto-upgrades?
- [ ] Is there a lockfile? Is it up to date?
- [ ] Are there unnecessary dependencies that increase the attack surface?

## 9. Denial of Service

- [ ] Are there unbounded operations? (infinite loops, unbounded allocations, recursive without limit)
- [ ] Are timeouts set on external calls (HTTP, DB, queues)?
- [ ] Are rate limits applied to public endpoints?
- [ ] Is user-controlled data used to allocate memory? (e.g., zip bombs, billion laughs)

## 10. Error Handling & Failures

- [ ] Do errors fail open or closed? (failing closed = denying access / stopping operation on error)
- [ ] Are exceptions caught at the right level, or are they silently swallowed?
- [ ] Is there a global error handler that prevents sensitive info leakage?
- [ ] Do failed security checks produce the same error as failed login to prevent user enumeration?
