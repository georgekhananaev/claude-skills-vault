# Go Standards

Idiomatic Go with strict error handling and concurrency safety.

## Core Principles

- **Always handle errors**: No `_` for errors
- **Context propagation**: Pass context.Context as first param
- **Interface segregation**: Small, focused interfaces
- **Goroutine safety**: Proper synchronization

## Error Handling (Mandatory)

### Never Ignore Errors

```go
// CRITICAL: Never ignore errors
result, _ := doSomething()       // Error - ignored error
_ = json.Unmarshal(data, &obj)   // Error - ignored error

// OK: Handle errors explicitly
result, err := doSomething()
if err != nil {
    return fmt.Errorf("doing something: %w", err)
}

// OK: If truly ignorable, document why
_ = os.Remove(tempFile) // Best effort cleanup, ignore error
```

### Wrap Errors with Context

```go
// Error - no context
if err != nil {
    return err
}

// OK - wrapped with context
if err != nil {
    return fmt.Errorf("fetching user %s: %w", userID, err)
}

// OK - custom error types
type NotFoundError struct {
    Resource string
    ID       string
}

func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s not found: %s", e.Resource, e.ID)
}
```

### Error Checking Patterns

```go
// Check errors immediately
file, err := os.Open(path)
if err != nil {
    return nil, fmt.Errorf("opening file: %w", err)
}
defer file.Close()

// Use errors.Is/As for sentinel errors
if errors.Is(err, sql.ErrNoRows) {
    return nil, ErrNotFound
}

var pathErr *os.PathError
if errors.As(err, &pathErr) {
    log.Printf("path error on %s: %v", pathErr.Path, pathErr.Err)
}
```

## Context Propagation

```go
// ALWAYS pass context as first parameter
func ProcessUser(ctx context.Context, userID string) error {
    // Check context before expensive operations
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }

    // Pass context to all downstream calls
    user, err := db.GetUser(ctx, userID)
    if err != nil {
        return fmt.Errorf("getting user: %w", err)
    }

    return notify.Send(ctx, user.Email, "Welcome!")
}

// Use context for timeouts
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

result, err := slowOperation(ctx)
```

## Concurrency Safety

### Race Detection

```go
// ALWAYS run tests with race detector
// go test -race ./...

// ERROR: Data race
var counter int

func increment() {
    counter++  // Race condition
}

// OK: Use mutex
var (
    counter int
    mu      sync.Mutex
)

func increment() {
    mu.Lock()
    defer mu.Unlock()
    counter++
}

// OK: Use atomic
var counter atomic.Int64

func increment() {
    counter.Add(1)
}

// OK: Use channels
func increment(c chan<- int) {
    c <- 1
}
```

### Goroutine Lifecycle

```go
// ERROR: Goroutine leak
func bad() {
    go func() {
        // No way to stop this
        for {
            doWork()
        }
    }()
}

// OK: Proper cancellation
func good(ctx context.Context) {
    go func() {
        for {
            select {
            case <-ctx.Done():
                return
            default:
                doWork()
            }
        }
    }()
}

// OK: WaitGroup for completion
func processAll(items []Item) error {
    var wg sync.WaitGroup
    errCh := make(chan error, len(items))

    for _, item := range items {
        wg.Add(1)
        go func(item Item) {
            defer wg.Done()
            if err := process(item); err != nil {
                errCh <- err
            }
        }(item)
    }

    wg.Wait()
    close(errCh)

    for err := range errCh {
        if err != nil {
            return err
        }
    }
    return nil
}
```

## golangci-lint Configuration

```yaml
linters:
  enable:
    - errcheck
    - govet
    - staticcheck
    - gosimple
    - ineffassign
    - unused
    - gocritic
    - gofmt
    - goimports
    - gosec
    - exhaustive
    - nilnil
    - nilerr
    - contextcheck
    - errorlint
    - wrapcheck
    - prealloc
    - unconvert
    - gocyclo
    - funlen
    - godot
    - misspell

linters-settings:
  errcheck:
    check-type-assertions: true
    check-blank: true
  govet:
    enable-all: true
  gocritic:
    enabled-tags:
      - diagnostic
      - style
      - performance
  exhaustive:
    default-signifies-exhaustive: true
  gocyclo:
    min-complexity: 10
  funlen:
    lines: 50
    statements: 40
  wrapcheck:
    ignoreSigs:
      - .Errorf(
      - errors.New(
      - errors.Join(

run:
  timeout: 5m
  skip-dirs:
    - generated
    - mocks
    - pb
  skip-files:
    - ".*\\.pb\\.go$"
    - ".*_mock\\.go$"

issues:
  exclude-use-default: false
  max-issues-per-linter: 0
  max-same-issues: 0
```

## Interface Design

```go
// ERROR: Large interface
type UserService interface {
    Create(ctx context.Context, u *User) error
    Get(ctx context.Context, id string) (*User, error)
    Update(ctx context.Context, u *User) error
    Delete(ctx context.Context, id string) error
    List(ctx context.Context) ([]*User, error)
    Search(ctx context.Context, q string) ([]*User, error)
    // ... 10 more methods
}

// OK: Small, focused interfaces
type UserReader interface {
    Get(ctx context.Context, id string) (*User, error)
}

type UserWriter interface {
    Create(ctx context.Context, u *User) error
    Update(ctx context.Context, u *User) error
}

type UserDeleter interface {
    Delete(ctx context.Context, id string) error
}

// Compose when needed
type UserStore interface {
    UserReader
    UserWriter
    UserDeleter
}
```

## Function Design

```go
// ERROR: Naked returns in long functions
func bad(x int) (result int, err error) {
    // ... 20+ lines ...
    return  // Error - unclear what's returned
}

// OK: Explicit returns
func good(x int) (int, error) {
    // ... processing ...
    return result, nil
}

// ERROR: Too many parameters
func bad(a, b, c, d, e, f string) error { ... }

// OK: Use options pattern or config struct
type Config struct {
    A, B, C string
}

func good(cfg Config) error { ... }

// OR functional options
type Option func(*config)

func WithTimeout(d time.Duration) Option {
    return func(c *config) { c.timeout = d }
}

func New(opts ...Option) *Service { ... }
```

## Structured Logging

```go
import "github.com/rs/zerolog/log"

// ERROR: Printf style
fmt.Printf("User %s logged in\n", userID)
log.Printf("Processing %d items", len(items))

// OK: Structured logging
log.Info().
    Str("user_id", userID).
    Str("action", "login").
    Msg("user logged in")

log.Error().
    Err(err).
    Str("user_id", userID).
    Msg("failed to process")
```

## Anti-Patterns

| Bad | Good | Why |
|-----|------|-----|
| `_, _ = fn()` | `err := fn()` | Handle errors |
| Naked returns | Explicit returns | Clarity |
| Big interfaces | Small interfaces | Decoupling |
| `panic()` for errors | Return `error` | Recoverable |
| Global state | Dependency injection | Testability |
| `init()` functions | Explicit initialization | Predictable |
| Magic numbers | Named constants | Readability |