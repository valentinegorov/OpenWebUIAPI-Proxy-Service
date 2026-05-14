# Python Code Review Guide

## Style & Idioms

- Follow PEP 8 unless a project-specific style guide overrides it.
- Use list/dict/set comprehensions over `map`/`filter` with lambdas.
- Use `with` statements for resource management (files, locks, connections).
- Prefer `pathlib.Path` over `os.path` for new code.
- Use f-strings (Python 3.6+) for string formatting; avoid `%` formatting.
- Type hints are encouraged (`def foo(x: int) -> str:`); flag missing hints in public APIs.

## Common Pitfalls

### Mutable Default Arguments
```python
# BAD
def append_to(element, target=[]):
    target.append(element)
    return target

# GOOD
def append_to(element, target=None):
    if target is None:
        target = []
    target.append(element)
    return target
```

### Late Binding Closures
```python
# BAD — all lambdas capture the same `i`
funcs = [lambda: i for i in range(5)]

# GOOD
funcs = [lambda i=i: i for i in range(5)]
```

### Except: Broad Exception Handling
- Never use bare `except:` or `except Exception:` without re-raising or logging.
- Catch the most specific exception possible.
- Avoid `except: pass` — it silently swallows everything including `KeyboardInterrupt` and `SystemExit`.

### Eager vs Lazy Evaluation
- `range()` is lazy and memory-efficient; don't wrap in `list()` unnecessarily.
- Generator expressions `(...)` vs list comprehensions `[...]` — use generators when chaining operations.

### String Concatenation in Loops
```python
# BAD — creates a new string each iteration
result = ""
for item in items:
    result += str(item)

# GOOD
result = "".join(str(item) for item in items)
```

### Equality vs Identity
- Use `is` for singletons: `None`, `True`, `False`.
- Use `==` for value equality.
- Flag `x is 5` or `x == None` as bugs.

## Security-Specific

- **Subprocess**: Never use `shell=True` with user input. Prefer `subprocess.run([...])` with a command list.
- **Pickle**: Never unpickle untrusted data. Use `json` or a safe serialization format.
- **SQL**: Flag `cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")`. Use parameterised queries.
- **Path Traversal**: When constructing file paths from user input, use `pathlib` and validate the resolved path stays within the expected directory.
- **Secrets**: Flag any inline API keys, tokens, or passwords.

## Performance

- Flag O(n²) patterns like `if x in list` inside a loop — suggest converting to `set`.
- Flag `df.iterrows()` in pandas — suggest vectorised operations or `itertuples()`.
- Profile before optimising; don't suggest performance improvements without clear evidence of a bottleneck.

## Testing

- Flag public functions/methods without corresponding tests.
- Check that edge cases are covered: empty input, None, large inputs, Unicode strings.
- Fixtures in `conftest.py` are preferred over repeated setup in test files.
