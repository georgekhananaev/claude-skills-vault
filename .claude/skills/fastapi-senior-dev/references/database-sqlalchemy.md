# SQLAlchemy 2.0 Async Patterns

## Async Engine Setup

### Configuration

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

# Production configuration
engine = create_async_engine(
    settings.db.async_url,
    poolclass=AsyncAdaptedQueuePool,  # NOT QueuePool for async
    pool_size=10,           # Base connections
    max_overflow=20,        # Extra connections under load
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True,     # Validate connections before use
    echo=settings.debug,    # SQL logging in debug mode
)

# For serverless/testing: use NullPool (no connection reuse)
test_engine = create_async_engine(
    test_db_url,
    poolclass=NullPool,  # New connection per request
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent lazy loads after commit
)
```

### Pool Selection Guide

| Pool Type | Use Case |
|-----------|----------|
| `AsyncAdaptedQueuePool` | Production (default) |
| `NullPool` | Serverless, testing, or "another operation in progress" errors |

## Session Management

### Dependency Pattern

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# Usage in routes
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404)
    return user
```

### Transaction Context Manager

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def transaction(session: AsyncSession):
    """Explicit transaction boundary."""
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise

# Usage
async with transaction(db) as tx:
    user = User(email="test@example.com")
    tx.add(user)
    # Auto-commit on exit, rollback on exception
```

### Nested Transactions (Savepoints)

```python
async def transfer_funds(db: AsyncSession, from_id: int, to_id: int, amount: Decimal):
    async with db.begin_nested():  # Creates savepoint
        from_account = await db.get(Account, from_id)
        to_account = await db.get(Account, to_id)

        if from_account.balance < amount:
            raise InsufficientFunds()

        from_account.balance -= amount
        to_account.balance += amount
        # Savepoint released on success, rolled back on exception
```

## Query Patterns

### Basic Queries

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

# Get single record
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()

# Get multiple records
result = await db.execute(select(User).where(User.is_active == True))
users = result.scalars().all()

# Async iteration (memory efficient)
result = await db.stream(select(User))
async for user in result.scalars():
    process(user)
```

### Relationship Loading

```python
# selectinload: Best for one-to-many (separate IN query)
stmt = (
    select(User)
    .options(selectinload(User.orders))
    .where(User.id == user_id)
)

# joinedload: Best for one-to-one/many-to-one (JOIN in same query)
stmt = (
    select(Order)
    .options(joinedload(Order.user))
    .where(Order.id == order_id)
)

# Nested loading
stmt = (
    select(User)
    .options(
        selectinload(User.orders).selectinload(Order.items)
    )
)

# Avoid N+1: Always eager load when iterating
async def list_users_with_orders(db: AsyncSession) -> list[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.orders))
        .where(User.is_active == True)
    )
    return result.scalars().all()
```

### Keyset Pagination (Cursor-based)

```python
from sqlalchemy import and_

async def list_orders_cursor(
    db: AsyncSession,
    limit: int = 20,
    cursor: int | None = None  # Last seen ID
) -> tuple[list[Order], int | None]:
    stmt = select(Order).order_by(Order.id.desc()).limit(limit + 1)

    if cursor:
        stmt = stmt.where(Order.id < cursor)

    result = await db.execute(stmt)
    orders = result.scalars().all()

    # Check if there's a next page
    has_next = len(orders) > limit
    if has_next:
        orders = orders[:limit]

    next_cursor = orders[-1].id if orders and has_next else None
    return orders, next_cursor
```

### Streaming Large Results

```python
async def export_all_users(db: AsyncSession):
    """Stream users without loading all into memory."""
    result = await db.stream(
        select(User)
        .execution_options(yield_per=100)  # Fetch in batches
    )

    async for user in result.scalars():
        yield user.to_csv_row()
```

## Model Patterns

### Base Model with Mixins

```python
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
```

### Hybrid Properties

