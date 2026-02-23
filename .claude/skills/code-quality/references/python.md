# Python Standards (PEP 8 / 3.11+)

Auto-enforce Python 3.11+ standards with strict typing and modern idioms.

## Core Standards

| Standard | Desc |
|----------|------|
| PEP 8 | Naming, imports, spacing |
| PEP 484/585 | Type hints (modern) |
| PEP 257 | Docstrings |
| PEP 604 | Union `|` |
| PEP 570/3102 | `/` positional, `*` keyword |

## Naming

```python
class UserAccount: pass        # PascalCase
class HTTPClient: pass         # Acronyms: all caps
def calculate_total(): pass    # snake_case
async def fetch_data(): pass   # async same

user_name = "john"             # Variables: snake_case
MAX_RETRIES = 3                # Constants: SCREAMING_SNAKE

def _internal(): pass          # Private: underscore
__mangled = "hidden"           # Name mangling: double

T = TypeVar("T")               # TypeVars: PascalCase
UserT = TypeVar("UserT", bound="User")
```

## Type Hints (3.11+)

### Modern Syntax (Required)

```python
# Built-in generics (NOT typing module)
def process(items: list[str]) -> dict[str, int]: ...

# Union w/ | (NOT Optional/Union)
def find_user(id: str) -> User | None: ...

# Self type
from typing import Self
class Builder:
    def chain(self) -> Self: return self
```

### Patterns

```python
from collections.abc import Callable, Awaitable
from typing import TypedDict, Literal, TypeAlias, ParamSpec, Generic

# Callable
Handler = Callable[[Request], Response]
AsyncHandler = Callable[[Request], Awaitable[Response]]

# TypedDict
class UserData(TypedDict):
    id: str
    email: Required[str]
    phone: NotRequired[str | None]

# Literal
Status = Literal["pending", "active", "disabled"]

# TypeAlias
JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]

# ParamSpec (decorators)
P = ParamSpec("P")
def logged(fn: Callable[P, T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        logger.info(f"Calling {fn.__name__}")
        return fn(*args, **kwargs)
    return wrapper

# Generic
class Repo(Generic[T]):
    def get(self, id: str) -> T | None: ...
```

### Deprecated (Never Use)

```python
# WRONG                          # RIGHT
List[str]                        # list[str]
Optional[int]                    # int | None
Dict[str, int]                   # dict[str, int]
Tuple[int, str]                  # tuple[int, str]
Union[int, str]                  # int | str
```

## Docstrings (Google Style)

```python
def calculate_discount(price: float, percent: float, min_price: float = 0.0) -> float:
    """Calculate discounted price w/ floor.

    Args:
        price: Original price.
        percent: Discount (0-100).
        min_price: Min allowed price.

    Returns:
        Final price, never below min_price.

    Raises:
        ValueError: If invalid inputs.
    """
```

**Skip docstrings for:** self-documenting fns, `_private` methods, trivial `@property`

## Imports

```python
# 1. Stdlib (alphabetical)
import asyncio
from pathlib import Path
from typing import Any

# 2. Third-party
import httpx
from fastapi import Depends, HTTPException
from pydantic import BaseModel

# 3. Local
from app.core.config import settings
from app.models import User
```

**Rules:** No wildcards (`*`), group from same module, parentheses for long imports

## Function Signatures (PEP 570/3102)

```python
def api_fn(
    x: int, y: int,           # positional-only
    /,
    z: int = 0,               # positional or keyword
    *,
    strict: bool = False,     # keyword-only
) -> Result: ...
```

### Overloads

```python
from typing import overload

@overload
def process(v: int) -> int: ...
@overload
def process(v: str) -> str: ...
def process(v: int | str) -> int | str:
    return v * 2 if isinstance(v, int) else v.upper()
```

## Function Design

| Lines | Status |
|-------|--------|
| < 20 | Ideal |
| 20-30 | OK |
| 30-50 | Split |
| > 50 | Refactor |

**Params:** Max 5 -> use dataclass/config obj for more
**Returns:** Always annotate; no flag-based return types

## Exception Handling

