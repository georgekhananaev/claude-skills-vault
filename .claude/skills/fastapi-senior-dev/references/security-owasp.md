# OWASP Security Compliance

## Injection Prevention

### SQL Injection

Always use parameterized queries via SQLAlchemy ORM.

```python
# WRONG: String interpolation
query = f"SELECT * FROM users WHERE email = '{email}'"

# RIGHT: Parameterized query
stmt = select(User).where(User.email == email)

# RIGHT: Raw SQL with parameters
stmt = text("SELECT * FROM users WHERE email = :email")
result = await db.execute(stmt, {"email": email})
```

### NoSQL Injection

Use Beanie ODM query builders, never raw dicts from user input.

```python
# WRONG: Unsanitized user input
query = {"$where": user_input}

# RIGHT: Use ODM operators
from beanie.odm.operators.find.comparison import Eq
users = await User.find(Eq(User.email, email)).to_list()
```

### Command Injection

Never construct shell commands from user input.

```python
# WRONG
os.system(f"convert {user_filename} output.png")

# RIGHT: Use subprocess with list args
import subprocess
subprocess.run(
    ["convert", validated_filename, "output.png"],
    capture_output=True,
    timeout=30
)
```

## Input Validation

### Pydantic Validation

```python
from pydantic import BaseModel, Field, field_validator
import re

class UserCreate(BaseModel):
    email: str = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")
        return v
```

### Path Traversal Prevention

```python
from pathlib import Path

UPLOAD_DIR = Path("/app/uploads")

def safe_file_path(filename: str) -> Path:
    """Prevent path traversal attacks."""
    # Remove any path components
    safe_name = Path(filename).name

    # Additional sanitization
    safe_name = re.sub(r'[^\w\-_.]', '_', safe_name)

    full_path = UPLOAD_DIR / safe_name

    # Ensure path is within upload directory
    if not full_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
        raise ValueError("Invalid filename")

    return full_path
```

## XSS Prevention

### Response Headers

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )

        return response

app.add_middleware(SecurityHeadersMiddleware)
```

### HTML Escaping

```python
from markupsafe import escape

def render_user_content(content: str) -> str:
    """Escape user content before rendering."""
    return escape(content)
```

## CSRF Protection

### SameSite Cookies

```python
response.set_cookie(
    key="session_id",
    value=session_id,
    httponly=True,
    secure=True,  # HTTPS only
    samesite="strict",  # Prevents CSRF
)
```

### CSRF Tokens for Forms

```python
import secrets

class CSRFProtection:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def generate_token(self, session_id: str) -> str:
        token = secrets.token_urlsafe(32)
        await self.redis.setex(f"csrf:{session_id}", 3600, token)
        return token

    async def validate_token(self, session_id: str, token: str) -> bool:
        stored = await self.redis.get(f"csrf:{session_id}")
        return secrets.compare_digest(stored or "", token)

# Dependency
async def verify_csrf(
    request: Request,
    csrf_token: str = Form(...),
    csrf: CSRFProtection = Depends(get_csrf)
):
    session_id = request.cookies.get("session_id")
    if not await csrf.validate_token(session_id, csrf_token):
        raise HTTPException(403, "Invalid CSRF token")
```

## Rate Limiting

### Per-Endpoint Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/auth/login")
@limiter.limit("5/minute")  # Strict for auth
async def login(request: Request):
    ...

@router.get("/api/data")
@limiter.limit("100/minute")  # Relaxed for API
async def get_data(request: Request):
    ...
```

### Distributed Rate Limiting (Redis)

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.on_event("startup")
async def startup():
    await FastAPILimiter.init(redis)

@router.get("/api/resource")
async def resource(
    _: None = Depends(RateLimiter(times=10, seconds=60))
):
    ...
```

## Request Body Limits

### DoS Protection

```python
from starlette.middleware.base import BaseHTTPMiddleware

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = 1024 * 1024):  # 1MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")

        if content_length:
            if int(content_length) > self.max_size:
                return JSONResponse(
                    {"error": "Request too large"},
                    status_code=413
                )

        return await call_next(request)

