# API Lifecycle Management

## Versioning Strategies

### URL-Based Versioning (Recommended)

```python
from fastapi import APIRouter, FastAPI

app = FastAPI()

# Version 1
v1_router = APIRouter(prefix="/api/v1")

@v1_router.get("/users/{user_id}")
async def get_user_v1(user_id: int):
    return {"id": user_id, "name": "John"}

# Version 2 with breaking changes
v2_router = APIRouter(prefix="/api/v2")

@v2_router.get("/users/{user_id}")
async def get_user_v2(user_id: int):
    return {
        "id": user_id,
        "profile": {"name": "John", "avatar": None}  # New structure
    }

app.include_router(v1_router)
app.include_router(v2_router)
```

### Header-Based Versioning

```python
from fastapi import Header, HTTPException

async def get_api_version(
    accept: str = Header(default="application/vnd.myapi.v2+json")
) -> int:
    """Extract API version from Accept header."""
    # Parse: application/vnd.myapi.v{N}+json
    if "v1" in accept:
        return 1
    elif "v2" in accept:
        return 2
    return 2  # Default to latest

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    version: int = Depends(get_api_version)
):
    if version == 1:
        return {"id": user_id, "name": "John"}
    else:
        return {"id": user_id, "profile": {"name": "John"}}
```

### Versioning Best Practices

| Approach | Pros | Cons | Use When |
|----------|------|------|----------|
| URL `/v1/` | Clear, cacheable, easy routing | URL pollution | Public APIs |
| Header `Accept` | Clean URLs | Harder to test | Internal APIs |
| Query `?version=1` | Simple | Not RESTful | Quick prototypes |

## Deprecation

### Deprecation Headers

```python
from fastapi import Response
from datetime import datetime, timedelta

class DeprecationMiddleware:
    DEPRECATED_ENDPOINTS = {
        "/api/v1/users": {
            "sunset": datetime(2024, 6, 1),
            "successor": "/api/v2/users"
        }
    }

    async def __call__(self, request, call_next):
        response = await call_next(request)

        path = request.url.path
        if path in self.DEPRECATED_ENDPOINTS:
            info = self.DEPRECATED_ENDPOINTS[path]
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = info["sunset"].strftime("%a, %d %b %Y %H:%M:%S GMT")
            response.headers["Link"] = f'<{info["successor"]}>; rel="successor-version"'

        return response

app.add_middleware(DeprecationMiddleware)
```

### Deprecation Decorator

```python
import warnings
from functools import wraps

def deprecated(
    message: str = None,
    successor: str = None,
    sunset_date: str = None
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)

            # Log usage of deprecated endpoint
            logger.warning(
                "Deprecated endpoint called",
                endpoint=func.__name__,
                sunset=sunset_date
            )

            return response

        # Mark in OpenAPI
        wrapper.__doc__ = f"**DEPRECATED**: {message or 'This endpoint is deprecated.'}"
        if successor:
            wrapper.__doc__ += f" Use `{successor}` instead."

        return wrapper
    return decorator

@router.get("/old-endpoint")
@deprecated(
    message="This endpoint will be removed",
    successor="/api/v2/new-endpoint",
    sunset_date="2024-06-01"
)
async def old_endpoint():
    ...
```

## OpenAPI Customization

### Custom Schema

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="My API",
        version="2.0.0",
        description="Production API with versioning",
        routes=app.routes,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }

    # Global security
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Server info
    openapi_schema["servers"] = [
        {"url": "https://api.example.com", "description": "Production"},
        {"url": "https://staging-api.example.com", "description": "Staging"},
    ]

    # Contact info
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "email": "api@example.com",
        "url": "https://example.com/support"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Response Examples

```python
from pydantic import BaseModel, Field

class UserResponse(BaseModel):
    id: int = Field(..., example=123)
    email: str = Field(..., example="user@example.com")
    name: str = Field(..., example="John Doe")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 123,
                    "email": "john@example.com",
                    "name": "John Doe"
                }
            ]
        }
    }

class ErrorResponse(BaseModel):
    error: dict = Field(
        ...,
        example={"code": "NOT_FOUND", "message": "Resource not found"}
    )

@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_user(user_id: int):
    ...
```

### Tags and Grouping

```python
from fastapi import FastAPI

app = FastAPI(
    openapi_tags=[
        {
            "name": "Users",
            "description": "User management operations",
            "externalDocs": {
                "description": "User guide",
                "url": "https://docs.example.com/users"
            }
        },
        {
            "name": "Orders",
            "description": "Order processing"
        },
        {
            "name": "Admin",
            "description": "Administrative operations (requires admin role)"
        }
    ]
)

@router.get("/users", tags=["Users"])
async def list_users():
    ...

@router.get("/admin/users", tags=["Admin"])
async def admin_list_users():
    ...
```

## Changelog Generation

### Automated Changelog

```python
# changelog.py
from datetime import datetime
from pydantic import BaseModel

class ChangelogEntry(BaseModel):
    version: str
    date: str
    changes: list[str]
    breaking: list[str] = []
    deprecated: list[str] = []

CHANGELOG = [
    ChangelogEntry(
        version="2.1.0",
        date="2024-01-15",
        changes=[
            "Added pagination to /users endpoint",
            "Improved error messages"
        ],
        deprecated=[
            "/api/v1/users - use /api/v2/users instead"
        ]
    ),
    ChangelogEntry(
        version="2.0.0",
        date="2024-01-01",
        changes=[
            "Restructured user response format"
        ],
        breaking=[
            "User response now uses nested profile object"
        ]
    )
]

@router.get("/changelog")
async def get_changelog():
    return CHANGELOG
```

### OpenAPI Changelog Extension

```python
def custom_openapi():
    schema = get_openapi(...)

    schema["info"]["x-changelog"] = [
        {
            "version": "2.1.0",
            "date": "2024-01-15",
            "summary": "Pagination and error improvements"
        }
    ]

    return schema
```

## SDK Generation Hints

### OpenAPI Extensions for Codegen

```python
from pydantic import BaseModel, Field

class CreateUserRequest(BaseModel):
    """
    Request to create a new user.

    x-codegen-request-body-name: user
    """
    email: str = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")

@router.post(
    "/users",
    operation_id="createUser",  # SDK method name
    summary="Create a new user",
    response_model=UserResponse,
)
async def create_user(user: CreateUserRequest):
    """
    Create a new user account.

    This endpoint creates a new user and returns the created user object.
    """
    ...
```

### Client Generation

```bash
# Generate TypeScript client
npx @openapitools/openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-fetch \
  -o ./sdk/typescript

# Generate Python client
openapi-generator generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./sdk/python
```

## Documentation Best Practices

### Hide Internal Endpoints

```python
from fastapi import FastAPI

app = FastAPI(
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Or expose only on specific paths
@router.get("/internal/health", include_in_schema=False)
async def internal_health():
    ...
```

### Documentation-First Development

```yaml
# openapi-spec.yaml (design first)
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0

paths:
  /users:
    get:
      operationId: listUsers
      summary: List all users
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        200:
          description: List of users
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
```

```python
# Validate implementation matches spec
from openapi_spec_validator import validate_spec
import yaml

with open("openapi-spec.yaml") as f:
    spec = yaml.safe_load(f)
    validate_spec(spec)
```

## Required Packages

```bash
pip install pyyaml openapi-spec-validator
# For SDK generation: npm install @openapitools/openapi-generator-cli
```