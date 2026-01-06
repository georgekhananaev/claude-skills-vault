#!/usr/bin/env python3
"""
FastAPI Clean Architecture Scaffolder

Generates a production-ready FastAPI project structure following
hexagonal/clean architecture principles.

Usage:
    python scaffold_structure.py <project_name> [options]

Options:
    --with-docker    Include Docker configuration
    --with-alembic   Include Alembic migrations setup
    --db postgres    Database type (postgres, mysql, sqlite)
    --cache redis    Cache type (redis, memcached, none)

Example:
    python scaffold_structure.py my_api --with-docker --with-alembic --db postgres
"""

import argparse
import os
from pathlib import Path


STRUCTURE = {
    "src": {
        "api": {
            "routes": {"__init__.py": "", "users.py": None, "health.py": None},
            "deps": {"__init__.py": "", "database.py": None, "auth.py": None},
            "schemas": {"__init__.py": "", "users.py": None, "common.py": None},
            "__init__.py": "",
        },
        "services": {"__init__.py": "", "user_service.py": None},
        "repositories": {"__init__.py": "", "user_repository.py": None},
        "models": {
            "domain": {"__init__.py": "", "user.py": None},
            "db": {"__init__.py": "", "user.py": None},
            "__init__.py": "",
        },
        "core": {
            "__init__.py": "",
            "config.py": None,
            "security.py": None,
            "exceptions.py": None,
        },
        "infrastructure": {
            "__init__.py": "",
            "database.py": None,
            "cache.py": None,
            "external": {"__init__.py": ""},
        },
        "__init__.py": "",
        "main.py": None,
    },
    "tests": {
        "__init__.py": "",
        "conftest.py": None,
        "api": {"__init__.py": "", "test_users.py": None},
        "services": {"__init__.py": "", "test_user_service.py": None},
    },
}


def create_structure(base_path: Path, structure: dict, templates: dict) -> None:
    """Recursively create directory structure with files."""
    for name, content in structure.items():
        path = base_path / name
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            create_structure(path, content, templates)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if content is None:
                template_key = str(path.relative_to(base_path.parent))
                file_content = templates.get(template_key, f"# {name}\n")
            else:
                file_content = content
            path.write_text(file_content)
            print(f"  Created: {path}")


def get_templates(project_name: str, db: str, cache: str) -> dict:
    """Generate file templates based on configuration."""
    return {
        f"{project_name}/src/main.py": f'''"""
{project_name} - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import users, health
from src.core.config import settings
from src.core.exceptions import register_exception_handlers

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
register_exception_handlers(app)

# Routes
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
''',
        f"{project_name}/src/core/config.py": f'''"""
Application configuration using pydantic-settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # App
    PROJECT_NAME: str = "{project_name}"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "{"postgresql+asyncpg" if db == "postgres" else "sqlite+aiosqlite"}://..."

    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
''',
        f"{project_name}/src/core/exceptions.py": '''"""
Custom exception classes and handlers.
"""
from typing import Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: str, status: int = 400):
        self.message = message
        self.code = code
        self.status = status


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, resource: str, id: Any):
        super().__init__(f"{resource} {id} not found", "NOT_FOUND", 404)


class ValidationError(AppException):
    """Validation failed."""

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 422)


class AuthError(AppException):
    """Authentication/authorization failed."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED", 401)


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers with the app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
''',
        f"{project_name}/src/infrastructure/database.py": '''"""
Database connection and session management.
"""
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
''',
        f"{project_name}/src/api/routes/health.py": '''"""
Health check endpoints.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check():
    """Readiness check - verify dependencies."""
    # TODO: Add DB and cache connectivity checks
    return {"status": "ready"}
''',
        f"{project_name}/tests/conftest.py": '''"""
Pytest configuration and fixtures.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.main import app
from src.api.deps.database import get_db
from src.models.db.base import Base


@pytest.fixture
async def db_session():
    """Create in-memory database session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.fixture
async def client(db_session):
    """Create async test client with overridden dependencies."""
    app.dependency_overrides[get_db] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
''',
    }


