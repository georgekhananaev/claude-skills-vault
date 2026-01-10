# Testing Standards

Cross-language testing requirements for production code.

## Coverage Thresholds

| Metric | Threshold | Enforcement |
|--------|-----------|-------------|
| Line coverage | 80% minimum | CI blocks below |
| Branch coverage | 70% minimum | CI warns below |
| New code coverage | 90% minimum | PR blocks below |

## What to Test (Priority Order)

1. **Critical Paths**: Auth, payments, data mutations
2. **Edge Cases**: Empty inputs, null values, boundaries
3. **Error Handling**: Ensure errors are caught and handled
4. **Integration Points**: API contracts, DB queries

## What NOT to Test

- Generated code (GraphQL, Protobuf, Prisma)
- Simple getters/setters
- Framework internals
- Third-party library behavior

## TypeScript (Vitest/Jest)

### Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        coverage: {
            provider: 'v8',
            reporter: ['text', 'json', 'html'],
            thresholds: {
                lines: 80,
                branches: 70,
                functions: 80,
                statements: 80,
            },
            exclude: [
                'node_modules/',
                '**/*.d.ts',
                '**/__generated__/**',
                '**/generated/**',
            ],
        },
    },
});
```

### Unit Tests

```typescript
import { describe, it, expect, vi } from 'vitest';

describe('UserService', () => {
    describe('createUser', () => {
        it('creates user with valid input', async () => {
            const user = await userService.create({
                email: 'test@example.com',
                name: 'Test User',
            });

            expect(user.id).toBeDefined();
            expect(user.email).toBe('test@example.com');
        });

        it('throws on duplicate email', async () => {
            await userService.create({ email: 'dup@test.com', name: 'First' });

            await expect(
                userService.create({ email: 'dup@test.com', name: 'Second' })
            ).rejects.toThrow('Email already exists');
        });

        it('validates email format', async () => {
            await expect(
                userService.create({ email: 'invalid', name: 'Test' })
            ).rejects.toThrow('Invalid email');
        });
    });
});
```

### Mocking

```typescript
import { vi } from 'vitest';

// Mock module
vi.mock('./database', () => ({
    db: {
        user: {
            create: vi.fn(),
            findUnique: vi.fn(),
        },
    },
}));

// Mock implementation per test
it('handles database error', async () => {
    vi.mocked(db.user.create).mockRejectedValue(new Error('Connection failed'));

    await expect(userService.create(validInput)).rejects.toThrow('Connection failed');
});
```

## Python (pytest)

### Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = [
    "--strict-markers",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
]

[tool.coverage.run]
branch = true
omit = [
    "*/migrations/*",
    "*/__generated__/*",
    "*/conftest.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

### Unit Tests

```python
import pytest
from app.services import UserService, DuplicateEmailError

class TestUserService:
    @pytest.fixture
    def service(self, mock_db):
        return UserService(db=mock_db)

    async def test_create_user_valid_input(self, service):
        user = await service.create(
            email="test@example.com",
            name="Test User",
        )

        assert user.id is not None
        assert user.email == "test@example.com"

    async def test_create_user_duplicate_email(self, service):
        await service.create(email="dup@test.com", name="First")

        with pytest.raises(DuplicateEmailError):
            await service.create(email="dup@test.com", name="Second")

    @pytest.mark.parametrize("email", [
        "invalid",
        "@missing.com",
        "no-domain@",
        "",
    ])
    async def test_create_user_invalid_email(self, service, email):
        with pytest.raises(ValueError, match="Invalid email"):
            await service.create(email=email, name="Test")
```

### Fixtures

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.user.create = AsyncMock()
    db.user.find_unique = AsyncMock(return_value=None)
    return db

@pytest.fixture
async def test_user(service):
    """Create a test user for use in other tests."""
    return await service.create(email="fixture@test.com", name="Fixture User")
```

## Go

### Configuration

```bash
# Run tests with coverage
go test -v -race -coverprofile=coverage.out ./...

# Check coverage threshold
go tool cover -func=coverage.out | grep total | awk '{print $3}' | \
    awk -F'%' '{if ($1 < 80) exit 1}'
```

### Unit Tests

```go
package user_test

import (
    "context"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestUserService_Create(t *testing.T) {
    t.Run("creates user with valid input", func(t *testing.T) {
        svc := NewUserService(mockDB)

        user, err := svc.Create(ctx, CreateUserInput{
            Email: "test@example.com",
            Name:  "Test User",
        })

        require.NoError(t, err)
        assert.NotEmpty(t, user.ID)
        assert.Equal(t, "test@example.com", user.Email)
    })

    t.Run("returns error on duplicate email", func(t *testing.T) {
        svc := NewUserService(mockDB)
        input := CreateUserInput{Email: "dup@test.com", Name: "First"}

        _, err := svc.Create(ctx, input)
        require.NoError(t, err)

        _, err = svc.Create(ctx, input)
        assert.ErrorIs(t, err, ErrDuplicateEmail)
    })
}

func TestUserService_Create_InvalidEmail(t *testing.T) {
    tests := []struct {
        name  string
        email string
    }{
        {"missing @", "invalid"},
        {"missing local", "@missing.com"},
        {"missing domain", "no-domain@"},
        {"empty", ""},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            svc := NewUserService(mockDB)

            _, err := svc.Create(ctx, CreateUserInput{
                Email: tt.email,
                Name:  "Test",
            })

            assert.ErrorIs(t, err, ErrInvalidEmail)
        })
    }
}
```

### Race Detection

```bash
# ALWAYS run tests with race detector in CI
go test -race ./...
```

## Rust

### Configuration

```toml
# Cargo.toml
[dev-dependencies]
tokio-test = "0.4"
mockall = "0.12"
proptest = "1.4"
```

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_create_user_valid_input() {
        let service = UserService::new(MockDb::new());

        let user = service.create(CreateUserInput {
            email: "test@example.com".into(),
            name: "Test User".into(),
        }).await.unwrap();

        assert!(!user.id.is_empty());
        assert_eq!(user.email, "test@example.com");
    }

    #[tokio::test]
    async fn test_create_user_duplicate_email() {
        let service = UserService::new(MockDb::new());
        let input = CreateUserInput {
            email: "dup@test.com".into(),
            name: "First".into(),
        };

        service.create(input.clone()).await.unwrap();

        let result = service.create(input).await;
        assert!(matches!(result, Err(UserError::DuplicateEmail(_))));
    }

    // Property-based testing
    proptest! {
        #[test]
        fn create_user_never_panics(email: String, name: String) {
            let service = UserService::new(MockDb::new());
            let _ = tokio_test::block_on(service.create(CreateUserInput {
                email,
                name,
            }));
        }
    }
}
```

### Coverage

```bash
# Install tarpaulin
cargo install cargo-tarpaulin

# Run with coverage
cargo tarpaulin --out Html --fail-under 80
```

## CI Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: TypeScript Tests
        if: hashFiles('package.json')
        run: |
          npm ci
          npm run test:coverage
          # Fail if coverage below threshold
          npx vitest run --coverage --coverage.thresholds.lines=80

      - name: Python Tests
        if: hashFiles('pyproject.toml')
        run: |
          pip install -e ".[dev]"
          pytest --cov=src --cov-fail-under=80

      - name: Go Tests
        if: hashFiles('go.mod')
        run: |
          go test -v -race -coverprofile=coverage.out ./...
          # Check threshold
          COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | tr -d '%')
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "Coverage $COVERAGE% is below 80%"
            exit 1
          fi

      - name: Rust Tests
        if: hashFiles('Cargo.toml')
        run: cargo tarpaulin --fail-under 80
```