```python
# DO: Specific exceptions w/ context
try:
    user = await db.get(User, id)
except IntegrityError as e:
    raise UserExistsError(id) from e

# DO: Context managers
async with AsyncSession(engine) as session:
    async with session.begin(): ...

# DON'T
except:           # bare - catches SystemExit
except Exception: # swallows errors
    pass          # silent - at minimum log

# Exception groups (3.11+)
except* ValueError as eg:
    for e in eg.exceptions: handle(e)
```

## Security Rules

```python
# CRITICAL: Never use pickle with untrusted data
data = pickle.loads(user_input)  # Error - RCE

# CRITICAL: No eval
result = eval(user_expression)   # Error

# CRITICAL: No shell=True with user input
subprocess.run(f"ls {user_path}", shell=True)  # Error
subprocess.run(["ls", user_path])               # OK

# SQL: Parameterized queries only
cursor.execute(f"SELECT * FROM users WHERE id = {id}")     # Error
cursor.execute("SELECT * FROM users WHERE id = ?", (id,))  # OK
```

## Constants

```python
MAX_RETRIES = 3
DEFAULT_TIMEOUT = timedelta(seconds=30)
FORMATS = frozenset({"json", "xml"})

class Status(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"

# NO magic values
await asyncio.sleep(5)         # Bad
await asyncio.sleep(INTERVAL)  # Good
```

## Async

```python
# Context managers
async with httpx.AsyncClient() as client:
    resp = await client.get(url)

# TaskGroup (3.11+)
async with asyncio.TaskGroup() as tg:
    tg.create_task(fetch_a())
    tg.create_task(fetch_b())

# Timeout
async with asyncio.timeout(5.0):
    await slow_op()

# Never block loop
await asyncio.to_thread(blocking_io)  # sync I/O
await asyncio.sleep(1)                # NOT time.sleep()
```

## Pathlib (NOT os.path)

```python
from pathlib import Path

data = Path("data") / "config.json"
text = data.read_text(encoding="utf-8")
```

## Logging

```python
logger = logging.getLogger(__name__)

# Lazy formatting (NOT f-strings)
logger.info("Processing %s items", count)  # YES
logger.info(f"Processing {count}")         # NO - always evaluated

logger.exception("Failed")  # auto-includes traceback
```

## Data Models

| Type | Use Case |
|------|----------|
| TypedDict | External JSON/dicts |
| dataclass | Internal DTOs |
| Pydantic | Validation needed |
| NamedTuple | Immutable, hashable |

## Context Managers

```python
from contextlib import suppress, asynccontextmanager

with suppress(FileNotFoundError):
    Path("temp.txt").unlink()

@asynccontextmanager
async def connection():
    conn = await create()
    try: yield conn
    finally: await conn.close()
```

## Anti-Patterns

| Bad | Fix |
|-----|-----|
| No type hints | Type all params & returns |
| `List`, `Optional` | `list`, `| None` |
| Bare `except:` | Specific exceptions |
| Magic numbers | Named constants |
| `== None` | `is None` |
| f-strings in logger | `%s` formatting |
| os.path | pathlib |
| Mutable defaults | `None` + factory |
| > 50 lines | Split fn |

## Python 3.11+ Features

```python
# match/case
match cmd:
    case {"action": "create", "data": d}: create(d)
    case _: raise ValueError()

# tomllib (built-in TOML)
import tomllib
config = tomllib.load(open("config.toml", "rb"))
```

## Ruff Configuration (Strict)

```toml
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E", "W", "F", "I", "B", "C4", "C90", "UP", "N",
    "S", "T20", "SIM", "RUF", "PTH", "ASYNC", "ANN",
    "ARG", "ERA", "PL", "PERF", "LOG",
]
ignore = ["E501", "ANN101", "ANN102"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-args = 5

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "ANN", "ARG"]
```

## mypy Configuration (Strict)

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
show_error_codes = true
```

## Pre-commit

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
      - id: mypy
```

## Formatting

- Line: 88 (Black) or 79 (strict PEP 8)
- Indent: 4 spaces
- Blanks: 2 top-level, 1 methods
- Trailing commas in multi-line
