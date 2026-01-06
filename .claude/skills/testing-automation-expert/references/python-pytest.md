# Python Testing with Pytest

## Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
testpaths = ["tests"]
markers = [
    "unit: fast isolated tests",
    "integration: requires external services",
    "e2e: end-to-end tests",
    "slow: long-running tests",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "raise NotImplementedError"]
fail_under = 80
```

## Fixture Architecture

### Basic Fixtures

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

@pytest.fixture(scope="session")
async def db_engine():
    """Session-scoped DB engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    """Per-test isolated session."""
    async with AsyncSession(db_engine) as session:
        yield session
        await session.rollback()
```

### Testcontainers (Real DB)

```python
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session")
async def db_engine(postgres_container):
    url = postgres_container.get_connection_url()
    async_url = url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(async_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
```

### Factory Fixtures

```python
@pytest.fixture
def user_factory(db_session):
    created = []

    async def create(email: str = "test@example.com", role: str = "user", **kwargs) -> User:
        user = User(email=email, role=role, **kwargs)
        db_session.add(user)
        await db_session.flush()
        created.append(user)
        return user

    yield create

    for user in created:
        await db_session.delete(user)
```

### Fixture Scopes

| Scope | Lifecycle | Use For |
|-------|-----------|---------|
| `function` | Per test (default) | Isolated state |
| `class` | Per test class | Shared setup |
| `module` | Per file | Expensive setup |
| `session` | Entire run | DB engine, containers |

## Parametrization

```python
# Basic
@pytest.mark.parametrize("input,expected", [
    ("valid@email.com", True),
    ("invalid", False),
    ("", False),
])
def test_email_validation(input, expected):
    assert validate_email(input) == expected

# With IDs
@pytest.mark.parametrize("user,expected", [
    pytest.param({"role": "admin"}, True, id="admin-allowed"),
    pytest.param({"role": "user"}, False, id="user-denied"),
])
def test_permissions(user, expected):
    ...

# Indirect (pass to fixtures)
@pytest.fixture
def user(request, db_session):
    role = request.param.get("role", "user")
    return User(role=role)

@pytest.mark.parametrize("user", [{"role": "admin"}], indirect=True)
def test_admin_access(user):
    ...
```

## Mocking (pytest-mock)

```python
def test_email_sent(mocker):
    mock_send = mocker.patch("myapp.services.email.send_email")
    user_service.create_user("test@example.com")
    mock_send.assert_called_once_with(to="test@example.com", subject="Welcome!")

def test_spy_method(mocker):
    spy = mocker.spy(user_service, "validate_email")
    user_service.create_user("test@example.com")
    spy.assert_called_once()

def test_mock_async_context(mocker):
    mock_session = mocker.MagicMock()
    mock_session.__aenter__ = mocker.AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = mocker.AsyncMock(return_value=None)
    mocker.patch("myapp.db.get_session", return_value=mock_session)
```

## Time Mocking (time-machine)

```python
import time_machine
from datetime import timedelta

@time_machine.travel("2024-01-15 10:00:00")
def test_token_expiry():
    token = create_token(expires_in=timedelta(hours=1))
    assert token.is_valid()

@time_machine.travel("2024-01-15 10:00:00")
def test_token_expired():
    token = create_token(expires_in=timedelta(hours=1))
    with time_machine.travel("2024-01-15 12:00:00"):
        assert not token.is_valid()
```

## Snapshot Testing (syrupy)

```python
def test_user_serialization(snapshot):
    user = User(id=1, name="John", email="john@test.com")
    assert user.to_dict() == snapshot

def test_api_response(snapshot, client):
    response = client.get("/api/users/1")
    assert response.json() == snapshot(name="user_response")

# Update: pytest --snapshot-update
```

## Declarative Assertions (dirty-equals)

Simplify complex JSON/object assertions:

```python
from dirty_equals import IsInt, IsNow, IsStr, IsUUID, IsPartialDict

def test_user_response(client):
    response = client.post("/api/users", json={"email": "test@test.com"})

    # Flexible assertions without exact values
    assert response.json() == {
        "id": IsUUID,
        "email": "test@test.com",
        "created_at": IsNow(iso_string=True),
        "token": IsStr(min_length=32),
    }

def test_partial_match():
    data = {"id": 1, "name": "John", "metadata": {"key": "value"}}

    # Only check specific fields
    assert data == IsPartialDict(id=IsInt, name="John")

def test_list_contains():
    from dirty_equals import Contains, HasLen

    users = [{"id": 1}, {"id": 2}, {"id": 3}]
    assert users == HasLen(3) & Contains({"id": IsInt})
```

## Flakiness Detection (pytest-randomly)

Randomize test order to expose hidden state dependencies:

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "-p randomly"
```

```bash
# Run with specific seed (reproduce failures)
pytest -p randomly --randomly-seed=12345

# Disable for debugging
pytest -p randomly --randomly-dont-shuffle

# Show seed in output
pytest -v  # Seed shown: Using --randomly-seed=...
```

**Why it matters:**
- Exposes tests that depend on execution order
- Finds shared state pollution between tests
- Reveals hidden test coupling

## Async Testing

```python
from httpx import AsyncClient, ASGITransport

@pytest.fixture
async def client(app, db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_item(client):
    response = await client.post("/items", json={"name": "test"})
    assert response.status_code == 201
```

## Property-Based Testing (Hypothesis)

```python
from hypothesis import given, strategies as st, settings

@given(st.text())
def test_string_roundtrip(s):
    assert s.encode().decode() == s

@given(st.lists(st.integers()))
def test_sort_idempotent(lst):
    assert sorted(sorted(lst)) == sorted(lst)

# Custom strategy
@st.composite
def order_with_items(draw):
    order = draw(st.builds(Order))
    items = draw(st.lists(st.builds(OrderItem), min_size=1, max_size=10))
    order.items = items
    return order

@given(order_with_items())
def test_order_total(order):
    expected = sum(item.price * item.qty for item in order.items)
    assert order.calculate_total() == expected

# Profiles
settings.register_profile("ci", max_examples=1000)
settings.register_profile("dev", max_examples=50)
# pytest --hypothesis-profile=ci
```

## Directory Structure

```
tests/
├── conftest.py              # Root fixtures
├── unit/
│   ├── conftest.py
│   ├── test_models.py
│   └── test_services.py
├── integration/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_repositories.py
├── e2e/
│   ├── conftest.py
│   └── test_flows.py
└── fixtures/
    ├── users.json
    └── orders.json
```

## Commands

```bash
pytest                              # Run all
pytest -m "not slow"                # Skip slow
pytest --cov=src --cov-report=html  # Coverage
pytest -n auto                      # Parallel
pytest -x                           # Stop on first failure
pytest --lf                         # Re-run failed
pytest -v --tb=short                # Verbose
```

## Required Packages

```bash
pip install pytest pytest-asyncio pytest-cov pytest-xdist
pip install pytest-mock pytest-randomly time-machine
pip install syrupy hypothesis dirty-equals
pip install testcontainers[postgres] httpx
```