def create_docker_files(base_path: Path, project_name: str) -> None:
    """Create Docker configuration files."""
    dockerfile = '''# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Export requirements
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

    dockerignore = '''__pycache__
*.py[cod]
*.so
.Python
.env
.venv
env/
venv/
.git
.gitignore
.dockerignore
Dockerfile
docker-compose*.yml
*.md
tests/
.pytest_cache/
.coverage
htmlcov/
'''

    (base_path / "Dockerfile").write_text(dockerfile)
    (base_path / ".dockerignore").write_text(dockerignore)
    print(f"  Created: {base_path / 'Dockerfile'}")
    print(f"  Created: {base_path / '.dockerignore'}")


def create_alembic_files(base_path: Path, project_name: str) -> None:
    """Create Alembic migration configuration."""
    alembic_ini = '''[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''

    env_py = '''"""
Alembic environment configuration for async SQLAlchemy.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from src.core.config import settings
from src.models.db.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

    alembic_dir = base_path / "alembic"
    alembic_dir.mkdir(exist_ok=True)
    (alembic_dir / "versions").mkdir(exist_ok=True)

    (base_path / "alembic.ini").write_text(alembic_ini)
    (alembic_dir / "env.py").write_text(env_py)
    (alembic_dir / "versions" / ".gitkeep").write_text("")

    print(f"  Created: {base_path / 'alembic.ini'}")
    print(f"  Created: {alembic_dir / 'env.py'}")


def create_misc_files(base_path: Path, project_name: str) -> None:
    """Create miscellaneous project files."""
    gitignore = '''__pycache__
*.py[cod]
*.so
.Python
.env
.venv
env/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
'''

    pyproject = f'''[tool.poetry]
name = "{project_name}"
version = "0.1.0"
description = "FastAPI application"
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {{extras = ["standard"], version = "^0.27.0"}}
pydantic-settings = "^2.1.0"
sqlalchemy = {{extras = ["asyncio"], version = "^2.0.0"}}
asyncpg = "^0.29.0"
alembic = "^1.13.0"
httpx = "^0.26.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.23.0"
ruff = "^0.1.0"
mypy = "^1.8.0"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
'''

    env_example = '''# Application
DEBUG=false
SECRET_KEY=change-me-in-production

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0
'''

    (base_path / ".gitignore").write_text(gitignore)
    (base_path / "pyproject.toml").write_text(pyproject)
    (base_path / ".env.example").write_text(env_example)

    print(f"  Created: {base_path / '.gitignore'}")
    print(f"  Created: {base_path / 'pyproject.toml'}")
    print(f"  Created: {base_path / '.env.example'}")


def main():
    parser = argparse.ArgumentParser(description="Scaffold FastAPI project structure")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--with-docker", action="store_true", help="Include Docker files")
    parser.add_argument("--with-alembic", action="store_true", help="Include Alembic setup")
    parser.add_argument("--db", default="postgres", choices=["postgres", "mysql", "sqlite"])
    parser.add_argument("--cache", default="redis", choices=["redis", "memcached", "none"])
    parser.add_argument("--output", "-o", default=".", help="Output directory")

    args = parser.parse_args()

    base_path = Path(args.output) / args.project_name
    if base_path.exists():
        print(f"Error: Directory {base_path} already exists")
        return 1

    print(f"\nScaffolding FastAPI project: {args.project_name}")
    print(f"Database: {args.db}, Cache: {args.cache}")
    print("-" * 50)

    templates = get_templates(args.project_name, args.db, args.cache)
    create_structure(base_path, STRUCTURE, templates)

    create_misc_files(base_path, args.project_name)

    if args.with_docker:
        print("\nAdding Docker configuration...")
        create_docker_files(base_path, args.project_name)

    if args.with_alembic:
        print("\nAdding Alembic migrations...")
        create_alembic_files(base_path, args.project_name)

    print("\n" + "=" * 50)
    print(f"Project scaffolded at: {base_path}")
    print("\nNext steps:")
    print(f"  cd {args.project_name}")
    print("  poetry install")
    print("  cp .env.example .env")
    print("  uvicorn src.main:app --reload")

    return 0


if __name__ == "__main__":
    exit(main())