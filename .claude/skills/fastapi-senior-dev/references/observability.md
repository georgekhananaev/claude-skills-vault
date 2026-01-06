# Observability: Logging, Metrics, Tracing

## OpenTelemetry Setup

### Auto-Instrumentation

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

def setup_telemetry(app: FastAPI):
    # Configure tracer provider
    provider = TracerProvider()
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint="http://tempo:4317", insecure=True)
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Auto-instrument frameworks
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

# In main.py
setup_telemetry(app)
```

### Manual Span Creation

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def process_order(order_id: int):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)

        with tracer.start_as_current_span("validate_order"):
            await validate_order(order_id)

        with tracer.start_as_current_span("charge_payment"):
            result = await charge_payment(order_id)
            span.set_attribute("payment.success", result.success)

        with tracer.start_as_current_span("send_confirmation"):
            await send_confirmation_email(order_id)
```

### Context Propagation

```python
from opentelemetry.propagate import inject, extract
import httpx

async def call_external_service(data: dict):
    headers = {}
    inject(headers)  # Inject trace context into headers

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://external-service.com/api",
            json=data,
            headers=headers
        )
    return response.json()

# Incoming requests automatically extract context via instrumentation
```

### Sampling Strategies

```python
from opentelemetry.sdk.trace.sampling import (
    TraceIdRatioBased,
    ParentBased,
    ALWAYS_ON,
    ALWAYS_OFF
)

# Head-based sampling: 10% of traces
sampler = ParentBased(root=TraceIdRatioBased(0.1))

# Always sample errors (tail-based simulation)
class ErrorAwareSampler(Sampler):
    def should_sample(self, parent_context, trace_id, name, kind, attributes, links):
        # Always sample if parent was sampled
        if parent_context and parent_context.trace_flags.sampled:
            return SamplingResult(Decision.RECORD_AND_SAMPLE)

        # Sample 10% of normal requests
        if self._should_sample_ratio(trace_id, 0.1):
            return SamplingResult(Decision.RECORD_AND_SAMPLE)

        return SamplingResult(Decision.DROP)

# Apply in TracerProvider
provider = TracerProvider(sampler=sampler)
```

## Prometheus Metrics

### Instrumentation

```python
from prometheus_fastapi_instrumentator import Instrumentator, metrics

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    excluded_handlers=["/health", "/metrics"],
)

# Add default metrics
instrumentator.add(metrics.default())

# Add custom metrics
instrumentator.add(
    metrics.latency_histogram_by_path_method(
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )
)

# Instrument app
instrumentator.instrument(app).expose(app, endpoint="/metrics")
```

### Custom Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Counters
orders_created = Counter(
    "orders_created_total",
    "Total orders created",
    ["status", "payment_method"]
)

# Histograms
order_processing_time = Histogram(
    "order_processing_seconds",
    "Time to process order",
    ["order_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Gauges
active_connections = Gauge(
    "active_db_connections",
    "Current database connections"
)

# Usage
async def create_order(order: Order):
    with order_processing_time.labels(order_type=order.type).time():
        result = await process_order(order)
        orders_created.labels(
            status="success" if result.success else "failed",
            payment_method=order.payment_method
        ).inc()
        return result

# Update gauge
active_connections.set(engine.pool.checkedout())
```

### AlertManager Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: fastapi
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          / sum(rate(http_requests_total[5m])) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate ({{ $value | printf \"%.2f\" }}%)"

      # Slow responses (SLO violation)
      - alert: SlowResponses
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, path)
          ) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency > 500ms on {{ $labels.path }}"

      # Database connection exhaustion
      - alert: DBConnectionsHigh
        expr: active_db_connections > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connections approaching limit"
```

## Structured Logging

### Structlog Configuration

```python
import structlog
from structlog.types import Processor
import logging

def setup_logging(json_logs: bool = True):
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()
```

### Request ID Injection

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id

        # Bind to structlog context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response

app.add_middleware(RequestIDMiddleware)
```

### Log Sanitization

```python
SENSITIVE_KEYS = {"password", "token", "authorization", "api_key", "secret"}

def sanitize_processor(logger, method_name, event_dict):
    """Remove sensitive data from logs."""
    def sanitize(obj):
        if isinstance(obj, dict):
            return {
                k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else sanitize(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [sanitize(item) for item in obj]
        return obj

    return sanitize(event_dict)

# Add to processors
structlog.configure(
    processors=[
        sanitize_processor,
        # ... other processors
    ]
)
```

### Trace Correlation

```python
from opentelemetry import trace

def add_trace_context(logger, method_name, event_dict):
    """Add trace ID to log entries."""
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict

# Add to structlog processors
```

## Health Checks

### Liveness & Readiness

```python
from fastapi import APIRouter
from pydantic import BaseModel
from enum import Enum

health_router = APIRouter(tags=["health"])

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"

class HealthCheck(BaseModel):
    status: HealthStatus
    checks: dict[str, bool] = {}
    version: str = "1.0.0"

@health_router.get("/health/live")
async def liveness():
    """Kubernetes liveness probe. Is the process running?"""
    return {"status": "ok"}

@health_router.get("/health/ready", response_model=HealthCheck)
async def readiness(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Kubernetes readiness probe. Can we serve traffic?"""
    checks = {}

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    # Check Redis
    try:
        await redis.ping()
        checks["redis"] = True
    except Exception:
        checks["redis"] = False

    # Determine overall status
    all_healthy = all(checks.values())
    status = HealthStatus.HEALTHY if all_healthy else HealthStatus.UNHEALTHY

    response = HealthCheck(status=status, checks=checks)

    if not all_healthy:
        raise HTTPException(503, detail=response.model_dump())

    return response

@health_router.get("/health/startup")
async def startup():
    """Kubernetes startup probe. Has the app finished initializing?"""
    # Check if all startup tasks completed
    return {"status": "ready"}
```

## Error Tracking (Sentry)

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

def setup_sentry(dsn: str, environment: str):
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.1,  # 10% of sampled transactions
        send_default_pii=False,  # Don't send PII

        # Filter sensitive data
        before_send=filter_sensitive_data,
    )

def filter_sensitive_data(event, hint):
    """Remove sensitive data before sending to Sentry."""
    if "request" in event:
        headers = event["request"].get("headers", {})
        for key in ["authorization", "cookie", "x-api-key"]:
            if key in headers:
                headers[key] = "[REDACTED]"
    return event

# Hide stack traces in production responses
@app.exception_handler(Exception)
async def sentry_exception_handler(request: Request, exc: Exception):
    # Sentry captures automatically via integration
    logger.exception("Unhandled exception", exc_info=exc)

    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An error occurred"}}
    )
```

## Grafana Dashboard Patterns

### RED Metrics Dashboard

```json
{
  "panels": [
    {
      "title": "Request Rate",
      "type": "stat",
      "targets": [{
        "expr": "sum(rate(http_requests_total[5m]))"
      }]
    },
    {
      "title": "Error Rate",
      "type": "gauge",
      "targets": [{
        "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100"
      }]
    },
    {
      "title": "P95 Latency",
      "type": "timeseries",
      "targets": [{
        "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))"
      }]
    }
  ]
}
```

## Required Packages

```bash
# OpenTelemetry
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-sqlalchemy
pip install opentelemetry-instrumentation-redis
pip install opentelemetry-instrumentation-httpx
pip install opentelemetry-exporter-otlp

# Prometheus
pip install prometheus-fastapi-instrumentator prometheus-client

# Logging
pip install structlog

# Error tracking
pip install sentry-sdk[fastapi]
```