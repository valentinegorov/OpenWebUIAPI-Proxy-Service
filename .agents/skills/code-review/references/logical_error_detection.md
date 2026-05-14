# Logical Error & Internal Contradiction Detection

This reference covers systematic detection of logical errors and internal
project contradictions. Use during steps 3–4 of the code-review workflow
when reviewing correctness and hidden assumptions.

---

## 1. Definitions

| Term | Definition |
|:---|:---|
| **Logical error** | The code runs without crashing but produces incorrect results. The program follows the *wrong* algorithm or makes flawed assumptions. |
| **Internal contradiction** | Two or more parts of the codebase make mutually exclusive claims about state, invariants, or behaviour. Both *cannot* be true at the same time. |

These are the most dangerous class of bugs because compilers, linters, and
type checkers rarely catch them — only careful human (or agent) review does.

---

## 2. Logical Error Detection Patterns

### 2.1. Condition Inversion & Misplacement

The most common logical error: a condition that tests the opposite of what
the author intended, or a condition placed at the wrong scope.

**Heuristics to flag:**
- Early-return guards that return the wrong value:
  ```javascript
  // SUSPICIOUS: returns null when item IS found — inverted logic likely
  function find(items, id) {
      if (items.find(i => i.id === id)) return null;
      return items.find(i => i.id === id);
  }
  ```
- `if/else` blocks where both branches produce the same result.
- Negation where a double-negative obscures the intent (`if (!isNotValid)`).
- Boolean parameters that are always called with the same value — dead code smell.

### 2.2. Off-by-One Errors

**Heuristics:**
- Loop bounds: `i < len` vs `i <= len` vs `i < len - 1`. Trace with `len=0` and `len=1`.
- Array slicing: `slice(0, n)` excludes index `n`. Confirm intent.
- Pagination: check boundary calculations — `offset + limit > total` cases.
- Date range queries: `>= start AND < end` (exclusive end) vs `BETWEEN` (inclusive both sides) — flag inconsistencies.

**Quick check:** For any loop or range, mentally substitute the minimum and maximum values (0, 1, empty) and verify the behaviour.

### 2.3. Wrong Operator or Comparator

**Heuristics:**
- `>` vs `>=` — one character that changes entire filter semantics.
- `&&` vs `||` — De Morgan's law violations: `!(a && b)` should be `!a || !b`.
- Assignment `=` instead of comparison `==`/`===` (languages where this is allowed).
- Bitwise `&`/`|` used where logical `&&`/`||` is intended (or vice versa).

### 2.4. Swapped Arguments

**Heuristics:**
- Functions with multiple parameters of the **same type**: `move(from, to)` called as `move(to, from)`.
- Callbacks where parameter order matters: `Array.reduce((acc, cur) => ...)` not `(cur, acc)`.
- Flag the second parameter when its name in the call expression matches the first parameter name in the signature.

### 2.5. Missing or Redundant Updates

**Heuristics:**
- A state variable that is set but never read (dead store).
- A counter incremented inside a condition but missed outside of it.
- Cached values not invalidated when the underlying data changes.
- Two variables that should always be updated together but sometimes diverge (split updates).

### 2.6. Idempotency Confusion

**Heuristics:**
- A function documented as idempotent that has side effects or state dependence.
- Payment/charge functions without deduplication keys — double-charge risk.
- Retry logic that doesn't check whether the first attempt succeeded before retrying.

### 2.7. Time & Concurrency Assumptions

**Heuristics:**
- `Date.now()` used for unique ID generation (collisions possible).
- `setTimeout(fn, 0)` assuming it runs immediately (it queues to the event loop).
- Read-check-write patterns without locking → TOCTOU (time-of-check-to-time-of-use) bugs.
- Optimistic UI updates without a rollback path on server error.

---

## 3. Internal Contradiction Detection

### 3.1. Conflicting Business Rules

Search the codebase for the same domain concept implemented differently.

**Method:** grep for unique domain terms and compare the surrounding logic.

```
Example workflow:
1. Identify a key term: "discount", "refund", "timeout"
2. grep across the codebase for that term
3. Compare each occurrence's logic
4. Flag any two implementations that would disagree on the same input
```

**Specific red flags:**
- Two validation functions for the same entity with different rules.
- `maxRetries: 3` in one file and `MAX_RETRIES = 5` in another.
- One function assumes IDs are numeric; another treats them as strings.
- Different default values for the same config key in different modules.