```python
from sqlalchemy.ext.hybrid import hybrid_property

class User(Base):
    __tablename__ = "users"

    first_name: Mapped[str]
    last_name: Mapped[str]

    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @full_name.expression
    def full_name(cls):
        return cls.first_name + " " + cls.last_name

# Works in queries
stmt = select(User).where(User.full_name == "John Doe")
```

### Event Listeners

```python
from sqlalchemy import event
from sqlalchemy.orm import Session

@event.listens_for(User, "before_insert")
def set_user_defaults(mapper, connection, target):
    if not target.created_at:
        target.created_at = datetime.utcnow()

@event.listens_for(Session, "before_flush")
def audit_changes(session, flush_context, instances):
    for obj in session.dirty:
        if hasattr(obj, "updated_at"):
            obj.updated_at = datetime.utcnow()
```

## Performance

### N+1 Detection

```python
import logging
from sqlalchemy import event

# Log lazy loads (detect N+1 in development)
@event.listens_for(Engine, "before_cursor_execute")
def log_query(conn, cursor, statement, parameters, context, executemany):
    if "SELECT" in statement and logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug(f"SQL: {statement[:100]}...")
```

### Bulk Operations

```python
from sqlalchemy.dialects.postgresql import insert

# Bulk insert with conflict handling
async def upsert_users(db: AsyncSession, users: list[dict]):
    stmt = insert(User).values(users)
    stmt = stmt.on_conflict_do_update(
        index_elements=["email"],
        set_={"name": stmt.excluded.name}
    )
    await db.execute(stmt)
    await db.commit()

# Bulk update
from sqlalchemy import update

await db.execute(
    update(User)
    .where(User.is_active == False)
    .values(deleted_at=datetime.utcnow())
)
```

### Raw asyncpg for Performance

```python
async def bulk_insert_raw(db: AsyncSession, records: list[tuple]):
    """Use raw asyncpg for maximum insert performance."""
    conn = await db.connection()
    raw_conn = await conn.get_raw_connection()

    await raw_conn.copy_records_to_table(
        "users",
        records=records,
        columns=["email", "name", "created_at"]
    )
```

## Zero-Downtime Migrations

### Expand-Contract Pattern

```python
# Step 1: EXPAND - Add new column (nullable, no default)
# migrations/001_add_new_column.py
def upgrade():
    op.add_column("users", sa.Column("new_field", sa.String(), nullable=True))

def downgrade():
    op.drop_column("users", "new_field")

# Step 2: MIGRATE - Backfill data (can run while app is live)
# migrations/002_backfill_new_column.py
def upgrade():
    op.execute("""
        UPDATE users
        SET new_field = old_field
        WHERE new_field IS NULL
    """)

# Step 3: CONTRACT - Make non-nullable (after code deployed)
# migrations/003_make_required.py
def upgrade():
    op.alter_column("users", "new_field", nullable=False)
```

### Lock Timeout Configuration

```python
# alembic/env.py
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
    )

    with connectable.connect() as connection:
        # Set lock timeout to prevent long-running locks
        connection.execute(text("SET lock_timeout = '5s'"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()
```

### Safe Index Creation

```python
# Create index concurrently (no table lock)
def upgrade():
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_users_email
        ON users (email)
    """)

# In alembic.ini, set:
# transaction_per_migration = false  # Required for CONCURRENTLY
```

## Testing

### Testcontainers Setup

```python
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session")
async def db_engine(postgres_container):
    url = postgres_container.get_connection_url()
    async_url = url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(async_url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    async with AsyncSession(db_engine) as session:
        yield session
        await session.rollback()  # Isolate tests
```

### Factory Pattern

```python
import factory
from factory.alchemy import SQLAlchemyModelFactory

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")
    is_active = True

# Usage in tests
@pytest.mark.asyncio
async def test_user_service(db_session):
    UserFactory._meta.sqlalchemy_session = db_session
    user = UserFactory.create()

    result = await user_service.get_by_id(db_session, user.id)
    assert result.email == user.email
```

## Required Packages

```bash
pip install sqlalchemy[asyncio] asyncpg alembic
pip install testcontainers[postgres]  # Testing
```