# Python Standards

Extends the `pep8` skill with additional strictness.

> **Note**: For comprehensive Python style, see `.claude/skills/pep8/SKILL.md`

## Core Principles

- **Type hints everywhere**: All function signatures typed
- **Modern syntax**: Python 3.11+ features only
- **Strict mypy**: Full strict mode enabled
- **No bare exceptions**: Always specific

## Type Hints (Mandatory)

### Modern Syntax (Required)

```python
# CRITICAL: All functions must be typed
def bad(data):                   # Error - no types
    return data

def good(data: dict[str, Any]) -> list[str]:  # OK
    return list(data.keys())

# Use built-in generics (NOT typing module)
items: list[str] = []            # OK
users: dict[str, User] = {}      # OK

# Union with | (NOT Optional/Union)
value: str | None = None         # OK
result: int | str = 0            # OK

# NEVER use deprecated syntax
from typing import List, Optional, Dict  # Error
```

### Function Signatures

```python
from collections.abc import Callable, Awaitable

# Always type parameters and returns
def process(
    items: list[str],
    *,
    strict: bool = False,
) -> dict[str, int]:
    ...

# Async functions
async def fetch(url: str) -> bytes:
    ...

# Callable types
Handler = Callable[[Request], Response]
AsyncHandler = Callable[[Request], Awaitable[Response]]
```

### Advanced Patterns

```python
from typing import TypeVar, Generic, Self, ParamSpec, TypedDict

# TypeVar for generics
T = TypeVar("T")

class Repository(Generic[T]):
    def get(self, id: str) -> T | None: ...
    def save(self, entity: T) -> T: ...

# Self type for fluent interfaces
class Builder:
    def with_name(self, name: str) -> Self:
        self.name = name
        return self

# TypedDict for structured dicts
class UserData(TypedDict):
    id: str
    email: str
    name: str | None

# ParamSpec for decorators
P = ParamSpec("P")

def logged(fn: Callable[P, T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        logger.info(f"Calling {fn.__name__}")
        return fn(*args, **kwargs)
    return wrapper
```

## Ruff Configuration (Strict)

```toml
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E", "W",     # pycodestyle
    "F",          # pyflakes
    "I",          # isort
    "B",          # flake8-bugbear
    "C4",         # flake8-comprehensions
    "C90",        # mccabe complexity
    "UP",         # pyupgrade
    "N",          # pep8-naming
    "S",          # flake8-bandit (security)
    "T20",        # flake8-print
    "SIM",        # flake8-simplify
    "RUF",        # ruff-specific
    "PTH",        # flake8-use-pathlib
    "ASYNC",      # flake8-async
    "ANN",        # flake8-annotations
    "ARG",        # flake8-unused-arguments
    "ERA",        # eradicate (commented code)
    "PL",         # pylint
    "PERF",       # perflint
    "LOG",        # flake8-logging
]
ignore = ["E501", "ANN101", "ANN102"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-args = 5

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "ANN", "ARG"]
"conftest.py" = ["ANN"]
```

## mypy Configuration (Strict)

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true
check_untyped_defs = true
show_error_codes = true
enable_error_code = ["ignore-without-code", "redundant-cast"]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

## Exception Handling

```python
# CRITICAL: No bare except
try:
    result = process()
except:  # Error - catches SystemExit, KeyboardInterrupt
    pass

# CRITICAL: No broad Exception without re-raise
try:
    result = process()
except Exception:  # Error - swallows all errors
    pass

# OK: Specific exceptions with context
try:
    user = await db.get(User, id)
except IntegrityError as e:
    raise UserExistsError(id) from e
except DatabaseError as e:
    logger.exception("Database error")
    raise ServiceUnavailableError() from e

# OK: Exception groups (3.11+)
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(task1())
        tg.create_task(task2())
except* ValueError as eg:
    for e in eg.exceptions:
        handle(e)
```

## Security Rules

```python
# CRITICAL: Never use pickle with untrusted data
import pickle
data = pickle.loads(user_input)  # Error - RCE vulnerability

# Use safe alternatives
import json
data = json.loads(user_input)    # OK

# CRITICAL: No eval
result = eval(user_expression)   # Error
result = literal_eval(user_expression)  # OK for literals only

# CRITICAL: No shell=True with user input
subprocess.run(f"ls {user_path}", shell=True)  # Error
subprocess.run(["ls", user_path])               # OK

# SQL: Parameterized queries only
cursor.execute(f"SELECT * FROM users WHERE id = {id}")  # Error
cursor.execute("SELECT * FROM users WHERE id = ?", (id,))  # OK
```

## Anti-Patterns

| Bad | Good | Why |
|-----|------|-----|
| No type hints | Type all params & returns | Type safety |
| `List[str]` | `list[str]` | Modern syntax |
| `Optional[int]` | `int \| None` | PEP 604 |
| Bare `except:` | Specific exceptions | Don't swallow errors |
| Magic numbers | Named constants | Readability |
| `== None` | `is None` | Identity check |
| f-strings in logger | `%s` formatting | Lazy evaluation |
| `os.path` | `pathlib.Path` | Modern API |
| Mutable defaults | `None` + factory | Avoid shared state |

## File Organization

```python
# 1. Future imports (if needed)
from __future__ import annotations

# 2. Standard library
import asyncio
from pathlib import Path
from typing import Any

# 3. Third-party
import httpx
from fastapi import Depends
from pydantic import BaseModel

# 4. Local
from app.core.config import settings
from app.models import User
```