### 3.2. Comment-Code Contradictions

The comment says one thing; the code does another. The code is usually the truth,
but the *intent* is unclear — so either could be wrong.

**Heuristics:**
```python
# Returns the user's age in years
def get_user_age(user):
    return (datetime.now() - user.birthdate).days  # returns days, not years!
```
```javascript
// Never returns null
function lookup(id) {
    if (!id) return null;  // contradicts the comment
}
```

**Method:**
- For every non-trivial function comment, read the implementation and check congruence.
- Flag any comment that describes *what* happens that differs from *how* it happens.

### 3.3. Type & Nullability Contradictions

**Heuristics:**
- A variable typed as `T` (non-nullable) but initialised from a function that can return `null`.
- A TypeScript interface declares `field: string` but the API response occasionally omits it.
- A Go function returns `(T, error)` where `T` is a struct — when an error occurs, is `T` valid? The zero value may violate invariants.
- An `Optional<T>` that is `.get()`'d without `.isPresent()` check, contradicting the optional contract.

### 3.4. State Machine Inconsistencies

**Heuristics:**
- Enums/states with undocumented transitions (e.g., `CANCELLED → SHIPPED`).
- Guards that protect a transition but not the same transition from a different call site.
- Two pieces of code that disagree about what state the system is in.
- Missing terminal states — a state machine where nothing prevents re-processing a terminal state.

**Method:**
- Draw (mentally or explicitly) the state diagram from the setter/transition code.
- Look for transitions that bypass guards.
- Look for callers that invoke a transition without checking the current state first.

### 3.5. Dependency & Import Contradictions

**Heuristics:**
- Module A imports from Module B, and Module B imports from Module A (circular dependency — may work in some languages but signals poor separation).
- Two modules define the same constant independently (copy-paste drift).
- A "utils" function used in the frontend that assumes a Node.js environment (or vice versa).

---

## 4. Systematic Search Strategy

When reviewing a codebase (not a single snippet), follow this sequence:

### Step 1: Map key invariants
```
For each core entity (User, Order, Payment, etc.), ask:
- What must always be true about this entity? (invariants)
- Where are these invariants enforced? (validation, constructors, DB constraints)
- Are there any paths that bypass enforcement?
```

### Step 2: Trace the lifecycle
```
Pick a data type. Follow it from creation to deletion:
- Who creates it? Under what conditions?
- Who mutates it? Is mutation guarded?
- Who reads it? Do readers agree on the shape/semantics?
- Who deletes it? What happens to references?
```

### Step 3: Diff the happy path vs error paths
```
For each function that has early returns or exception handling:
- Does the error path clean up state the same way the happy path does?
- Are resources (file handles, connections, locks) released in both paths?
- Does the caller handle the error case correctly?
```

### Step 4: Cross-reference configuration
```
- Find all config/default files (.env, config.yaml, constants.ts, etc.)
- Find all usages of each config key
- Flag any case where the usage assumes a different type, range, or format than the default
```

### Step 5: Compare sibling implementations
```
- Two DAO/repository classes for different entities — do they handle errors the same way?
- Two API endpoints that accept similar payloads — do they validate the same fields?
- Two serializers/deserializers — do they agree on field naming (camelCase vs snake_case)?
```

---

## 5. Severity Guidelines

| Level | Criteria | Example |
|:---|:---|:---|
| **High** | Produces incorrect results silently in normal operation. Data corruption risk. | Wrong tax calculation, inverted auth check, missing dedup key |
| **Medium** | Produces incorrect results in edge cases. User-visible bug under specific conditions. | Off-by-one in pagination boundary, timezone mismatch in date display |
| **Low** | Internal inconsistency with no immediate bug but future maintenance risk. | Comment-code mismatch, redundant state variable |

---

## 6. Output Format for Logical Errors

When reporting a logical error or contradiction, include:

```
**Logical Error: [short title]**
- **Location**: file:line — [function/block name]
- **What the code does**: [what the code actually computes/does]
- **What it should do**: [what the author likely intended]
- **Why it matters**: [consequence in production]
- **Evidence of contradiction** (if applicable): [link to the conflicting code]
- **Suggested fix**: [concrete code change]
```
