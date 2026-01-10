# API Design Standards

Production-grade API design patterns for REST and RPC.

## HTTP Standards

### Status Codes

| Code | Use Case | When to Use |
|------|----------|-------------|
| 200 | Success | GET, PUT, PATCH returns data |
| 201 | Created | POST creates resource |
| 204 | No Content | DELETE, PUT with no response body |
| 400 | Bad Request | Validation failed, malformed input |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate, version mismatch |
| 422 | Unprocessable | Valid syntax but semantic error |
| 429 | Too Many Requests | Rate limited |
| 500 | Internal Error | Unexpected server error |

### Resource Naming

```
# GOOD: Plural nouns, hierarchical
GET  /users
GET  /users/{id}
GET  /users/{id}/orders
POST /users/{id}/orders

# BAD
GET  /getUser          # Verb in path
GET  /user/{id}        # Singular
POST /createOrder      # Verb in path
GET  /users/orders     # Non-hierarchical
```

### Query Parameters

```
# Filtering
GET /users?status=active&role=admin

# Pagination
GET /users?page=2&limit=20
GET /users?cursor=abc123&limit=20  # Cursor-based (preferred)

# Sorting
GET /users?sort=created_at:desc,name:asc

# Field selection
GET /users?fields=id,name,email
```

## Error Response Format (RFC 7807)

### Standard Structure

```typescript
interface ApiError {
    type: string;        // URI reference identifying error type
    title: string;       // Short human-readable summary
    status: number;      // HTTP status code
    detail?: string;     // Human-readable explanation
    instance?: string;   // URI reference to specific occurrence
    errors?: FieldError[]; // Validation errors
}

interface FieldError {
    field: string;
    message: string;
    code: string;
}
```

### Examples

```json
// Validation Error (400)
{
    "type": "https://api.example.com/errors/validation",
    "title": "Validation Failed",
    "status": 400,
    "detail": "One or more fields failed validation",
    "errors": [
        { "field": "email", "message": "Invalid email format", "code": "INVALID_FORMAT" },
        { "field": "age", "message": "Must be at least 18", "code": "MIN_VALUE" }
    ]
}

// Not Found (404)
{
    "type": "https://api.example.com/errors/not-found",
    "title": "Resource Not Found",
    "status": 404,
    "detail": "User with ID '123' was not found"
}

// Rate Limited (429)
{
    "type": "https://api.example.com/errors/rate-limited",
    "title": "Too Many Requests",
    "status": 429,
    "detail": "Rate limit exceeded. Try again in 60 seconds",
    "retryAfter": 60
}
```

### Implementation

```typescript
// TypeScript
class ApiError extends Error {
    constructor(
        public status: number,
        public type: string,
        public title: string,
        public detail?: string,
        public errors?: FieldError[]
    ) {
        super(title);
    }

    toJSON(): object {
        return {
            type: this.type,
            title: this.title,
            status: this.status,
            detail: this.detail,
            errors: this.errors,
        };
    }
}

// Usage
throw new ApiError(
    400,
    '/errors/validation',
    'Validation Failed',
    'Email is invalid',
    [{ field: 'email', message: 'Invalid format', code: 'INVALID_FORMAT' }]
);
```

```python
# Python
from dataclasses import dataclass
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@dataclass
class ApiError:
    type: str
    title: str
    status: int
    detail: str | None = None
    errors: list[dict] | None = None

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status,
            content={
                "type": self.type,
                "title": self.title,
                "status": self.status,
                "detail": self.detail,
                "errors": self.errors,
            }
        )
```

```go
// Go
type APIError struct {
    Type   string       `json:"type"`
    Title  string       `json:"title"`
    Status int          `json:"status"`
    Detail string       `json:"detail,omitempty"`
    Errors []FieldError `json:"errors,omitempty"`
}

func (e *APIError) Error() string {
    return e.Title
}

func NewValidationError(errors []FieldError) *APIError {
    return &APIError{
        Type:   "/errors/validation",
        Title:  "Validation Failed",
        Status: 400,
        Errors: errors,
    }
}
```

## API Versioning

### Strategies

| Strategy | Pros | Cons |
|----------|------|------|
| URL Path (`/v1/users`) | Clear, easy routing | URL pollution |
| Header (`Accept-Version: 1`) | Clean URLs | Hidden versioning |
| Query (`?version=1`) | Easy to add | Often forgotten |

**Recommendation**: URL path for major versions, header for minor.

### Breaking vs Non-Breaking Changes

**Non-Breaking (Safe)**:
- Adding new optional fields
- Adding new endpoints
- Adding new enum values (if clients ignore unknowns)

**Breaking (Requires New Version)**:
- Removing fields
- Renaming fields
- Changing field types
- Changing required/optional status
- Removing endpoints

### Deprecation

```typescript
// Response header
res.setHeader('Deprecation', 'true');
res.setHeader('Sunset', 'Sat, 31 Dec 2025 23:59:59 GMT');
res.setHeader('Link', '</v2/users>; rel="successor-version"');

// Response body (optional warning)
{
    "data": { ... },
    "_deprecation": {
        "message": "This endpoint is deprecated. Use /v2/users instead.",
        "sunset": "2025-12-31"
    }
}
```

## Input Validation

### Validate at the Edge

```typescript
// GOOD: Validate at API boundary
router.post('/users', async (req, res) => {
    const input = UserCreateSchema.parse(req.body);  // Throws on invalid
    const user = await userService.create(input);    // Service receives validated data
    res.status(201).json(user);
});

// BAD: Validate deep in service
router.post('/users', async (req, res) => {
    const user = await userService.create(req.body);  // Service must validate
    res.status(201).json(user);
});
```

### Schema Examples

```typescript
// TypeScript (Zod)
const UserCreateSchema = z.object({
    email: z.string().email().max(255),
    name: z.string().min(1).max(100),
    age: z.number().int().min(0).max(150).optional(),
    role: z.enum(['user', 'admin']).default('user'),
});

type UserCreate = z.infer<typeof UserCreateSchema>;
```

```python
# Python (Pydantic)
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=150)
    role: Literal['user', 'admin'] = 'user'
```

## Request/Response Patterns

### Consistent Envelope (Optional)

```typescript
// Success response
{
    "data": { "id": "123", "name": "John" },
    "meta": {
        "requestId": "req-abc123",
        "timestamp": "2024-01-15T10:30:00Z"
    }
}

// List response with pagination
{
    "data": [{ ... }, { ... }],
    "meta": {
        "total": 100,
        "page": 1,
        "limit": 20,
        "hasMore": true
    }
}
```

### Idempotency

```typescript
// Client sends idempotency key
POST /orders
Headers:
    Idempotency-Key: unique-request-id-123

// Server stores result, returns same response on retry
```

## Rate Limiting

### Response Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312200
Retry-After: 60  # Only on 429
```

### Implementation

```typescript
// Express middleware
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req, res) => {
        res.status(429).json({
            type: '/errors/rate-limited',
            title: 'Too Many Requests',
            status: 429,
            detail: `Rate limit exceeded. Try again in ${res.getHeader('Retry-After')} seconds`,
        });
    },
});
```

## Anti-Patterns

| Bad | Good | Why |
|-----|------|-----|
| Return 200 for errors | Use proper status codes | Client can't distinguish |
| Different error formats | RFC 7807 everywhere | Inconsistent parsing |
| No input validation | Validate at edge | Security, data integrity |
| Expose internal errors | Generic 500 message | Security |
| No pagination | Always paginate lists | Memory, performance |
| Sync long operations | Return 202, use webhooks | Timeout issues |