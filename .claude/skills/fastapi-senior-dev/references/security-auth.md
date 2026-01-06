# Authentication & Authorization

## OAuth2 Flows

### Authorization Code + PKCE (PRIMARY)

Use for SPAs, mobile apps, and modern web applications.

```python
import secrets
import hashlib
import base64
from urllib.parse import urlencode

# Step 1: Generate PKCE challenge (client-side)
def generate_pkce():
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return code_verifier, code_challenge

# Step 2: Authorization endpoint
@router.get("/auth/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    code_challenge_method: str = "S256",
    state: str = None,
):
    # Validate client and redirect_uri
    client = await get_client(client_id)
    if redirect_uri not in client.allowed_redirect_uris:
        raise HTTPException(400, "Invalid redirect_uri")

    # Store authorization request
    auth_code = secrets.token_urlsafe(32)
    await redis.setex(
        f"auth_code:{auth_code}",
        600,  # 10 min expiry
        json.dumps({
            "client_id": client_id,
            "code_challenge": code_challenge,
            "redirect_uri": redirect_uri,
        })
    )

    # Redirect to login page with auth_code
    return RedirectResponse(f"/login?code={auth_code}&state={state}")

# Step 3: Token endpoint
@router.post("/auth/token")
async def token(
    grant_type: str = Form(...),
    code: str = Form(None),
    code_verifier: str = Form(None),
    redirect_uri: str = Form(None),
    refresh_token: str = Form(None),
):
    if grant_type == "authorization_code":
        # Retrieve stored auth request
        auth_data = await redis.get(f"auth_code:{code}")
        if not auth_data:
            raise HTTPException(400, "Invalid code")

        auth = json.loads(auth_data)
        await redis.delete(f"auth_code:{code}")

        # Verify PKCE
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b"=").decode()

        if expected_challenge != auth["code_challenge"]:
            raise HTTPException(400, "Invalid code_verifier")

        # Issue tokens
        return await create_tokens(auth["user_id"])

    elif grant_type == "refresh_token":
        return await refresh_access_token(refresh_token)
```

### OAuth2 Password Flow (Legacy Only)

Only use for internal tools or legacy system migration.

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

@router.post("/auth/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    return await create_tokens(user.id)
```

## JWT Implementation with PyJWT

### Token Generation

```python
import jwt
from datetime import datetime, timedelta
from pydantic_settings import BaseSettings

class AuthSettings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

settings = AuthSettings()

def create_access_token(user_id: int, scopes: list[str] = None) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
        "scopes": scopes or [],
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),  # Unique token ID for blacklisting
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

async def create_tokens(user_id: int) -> dict:
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }
```

### Token Verification

```python
from jwt import PyJWTError, ExpiredSignatureError

def verify_token(token: str, token_type: str = "access") -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        if payload.get("type") != token_type:
            raise HTTPException(401, "Invalid token type")

        return payload

    except ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except PyJWTError:
        raise HTTPException(401, "Invalid token")
```

### Token Blacklisting (Redis)

```python
class TokenBlacklist:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def blacklist(self, token: str):
        """Blacklist a token until its expiry."""
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = datetime.fromtimestamp(payload["exp"])
        ttl = int((exp - datetime.utcnow()).total_seconds())

        if ttl > 0:
            jti = payload.get("jti", token[:32])
            await self.redis.setex(f"blacklist:{jti}", ttl, "1")

    async def is_blacklisted(self, token: str) -> bool:
        payload = jwt.decode(token, options={"verify_signature": False})
        jti = payload.get("jti", token[:32])
        return await self.redis.exists(f"blacklist:{jti}")

# Logout endpoint
@router.post("/auth/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    blacklist: TokenBlacklist = Depends(get_blacklist)
):
    await blacklist.blacklist(token)
    return {"message": "Logged out"}
```

### Refresh Token in HttpOnly Cookie

```python
from fastapi.responses import JSONResponse

@router.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    tokens = await create_tokens(user.id)

    response = JSONResponse({
        "access_token": tokens["access_token"],
        "token_type": "bearer"
    })

    # Set refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,  # HTTPS only
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/auth/refresh"  # Only sent to refresh endpoint
    )

    return response

@router.post("/auth/refresh")
async def refresh(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, "No refresh token")

    payload = verify_token(refresh_token, token_type="refresh")
    return await create_tokens(int(payload["sub"]))
```

## Scopes & RBAC

### Scope-Based Authorization

```python
from fastapi.security import SecurityScopes

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = verify_token(token)
    token_scopes = payload.get("scopes", [])

    # Check required scopes
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                403,
                detail=f"Missing scope: {scope}",
                headers={"WWW-Authenticate": f'Bearer scope="{scope}"'}
            )

    user = await db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(401, "User not found")

    return user

