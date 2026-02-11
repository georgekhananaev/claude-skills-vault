# Structured Logging Standards

Cross-language structured logging for observability.

## Why Structured Logging?

| Unstructured | Structured |
|--------------|------------|
| `User 123 logged in` | `{"event":"login","user_id":"123"}` |
| Hard to parse | Machine-readable |
| No filtering | Filter by field |
| No aggregation | Count by event type |
| Debug only | Production observability |

## Core Rules

| Rule | Severity | Description |
|------|----------|-------------|
| JSON format | Error | All logs must be structured JSON |
| Correlation IDs | Error | Every request needs traceId |
| No PII | Critical | Never log passwords, tokens, emails |
| Log levels | Warning | Use appropriate level |

## Log Levels

| Level | Use Case | Example |
|-------|----------|---------|
| **error** | Failures requiring attention | DB connection failed |
| **warn** | Potential issues | Retry attempt 3/5 |
| **info** | Business events | User created |
| **debug** | Development details | Query took 50ms |

## TypeScript (pino)

### Setup

```typescript
import pino from 'pino';

const logger = pino({
    level: process.env.LOG_LEVEL || 'info',
    formatters: {
        level: (label) => ({ level: label }),
    },
    // Redact sensitive fields
    redact: ['password', 'token', 'authorization', 'cookie'],
});
```

### Usage

```typescript
// GOOD: Structured with context
logger.info({ userId, action: 'login', duration: 150 }, 'User logged in');

// GOOD: Error with stack trace
logger.error({ err, userId }, 'Failed to process payment');

// GOOD: Child logger with request context
const reqLogger = logger.child({ requestId, userId });
reqLogger.info({ action: 'checkout' }, 'Processing checkout');

// BAD: Unstructured string
console.log(`User ${userId} logged in`);  // Error

// BAD: Sensitive data
logger.info({ password, token });  // Critical - never log secrets
```

### Request Middleware

```typescript
import { randomUUID } from 'crypto';

function requestLogger(req, res, next) {
    const requestId = req.headers['x-request-id'] || randomUUID();

    req.log = logger.child({
        requestId,
        method: req.method,
        path: req.path,
    });

    const start = Date.now();

    res.on('finish', () => {
        req.log.info({
            statusCode: res.statusCode,
            duration: Date.now() - start,
        }, 'Request completed');
    });

    next();
}
```

## Python (structlog)

### Setup

```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        int(os.getenv("LOG_LEVEL", "20"))  # INFO
    ),
)

logger = structlog.get_logger()
```

### Usage

```python
# GOOD: Structured
logger.info("user_login", user_id=user_id, duration_ms=150)

# GOOD: Error with exception
try:
    process()
except Exception:
    logger.exception("processing_failed", user_id=user_id)

# GOOD: Bound logger with context
log = logger.bind(request_id=request_id, user_id=user_id)
log.info("checkout_started")

# BAD: f-string logging
print(f"User {user_id} logged in")  # Error

# BAD: Using logging module directly with f-strings
import logging
logging.info(f"User {user_id} logged in")  # Error - always evaluated
```

### Request Context

```python
from structlog.contextvars import bind_contextvars, clear_contextvars

@contextmanager
def request_context(request_id: str, user_id: str | None = None):
    bind_contextvars(request_id=request_id, user_id=user_id)
    try:
        yield
    finally:
        clear_contextvars()

# Usage in middleware
async def logging_middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))

    with request_context(request_id):
        logger.info("request_started", method=request.method, path=request.url.path)
        start = time.monotonic()

        response = await call_next(request)

        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=int((time.monotonic() - start) * 1000),
        )
        return response
```

## Go (zerolog)

### Setup

```go
package main

import (
    "os"
    "github.com/rs/zerolog"
    "github.com/rs/zerolog/log"
)

func init() {
    zerolog.TimeFieldFormat = zerolog.TimeFormatUnix

    level, _ := zerolog.ParseLevel(os.Getenv("LOG_LEVEL"))
    if level == zerolog.NoLevel {
        level = zerolog.InfoLevel
    }
    zerolog.SetGlobalLevel(level)
}
```

### Usage

```go
// GOOD: Structured
log.Info().
    Str("user_id", userID).
    Str("action", "login").
    Int("duration_ms", 150).
    Msg("user logged in")

// GOOD: Error with error field
log.Error().
    Err(err).
    Str("user_id", userID).
    Msg("failed to process payment")

// GOOD: Logger with context
logger := log.With().
    Str("request_id", requestID).
    Str("user_id", userID).
    Logger()

logger.Info().Msg("processing checkout")

// BAD: Printf style
fmt.Printf("User %s logged in\n", userID)  // Error
log.Printf("User %s logged in", userID)    // Error
```

### Request Context

```go
func LoggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            requestID = uuid.New().String()
        }

        logger := log.With().
            Str("request_id", requestID).
            Str("method", r.Method).
            Str("path", r.URL.Path).
            Logger()

        ctx := logger.WithContext(r.Context())

        start := time.Now()

        ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)
        next.ServeHTTP(ww, r.WithContext(ctx))

        log.Ctx(ctx).Info().
            Int("status", ww.Status()).
            Dur("duration", time.Since(start)).
            Msg("request completed")
    })
}
```

## Rust (tracing)

### Setup

```rust
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

fn init_logging() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info".into()),
        )
        .with(tracing_subscriber::fmt::layer().json())
        .init();
}
```

### Usage

```rust
use tracing::{info, error, instrument, Span};

// GOOD: Structured
info!(user_id = %user_id, action = "login", duration_ms = 150, "user logged in");

// GOOD: Error with error field
error!(?err, user_id = %user_id, "failed to process payment");

// GOOD: Instrumented function
#[instrument(skip(password))]
async fn login(username: &str, password: &str) -> Result<User, Error> {
    info!("attempting login");
    // ...
}

// GOOD: Span for request context
let span = tracing::info_span!("request", request_id = %request_id);
let _guard = span.enter();
```

## PII Redaction

```typescript
// Helper to mask sensitive data
function maskEmail(email: string): string {
    const [local, domain] = email.split('@');
    return `${local[0]}***@${domain[0]}***.${domain.split('.').pop()}`;
}

function maskCard(card: string): string {
    return `****${card.slice(-4)}`;
}

// Use in logging
logger.info({
    email: maskEmail(user.email),
    cardLast4: user.card.slice(-4),
});
```

## Observability Stack Integration

### OpenTelemetry

```typescript
import { trace } from '@opentelemetry/api';

const tracer = trace.getTracer('my-service');

const span = tracer.startSpan('process-order');
span.setAttribute('order.id', orderId);

logger.info({
    traceId: span.spanContext().traceId,
    orderId,
}, 'Processing order');

span.end();
```

### Correlation IDs

Every log entry should include:
- `request_id` - Unique per request
- `trace_id` - OpenTelemetry trace ID (if available)
- `user_id` - Current user (if authenticated)
- `service` - Service name