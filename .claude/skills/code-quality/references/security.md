# Security Standards

Cross-language security rules for production code.

## Severity Levels

| Category | Severity | Description |
|----------|----------|-------------|
| Secrets | Critical | Hardcoded credentials |
| Injection | Critical | SQL/Command injection |
| Dependencies | Critical | Known CVEs |
| Deserialization | Critical | Unsafe parsing |
| Input Validation | Error | Missing validation |
| Auth | Error | Improper authentication |
| Crypto | Error | Custom cryptography |
| Logging | Error | PII in logs |

## Secrets Detection

### Pre-commit (gitleaks)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

### CI (GitHub Actions)

```yaml
- uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### gitleaks Configuration

```toml
# .gitleaks.toml
[extend]
useDefault = true

[allowlist]
description = "Allowlist for false positives"
paths = [
  '''\.test\.ts$''',
  '''\.spec\.ts$''',
  '''fixtures/''',
  '''__mocks__/''',
]

# Custom patterns
[[rules]]
id = "custom-api-key"
description = "Custom API key pattern"
regex = '''CUSTOM_[A-Z]+_KEY\s*=\s*['"][a-zA-Z0-9]{32,}['"]'''
```

## Dependency Scanning (SCA)

### TypeScript

```bash
# npm
npm audit --audit-level=high

# pnpm
pnpm audit --audit-level=high

# yarn
yarn audit --level high
```

### Python

```bash
# pip-audit
pip-audit --strict --desc on

# safety (alternative)
safety check
```

### Go

```bash
# govulncheck (official)
govulncheck ./...

# nancy (Sonatype)
go list -json -deps ./... | nancy sleuth
```

### Rust

```bash
# cargo-audit
cargo audit

# cargo-deny (more comprehensive)
cargo deny check
```

### CI Integration

```yaml
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: TypeScript - npm audit
        if: hashFiles('package-lock.json')
        run: npm audit --audit-level=high

      - name: Python - pip-audit
        if: hashFiles('requirements.txt') || hashFiles('pyproject.toml')
        run: pip-audit --strict

      - name: Go - govulncheck
        if: hashFiles('go.mod')
        run: govulncheck ./...

      - name: Rust - cargo-audit
        if: hashFiles('Cargo.toml')
        run: cargo audit
```

## Injection Prevention

### SQL Injection

```typescript
// CRITICAL: Never interpolate user input
const bad = await db.query(`SELECT * FROM users WHERE id = ${id}`);  // Error

// OK: Parameterized queries
const good = await db.query('SELECT * FROM users WHERE id = $1', [id]);  // OK
```

```python
# CRITICAL: Never use f-strings in queries
cursor.execute(f"SELECT * FROM users WHERE id = {id}")  # Error

# OK: Parameterized queries
cursor.execute("SELECT * FROM users WHERE id = %s", (id,))  # OK
```

```go
// CRITICAL: Never concatenate user input
db.Query("SELECT * FROM users WHERE id = " + id)  // Error

// OK: Parameterized queries
db.Query("SELECT * FROM users WHERE id = ?", id)  // OK
```

### Command Injection

```typescript
// CRITICAL: Never pass user input to shell
exec(`ls ${userPath}`);  // Error

// OK: Use array arguments
execFile('ls', [userPath]);  // OK
```

```python
# CRITICAL: Never use shell=True with user input
subprocess.run(f"ls {user_path}", shell=True)  # Error

# OK: Use array arguments
subprocess.run(["ls", user_path])  # OK
```

## Insecure Deserialization

### Python

```python
# CRITICAL: Never unpickle untrusted data
import pickle
data = pickle.loads(user_input)  # Error - RCE vulnerability

# OK: Use safe alternatives
import json
data = json.loads(user_input)  # OK

# For complex objects, use pydantic validation
from pydantic import BaseModel

class UserInput(BaseModel):
    name: str
    age: int

data = UserInput.model_validate_json(user_input)  # OK - validated
```

### TypeScript

```typescript
// CRITICAL: Never eval user input
eval(userInput);                  // Error
new Function(userInput)();        // Error
vm.runInNewContext(userInput);    // Error

// OK: Parse JSON safely
const data = JSON.parse(userInput);  // OK

// OK: Validate with zod
import { z } from 'zod';

const schema = z.object({
    name: z.string(),
    age: z.number(),
});

const data = schema.parse(JSON.parse(userInput));  // OK - validated
```

### Go

```go
// WARNING: gob with untrusted data
var data MyType
gob.NewDecoder(untrustedReader).Decode(&data)  // Warning

// OK: JSON with validation
var data MyType
if err := json.NewDecoder(reader).Decode(&data); err != nil {
    return err
}
if err := validate(data); err != nil {  // Always validate after decode
    return err
}
```

## Input Validation

### TypeScript (Zod)

```typescript
import { z } from 'zod';

const UserSchema = z.object({
    email: z.string().email(),
    age: z.number().min(0).max(150),
    role: z.enum(['user', 'admin']),
});

// Validate at API boundaries
function createUser(input: unknown): User {
    const validated = UserSchema.parse(input);  // Throws on invalid
    return userService.create(validated);
}
```

### Python (Pydantic)

```python
from pydantic import BaseModel, EmailStr, conint

class UserInput(BaseModel):
    email: EmailStr
    age: conint(ge=0, le=150)
    role: Literal['user', 'admin']

# Validate at API boundaries
@app.post("/users")
def create_user(input: UserInput) -> User:
    return user_service.create(input)
```

## Authentication/Authorization

```typescript
// ERROR: Timing-safe comparison missing
if (token === expectedToken) { ... }  // Error - timing attack

// OK: Use constant-time comparison
import { timingSafeEqual } from 'crypto';
const a = Buffer.from(token);
const b = Buffer.from(expectedToken);
if (a.length === b.length && timingSafeEqual(a, b)) { ... }  // OK
```

## Cryptography

```typescript
// ERROR: Custom crypto
function encrypt(data: string, key: string): string {
    return data.split('').map((c, i) =>
        String.fromCharCode(c.charCodeAt(0) ^ key.charCodeAt(i % key.length))
    ).join('');  // Error - XOR cipher is not secure
}

// OK: Use established libraries
import { createCipheriv, randomBytes } from 'crypto';

const iv = randomBytes(16);
const cipher = createCipheriv('aes-256-gcm', key, iv);  // OK
```

## Logging Security

```typescript
// ERROR: Logging sensitive data
logger.info({ password, token, creditCard });  // Error

// OK: Redact sensitive fields
logger.info({
    userId,
    email: maskEmail(email),  // user@example.com -> u***@e***.com
});
```

## OWASP Top 10 Coverage

| Risk | Mitigation | Tools |
|------|------------|-------|
| A01 Broken Access Control | Auth checks, RBAC | Custom middleware |
| A02 Cryptographic Failures | TLS, established crypto | OpenSSL, libsodium |
| A03 Injection | Parameterized queries | ORM, prepared statements |
| A04 Insecure Design | Threat modeling | Architecture review |
| A05 Security Misconfiguration | Secure defaults | Config scanning |
| A06 Vulnerable Components | SCA scanning | npm audit, pip-audit |
| A07 Auth Failures | MFA, rate limiting | Auth libraries |
| A08 Software Integrity | Code signing, SBOM | sigstore, in-toto |
| A09 Logging Failures | Structured logging | pino, structlog |
| A10 SSRF | URL validation | Allow lists |