app.add_middleware(RequestSizeLimitMiddleware, max_size=10 * 1024 * 1024)  # 10MB
```

### File Upload Limits

```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(..., max_length=5 * 1024 * 1024)  # 5MB
):
    # Validate content type
    allowed_types = {"image/jpeg", "image/png", "application/pdf"}
    if file.content_type not in allowed_types:
        raise HTTPException(400, "Invalid file type")

    # Additional size check
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(413, "File too large")

    return {"filename": file.filename, "size": len(contents)}
```

## Audit Logging

```python
import structlog
from datetime import datetime

logger = structlog.get_logger()

class AuditLogger:
    async def log(
        self,
        action: str,
        user_id: int | None,
        resource: str,
        resource_id: str | None,
        details: dict = None,
        request: Request = None
    ):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_id": user_id,
            "resource": resource,
            "resource_id": resource_id,
            "ip_address": request.client.host if request else None,
            "user_agent": request.headers.get("user-agent") if request else None,
            "details": details,
        }

        logger.info("audit", **log_entry)

        # Also store in database for compliance
        await self.db.execute(
            insert(AuditLog).values(**log_entry)
        )

# Usage
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    audit: AuditLogger = Depends(get_audit_logger)
):
    await user_service.delete(user_id)

    await audit.log(
        action="user.deleted",
        user_id=current_user.id,
        resource="user",
        resource_id=str(user_id),
        request=request
    )
```

## Log Sanitization

### Filter Sensitive Data

```python
import structlog
import re

SENSITIVE_KEYS = {"password", "token", "authorization", "api_key", "secret", "credit_card"}
SENSITIVE_PATTERNS = [
    (re.compile(r"Bearer\s+[\w\-\.]+"), "Bearer [REDACTED]"),
    (re.compile(r"\b\d{16}\b"), "[CARD_REDACTED]"),
]

def sanitize_value(key: str, value: any) -> any:
    """Sanitize sensitive values in logs."""
    if isinstance(value, dict):
        return {k: sanitize_value(k, v) for k, v in value.items()}

    if isinstance(value, str):
        if key.lower() in SENSITIVE_KEYS:
            return "[REDACTED]"

        for pattern, replacement in SENSITIVE_PATTERNS:
            value = pattern.sub(replacement, value)

    return value

def sanitize_processor(logger, method_name, event_dict):
    """Structlog processor to sanitize sensitive data."""
    return {k: sanitize_value(k, v) for k, v in event_dict.items()}

structlog.configure(
    processors=[
        sanitize_processor,
        structlog.processors.JSONRenderer(),
    ]
)
```

## Secrets Management

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Required secrets (no defaults)
    secret_key: str
    database_url: str

    # Optional with secure defaults
    debug: bool = False

# NEVER do this:
# SECRET_KEY = "hardcoded-secret"  # WRONG

# Always load from environment:
# SECRET_KEY=your-secret-here in .env or environment
```

## Dependency Scanning

### CI Pipeline Integration

```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install dependencies
        run: pip install pip-audit safety

      - name: Run pip-audit
        run: pip-audit --require-hashes --strict

      - name: Run safety check
        run: safety check --full-report
```

### Local Scanning

```bash
# Install
pip install pip-audit safety

# Scan for vulnerabilities
pip-audit

# Check against known CVEs
safety check
```

## Hide Stack Traces in Production

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log full error internally
    logger.exception("Unhandled exception", exc_info=exc, request_id=request.state.request_id)

    # Return generic message to client
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "type": type(exc).__name__}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "An error occurred"}}
        )
```

## Security Checklist

- [ ] All user input validated via Pydantic
- [ ] SQL queries use ORM/parameterized statements
- [ ] Security headers configured (CSP, X-Frame-Options, etc.)
- [ ] Cookies use HttpOnly, Secure, SameSite
- [ ] Rate limiting on auth endpoints
- [ ] Request body size limits configured
- [ ] Sensitive data filtered from logs
- [ ] Secrets loaded from environment (never hardcoded)
- [ ] Dependency scanning in CI pipeline
- [ ] Stack traces hidden in production
- [ ] Audit logging for security-relevant actions
- [ ] CORS configured with specific origins (not `*`)

## Required Packages

```bash
pip install python-multipart slowapi fastapi-limiter
pip install pip-audit safety  # Scanning
pip install structlog  # Logging
```