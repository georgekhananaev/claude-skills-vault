# Redis Caching & Pub/Sub

## Connection Setup

```python
from redis.asyncio import Redis, ConnectionPool
from pydantic_settings import BaseSettings

class RedisSettings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10

settings = RedisSettings()

# Connection pool (reuse connections)
pool = ConnectionPool.from_url(
    settings.redis_url,
    max_connections=settings.redis_pool_size,
    decode_responses=True,  # Auto-decode to str
)

async def get_redis() -> Redis:
    return Redis(connection_pool=pool)

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown():
    await pool.disconnect()
```

## Caching Patterns

### Cache-Aside Pattern

```python
from typing import TypeVar, Callable
import json

T = TypeVar("T")

class CacheService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], T],
        ttl: int = 300,  # 5 minutes
        model: type[T] | None = None
    ) -> T:
        # Try cache first
        cached = await self.redis.get(key)
        if cached:
            if model:
                return model.model_validate_json(cached)
            return json.loads(cached)

        # Cache miss - fetch from source
        value = await factory()

        # Store in cache
        if hasattr(value, "model_dump_json"):
            await self.redis.setex(key, ttl, value.model_dump_json())
        else:
            await self.redis.setex(key, ttl, json.dumps(value))

        return value

# Usage
cache = CacheService(redis)

async def get_user(user_id: int) -> User:
    return await cache.get_or_set(
        key=f"user:{user_id}",
        factory=lambda: db.get(User, user_id),
        ttl=300,
        model=User
    )
```

### Cache Invalidation

```python
class UserService:
    def __init__(self, db: AsyncSession, cache: Redis):
        self.db = db
        self.cache = cache

    async def update(self, user_id: int, data: UserUpdate) -> User:
        user = await self.db.get(User, user_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        await self.db.commit()

        # Invalidate cache
        await self.cache.delete(f"user:{user_id}")
        await self.cache.delete(f"user:email:{user.email}")

        return user

    async def delete(self, user_id: int):
        user = await self.db.get(User, user_id)
        await self.db.delete(user)
        await self.db.commit()

        # Pattern delete (all user-related keys)
        async for key in self.cache.scan_iter(f"user:{user_id}:*"):
            await self.cache.delete(key)
```

### Decorator Pattern

```python
from functools import wraps
import hashlib

def cached(ttl: int = 300, prefix: str = "cache"):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            key_data = f"{func.__name__}:{args}:{kwargs}"
            cache_key = f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"

            redis = await get_redis()

            # Try cache
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await redis.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

# Usage
@cached(ttl=600, prefix="stats")
async def get_dashboard_stats(user_id: int) -> dict:
    # Expensive computation
    ...
```

## Distributed Locks

```python
from redis.asyncio.lock import Lock
from contextlib import asynccontextmanager

@asynccontextmanager
async def distributed_lock(
    redis: Redis,
    name: str,
    timeout: float = 10.0,
    blocking_timeout: float = 5.0
):
    """Acquire distributed lock with automatic release."""
    lock = Lock(
        redis,
        name=f"lock:{name}",
        timeout=timeout,
        blocking_timeout=blocking_timeout,
    )

    acquired = await lock.acquire()
    if not acquired:
        raise LockError(f"Could not acquire lock: {name}")

    try:
        yield lock
    finally:
        await lock.release()

# Usage: Prevent concurrent processing
async def process_order(order_id: int):
    async with distributed_lock(redis, f"order:{order_id}"):
        # Only one instance can process this order
        order = await order_service.get(order_id)
        await order_service.process(order)
```

## Pub/Sub Patterns

### Publisher

```python
class EventPublisher:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def publish(self, channel: str, event: dict):
        await self.redis.publish(channel, json.dumps(event))

    async def publish_user_event(self, event_type: str, user_id: int, data: dict):
        await self.publish(
            f"users:{user_id}",
            {"type": event_type, "user_id": user_id, "data": data}
        )

# Usage
publisher = EventPublisher(redis)
await publisher.publish_user_event("order_created", user_id, {"order_id": 123})
```

### Subscriber

```python
class EventSubscriber:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.pubsub = redis.pubsub()
        self.handlers: dict[str, Callable] = {}

    def on(self, pattern: str):
        def decorator(func):
            self.handlers[pattern] = func
            return func
        return decorator

    async def start(self):
        await self.pubsub.psubscribe(*self.handlers.keys())

        async for message in self.pubsub.listen():
            if message["type"] == "pmessage":
                pattern = message["pattern"].decode()
                handler = self.handlers.get(pattern)
                if handler:
                    data = json.loads(message["data"])
                    await handler(data)

# Usage
subscriber = EventSubscriber(redis)

@subscriber.on("users:*")
async def handle_user_event(event: dict):
    if event["type"] == "order_created":
        await notification_service.notify(event["user_id"], "New order!")

# Start in background
asyncio.create_task(subscriber.start())
```

## Session Storage

```python
from uuid import uuid4
import json

class SessionStore:
    def __init__(self, redis: Redis, prefix: str = "session", ttl: int = 3600):
        self.redis = redis
        self.prefix = prefix
        self.ttl = ttl

    def _key(self, session_id: str) -> str:
        return f"{self.prefix}:{session_id}"

    async def create(self, data: dict) -> str:
        session_id = str(uuid4())
        await self.redis.setex(
            self._key(session_id),
            self.ttl,
            json.dumps(data)
        )
        return session_id

    async def get(self, session_id: str) -> dict | None:
        data = await self.redis.get(self._key(session_id))
        if data:
            # Refresh TTL on access
            await self.redis.expire(self._key(session_id), self.ttl)
            return json.loads(data)
        return None

    async def update(self, session_id: str, data: dict):
        await self.redis.setex(self._key(session_id), self.ttl, json.dumps(data))

    async def delete(self, session_id: str):
        await self.redis.delete(self._key(session_id))

# FastAPI middleware
@app.middleware("http")
async def session_middleware(request: Request, call_next):
    session_id = request.cookies.get("session_id")

    if session_id:
        request.state.session = await session_store.get(session_id)
    else:
        request.state.session = None

    response = await call_next(request)
    return response
```

## Rate Limiting with Redis

```python
from datetime import datetime

class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int  # seconds
    ) -> tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, remaining)."""
        now = datetime.utcnow().timestamp()
        window_start = now - window

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
        pipe.zadd(key, {str(now): now})  # Add current request
        pipe.zcard(key)  # Count requests in window
        pipe.expire(key, window)  # Set TTL

        results = await pipe.execute()
        count = results[2]

        return count <= limit, max(0, limit - count)

# Usage in dependency
async def rate_limit(
    request: Request,
    redis: Redis = Depends(get_redis)
):
    limiter = RateLimiter(redis)
    key = f"rate:{request.client.host}:{request.url.path}"

    allowed, remaining = await limiter.is_allowed(key, limit=100, window=60)

    if not allowed:
        raise HTTPException(429, "Rate limit exceeded")

    return remaining
```

## Required Packages

```bash
pip install redis[hiredis]  # hiredis for performance
```