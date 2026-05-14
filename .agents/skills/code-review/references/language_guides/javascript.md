# JavaScript / TypeScript Code Review Guide

## Style & Idioms

- Prefer `const` over `let`; never use `var` unless in a pre-ES6 codebase.
- Use arrow functions for callbacks and short functions; use regular functions when `this` binding matters.
- Use optional chaining (`?.`) and nullish coalescing (`??`) for safe property access.
- Prefer `async/await` over raw Promise chains or callbacks.
- Use template literals over string concatenation.
- In TypeScript: avoid `any`; use `unknown` when the type is truly unknown, and narrow it.

## Common Pitfalls

### Floating-Point Arithmetic
```javascript
// BAD — direct comparison
if (0.1 + 0.2 === 0.3) { /* never runs */ }

// GOOD
if (Math.abs(0.1 + 0.2 - 0.3) < Number.EPSILON) { /* works */ }
```

### Array Methods: Side Effects in map/filter
```javascript
// BAD — map should not have side effects
items.map(item => { db.save(item); return item; });

// GOOD
items.forEach(item => db.save(item));
```

### async without await inside loops
```javascript
// BAD — runs sequentially, usually unintentionally
for (const url of urls) {
  const data = await fetch(url);
}

// GOOD — if parallel is safe
const results = await Promise.all(urls.map(url => fetch(url)));
```

### Implicit Type Coercion
```javascript
// BAD — surprising results
if (value) { ... }     // 0, "", false, null, undefined all pass
if (value == null) { ... }  // catches undefined too

// GOOD — be explicit
if (value !== null && value !== undefined) { ... }
```

### Missing Error Handling in async Functions
```javascript
// BAD — unhandled promise rejection
async function getData() {
  return fetch('/api').then(r => r.json());
}

// GOOD — handle errors at the call site or with try/catch
async function getData() {
  try {
    const response = await fetch('/api');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (err) {
    console.error('Failed to fetch:', err);
    throw err;
  }
}
```

## Security-Specific

- **XSS**: innerHTML, document.write, and eval() with user input are critical red flags.
- **Prototype Pollution**: Merging user-supplied objects without sanitizing `__proto__` keys.
- **NoSQL Injection**: Passing user input directly into MongoDB `$where`, `$regex`, or untyped queries.
- **Secrets**: Client-side code should never contain API keys, tokens, or secrets. Flag any inline secrets.
- **CORS**: Misconfigured `Access-Control-Allow-Origin: *` with credentials is a security issue.
- **npm dependencies**: Flag packages with known vulnerabilities or unmaintained status.

## Node.js Specific

- **Blocking the event loop**: Synchronous fs/crypto operations (`readFileSync`, `pbkdf2Sync`) in request handlers.
- **Uncaught exceptions**: Missing `process.on('uncaughtException')` handler in production.
- **Memory leaks**: Event listeners not removed; large closures retaining references.

## React Specific

- Key props on list items should use stable unique IDs, not array indices (unless the list is static).
- Avoid inline function/object creation in JSX props inside render — use `useCallback`/`useMemo`.
- Side effects belong in `useEffect`, not in the render body.
- Flag direct DOM manipulation when React should manage it.

## Performance

- Flag `O(n²)` patterns like `array.includes()` inside a loop — suggest `Set`.
- Debounce/throttle rapid-fire events (scroll, resize, input).
- Lazy-load heavy modules with dynamic `import()`.
- Avoid deep cloning large objects inside hot paths; prefer structural sharing.

## Testing

- Flag untested async code, error paths, and edge cases.
- For React: prefer React Testing Library over Enzyme; test behaviour, not implementation.
- Mock external services, not the code under test.
