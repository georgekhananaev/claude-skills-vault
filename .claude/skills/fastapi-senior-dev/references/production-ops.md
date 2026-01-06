# Production Operations

## Health Check Endpoints

### Complete Health Check

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
import asyncio

health_router = APIRouter(prefix="/health", tags=["Health"])

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class DependencyCheck(BaseModel):
    name: str
    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None

class HealthResponse(BaseModel):
    status: HealthStatus
    timestamp: datetime
    version: str
    checks: list[DependencyCheck]

async def check_database(db: AsyncSession) -> DependencyCheck:
    start = datetime.utcnow()
    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=5.0)
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        return DependencyCheck(name="database", status=HealthStatus.HEALTHY, latency_ms=latency)
    except asyncio.TimeoutError:
        return DependencyCheck(name="database", status=HealthStatus.UNHEALTHY, message="Timeout")
    except Exception as e:
        return DependencyCheck(name="database", status=HealthStatus.UNHEALTHY, message=str(e))

async def check_redis(redis: Redis) -> DependencyCheck:
    start = datetime.utcnow()
    try:
        await asyncio.wait_for(redis.ping(), timeout=2.0)
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        return DependencyCheck(name="redis", status=HealthStatus.HEALTHY, latency_ms=latency)
    except Exception as e:
        return DependencyCheck(name="redis", status=HealthStatus.UNHEALTHY, message=str(e))

@health_router.get("/live")
async def liveness():
    """Kubernetes liveness probe - is the process running?"""
    return {"status": "ok"}

@health_router.get("/ready", response_model=HealthResponse)
async def readiness(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """Kubernetes readiness probe - can we serve traffic?"""
    checks = await asyncio.gather(
        check_database(db),
        check_redis(redis),
    )

    # Determine overall status
    if any(c.status == HealthStatus.UNHEALTHY for c in checks):
        status = HealthStatus.UNHEALTHY
    elif any(c.status == HealthStatus.DEGRADED for c in checks):
        status = HealthStatus.DEGRADED
    else:
        status = HealthStatus.HEALTHY

    response = HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        version=settings.version,
        checks=checks
    )

    if status == HealthStatus.UNHEALTHY:
        raise HTTPException(status_code=503, detail=response.model_dump())

    return response

@health_router.get("/startup")
async def startup_check():
    """Kubernetes startup probe - has initialization completed?"""
    if not app.state.ready:
        raise HTTPException(503, "Still starting up")
    return {"status": "ready"}
```

## Graceful Shutdown

### Signal Handling

```python
import signal
import asyncio
from contextlib import asynccontextmanager

shutdown_event = asyncio.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.ready = False

    # Initialize connections
    await init_database()
    await init_redis()
    await init_celery()

    app.state.ready = True
    logger.info("Application started")

    yield

    # Shutdown
    logger.info("Shutdown initiated")
    shutdown_event.set()

    # Wait for in-flight requests (handled by uvicorn)
    await asyncio.sleep(5)

    # Close connections gracefully
    await close_database()
    await close_redis()

    logger.info("Shutdown complete")

app = FastAPI(lifespan=lifespan)

# Handle SIGTERM
def handle_sigterm(signum, frame):
    logger.info("Received SIGTERM")
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_sigterm)
```

### Connection Draining

```python
from starlette.middleware.base import BaseHTTPMiddleware

class GracefulShutdownMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if shutdown_event.is_set():
            return JSONResponse(
                status_code=503,
                content={"error": "Service shutting down"},
                headers={"Connection": "close"}
            )

        response = await call_next(request)

        if shutdown_event.is_set():
            response.headers["Connection"] = "close"

        return response

app.add_middleware(GracefulShutdownMiddleware)
```

## Gunicorn + Uvicorn Configuration

### gunicorn.conf.py

```python
import multiprocessing

# Worker configuration
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# Binding
bind = "0.0.0.0:8000"
backlog = 2048

# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 5

# Limits
max_requests = 10000
max_requests_jitter = 1000

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "fastapi-app"

# Hooks
def on_starting(server):
    pass

def on_exit(server):
    pass

def pre_fork(server, worker):
    pass

def post_fork(server, worker):
    pass

def worker_exit(server, worker):
    pass
```

### Run Command

```bash
gunicorn main:app -c gunicorn.conf.py
```

## Docker Multi-Stage Build

### Dockerfile

```dockerfile
# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production stage
FROM python:3.12-slim as production

WORKDIR /app

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health/live')"

# Run
EXPOSE 8000
CMD ["gunicorn", "main:app", "-c", "gunicorn.conf.py"]
```

### docker-compose.yml

```yaml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/app
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d app"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## Kubernetes Deployment

### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  labels:
    app: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
        - name: api
          image: myregistry/fastapi-app:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: database-url
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /health/startup
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 30  # Allow 2.5 min startup
      terminationGracePeriodSeconds: 30
```

### service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-app
spec:
  selector:
    app: fastapi-app
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
```

## HPA/KEDA Autoscaling

### HPA Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
```

### KEDA for Custom Metrics

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: fastapi-app-scaler
spec:
  scaleTargetRef:
    name: fastapi-app
  minReplicaCount: 2
  maxReplicaCount: 20
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        metricName: http_requests_per_second
        query: sum(rate(http_requests_total{app="fastapi-app"}[1m]))
        threshold: "100"
```

## Environment Configuration

### pydantic-settings

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "FastAPI App"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # Database
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str
    access_token_expire_minutes: int = 30

    # Observability
    sentry_dsn: str | None = None
    otlp_endpoint: str | None = None

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### 12-Factor Configuration

```python
# All config from environment (12-factor app)
import os

class Config:
    # Required (will fail if not set)
    DATABASE_URL = os.environ["DATABASE_URL"]
    SECRET_KEY = os.environ["SECRET_KEY"]

    # Optional with defaults
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    PORT = int(os.getenv("PORT", "8000"))
    WORKERS = int(os.getenv("WORKERS", "4"))

    # Feature flags
    FEATURE_NEW_CHECKOUT = os.getenv("FEATURE_NEW_CHECKOUT", "false").lower() == "true"
```

## Required Packages

```bash
pip install gunicorn uvicorn[standard]
pip install pydantic-settings
```