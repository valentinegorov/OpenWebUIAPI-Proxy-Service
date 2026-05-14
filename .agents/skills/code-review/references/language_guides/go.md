# Go Code Review Guide

## Style & Idioms

- Follow `go fmt` / `gofmt` conventions — formatting is non-negotiable in Go.
- Follow Effective Go and the Code Review Comments wiki for naming and structure.
- Variable names: short in small scopes (`i`, `c`), descriptive in large scopes.
- Package names: lowercase, single word, no underscores, no `util` or `common` packages.
- Error strings should not be capitalised and should not end with punctuation.
- Use `context.Context` as the first parameter in functions that do I/O or blocking work.
- Prefer composition over inheritance (embedding structs).

## Common Pitfalls

### Goroutine Leaks
```go
// BAD — goroutine may block forever if ctx is never cancelled
go func() {
    <-ctx.Done()
    cleanup()
}()

// GOOD — always ensure goroutines can exit
go func() {
    select {
    case <-ctx.Done():
        cleanup()
    case <-time.After(timeout):
        cleanup()
    }
}()
```

### Defer in Loops
```go
// BAD — defer runs when function returns, not at end of iteration
for _, f := range files {
    file, _ := os.Open(f)
    defer file.Close()  // all files stay open until function ends
}

// GOOD — use an anonymous function
for _, f := range files {
    func() {
        file, _ := os.Open(f)
        defer file.Close()
        // use file
    }()
}
```

### Nil Interface vs Nil Pointer
```go
// BUG: a nil pointer stored in an interface is NOT a nil interface
var p *MyStruct = nil
var i interface{} = p
fmt.Println(i == nil) // false!

// Always return nil directly
func get() error {
    return nil // not a nil *MyError
}
```

### Copying Sync Primitives
```go
// BAD — mutex is copied
var mu sync.Mutex
m2 := mu // copies the mutex state — undefined behavior
doWork(mu) // pass by value copies the mutex

// GOOD — use pointer receiver or pass by pointer
func (s *Server) handle() {
    s.mu.Lock()
    defer s.mu.Unlock()
}
```

### Slice Confusion with append
```go
// BAD — unexpected aliasing
a := []int{1, 2, 3}
b := append(a[:2], 4) // may overwrite a[2]
fmt.Println(a) // could be [1, 2, 4]

// GOOD — use copy or full slice expression
b := append([]int{}, a[:2]...)
b = append(b, 4)
```

## Security-Specific

- **SQL Injection**: Never use `fmt.Sprintf` to build queries. Use `database/sql` placeholders.
- **Command Injection**: Never pass user input to `exec.Command` with `sh -c`. Use the `Command(name, arg...)` form.
- **Template Injection**: Validate that `html/template` is used for HTML (auto-escapes), not `text/template`.
- **TLS**: Never use `InsecureSkipVerify: true` in production TLS config.
- **Path Traversal**: Use `filepath.Clean` and validate that resolved paths stay within expected directory.
- **Crypto**: Use `crypto/rand` for randomness, not `math/rand`.

## Concurrency & Channels

- Check for goroutine leaks: every `go` should have a clear exit path.
- Channels: who closes the channel? Document ownership.
- Avoid buffered channels as a substitute for proper synchronization.
- Use `sync.WaitGroup` or `errgroup.Group` for waiting on goroutines.
- Flag shared mutable state without synchronisation (`go test -race`).

## Error Handling

- Never ignore errors: `_, _ = file.Read(buf)` is a red flag.
- Wrap errors with context: `fmt.Errorf("doing X: %w", err)` (Go 1.13+).
- Don't over-wrap — one `%w` is usually enough; chain with `errors.Is` and `errors.As`.
- Don't log AND return an error — pick one (usually return).

## Performance

- Flag allocations in hot loops: prefer pointers or value types appropriately.
- `strings.Builder` over `+` concatenation in loops.
- `sync.Pool` for frequently allocated short-lived objects.
- Avoid `interface{}` in performance-critical paths — use generics (Go 1.18+) or concrete types.
- Profile with `pprof` before optimising; don't guess.

## Testing

- Use table-driven tests (`t.Run`).
- Use `t.Parallel()` for independent tests.
- Prefer `testing/fstest` and interfaces over mocking with third-party libraries.
- Test error paths, not just happy paths.
- Use `go test -race` for concurrency testing.