# Usage with scopes
@router.get("/admin/users")
async def list_users(
    user: User = Security(get_current_user, scopes=["admin:read"])
):
    ...

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    user: User = Security(get_current_user, scopes=["admin:write"])
):
    ...
```

### Role Hierarchy

```python
from enum import Enum

class Role(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"

ROLE_HIERARCHY = {
    Role.USER: [],
    Role.MODERATOR: [Role.USER],
    Role.ADMIN: [Role.MODERATOR, Role.USER],
    Role.SUPERADMIN: [Role.ADMIN, Role.MODERATOR, Role.USER],
}

def has_role(user_role: Role, required_role: Role) -> bool:
    if user_role == required_role:
        return True
    return required_role in ROLE_HIERARCHY.get(user_role, [])

def require_role(role: Role):
    async def dependency(user: User = Depends(get_current_user)):
        if not has_role(user.role, role):
            raise HTTPException(403, f"Role {role} required")
        return user
    return dependency

# Usage
@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    user: User = Depends(require_role(Role.MODERATOR))
):
    ...
```

### Row-Level Security

```python
class PostService:
    async def get_visible_posts(
        self,
        db: AsyncSession,
        user: User
    ) -> list[Post]:
        """Return posts user is allowed to see."""
        stmt = select(Post)

        if user.role == Role.ADMIN:
            pass  # See all posts
        elif user.role == Role.MODERATOR:
            stmt = stmt.where(
                or_(Post.is_published == True, Post.author_id == user.id)
            )
        else:
            stmt = stmt.where(
                and_(Post.is_published == True, Post.is_deleted == False)
            )

        result = await db.execute(stmt)
        return result.scalars().all()
```

## OIDC Integration

### Keycloak/Auth0 Pattern

```python
import httpx
from jose import jwt as jose_jwt  # For JWKS validation

class OIDCProvider:
    def __init__(self, issuer: str, client_id: str):
        self.issuer = issuer
        self.client_id = client_id
        self._jwks = None

    async def get_jwks(self) -> dict:
        if self._jwks:
            return self._jwks

        async with httpx.AsyncClient() as client:
            discovery = await client.get(f"{self.issuer}/.well-known/openid-configuration")
            jwks_uri = discovery.json()["jwks_uri"]

            jwks_response = await client.get(jwks_uri)
            self._jwks = jwks_response.json()

        return self._jwks

    async def verify_token(self, token: str) -> dict:
        jwks = await self.get_jwks()

        payload = jose_jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=self.client_id,
            issuer=self.issuer
        )

        return payload

oidc = OIDCProvider(
    issuer="https://auth.example.com/realms/myapp",
    client_id="my-api"
)

async def get_oidc_user(token: str = Depends(oauth2_scheme)) -> dict:
    return await oidc.verify_token(token)
```

## API Key Authentication

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

class APIKeyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate(self, api_key: str) -> APIKey | None:
        # Hash the key for lookup
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        result = await self.db.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True,
                or_(APIKey.expires_at == None, APIKey.expires_at > datetime.utcnow())
            )
        )
        api_key_obj = result.scalar_one_or_none()

        if api_key_obj:
            # Track usage
            api_key_obj.last_used_at = datetime.utcnow()
            api_key_obj.usage_count += 1
            await self.db.commit()

        return api_key_obj

async def get_api_key(
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    service = APIKeyService(db)
    key = await service.validate(api_key)
    if not key:
        raise HTTPException(401, "Invalid API key")
    return key

# Usage
@router.get("/api/data")
async def get_data(api_key: APIKey = Depends(get_api_key)):
    ...
```

## Multi-Tenancy

### Tenant Isolation

```python
from contextvars import ContextVar

current_tenant: ContextVar[str] = ContextVar("current_tenant")

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from subdomain or header
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            host = request.headers.get("host", "")
            tenant_id = host.split(".")[0]

        if not await self.validate_tenant(tenant_id):
            return JSONResponse({"error": "Invalid tenant"}, status_code=400)

        current_tenant.set(tenant_id)
        return await call_next(request)

# Tenant-aware queries
async def get_tenant_db() -> AsyncGenerator[AsyncSession, None]:
    tenant_id = current_tenant.get()

    async with async_session() as session:
        # Set row-level security context
        await session.execute(text(f"SET app.current_tenant = '{tenant_id}'"))
        yield session
```

## Required Packages

```bash
pip install PyJWT passlib[bcrypt] python-multipart
pip install python-jose[cryptography]  # For OIDC JWKS
```
