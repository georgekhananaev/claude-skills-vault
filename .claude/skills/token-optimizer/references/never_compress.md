# Never Compress List

Content that MUST NOT be compressed or modified. These are security-critical elements where compression could cause data loss, security vulnerabilities, or incorrect behavior.

## Authentication & Secrets

| Category | Examples | Why |
|----------|----------|-----|
| Auth tokens | `Bearer eyJ...`, JWT tokens | Exact match req for auth |
| API keys | `sk-...`, `AKIA...` | Single char change = invalid |
| Passwords | User credentials | Security critical |
| Secrets | `secret_...`, env secrets | Must be exact |
| Session IDs | `sess_...`, cookies | Identity critical |

## Error Context

| Category | Examples | Why |
|----------|----------|-----|
| Stack traces | Full error traces | Debugging needs exact lines |
| Error codes | `ERR_001`, `HTTP 401` | Lookup requires exact code |
| Line numbers | `:42`, `line 156` | Must match source |
| File paths in errors | `/src/app.ts:42` | Navigation requires exact path |

## Code Elements

| Category | Examples | Why |
|----------|----------|-----|
| Code blocks | ``` fenced code ``` | Syntax must be valid |
| Inline code | `variableName` | Exact names matter |
| Regex patterns | `/^[a-z]+$/` | Single char = wrong match |
| SQL queries | `SELECT * FROM users` | Syntax critical |
| Shell commands | `rm -rf /var/log/*` | Dangerous if modified |

## Identifiers

| Category | Examples | Why |
|----------|----------|-----|
| URLs | `https://api.example.com/v1` | Endpoints must be exact |
| UUIDs | `550e8400-e29b-41d4-...` | Identity critical |
| Version numbers | `v2.1.0`, `^18.0.0` | Semver matching |
| Package names | `@org/package-name` | npm/pip lookup |
| Git refs | `abc123def`, branch names | Must be exact |

## Data Formats

| Category | Examples | Why |
|----------|----------|-----|
| JSON keys | `"user_id"`, `"createdAt"` | API contracts |
| Quoted strings | `"exact text"` | Intentionally exact |
| Config values | `timeout: 30000` | Numeric precision |
| Date formats | `2024-01-15T10:30:00Z` | Parsing requires format |

## Security-Related

| Category | Examples | Why |
|----------|----------|-----|
| Auth headers | `Authorization: Bearer ...` | Security flow |
| CORS origins | `https://allowed-origin.com` | Security policy |
| CSP directives | `script-src 'self'` | Security rules |
| Permission scopes | `read:users`, `write:admin` | Access control |

## Implementation Notes

### Detection Patterns

Use these regex patterns to identify protected content:

```python
PROTECTED_PATTERNS = [
    r"Bearer\s+\S+",           # Auth tokens
    r"api[_-]?key[:\s]+\S+",   # API keys
    r"password[:\s]+\S+",      # Passwords
    r"secret[:\s]+\S+",        # Secrets
    r"https?://[^\s]+",        # URLs
    r"`[^`]+`",                # Inline code
    r"```[\s\S]*?```",         # Code blocks
    r'"[^"]*"',                # Quoted strings
    r"'[^']*'",                # Single-quoted
    r"\b[0-9a-f]{8}-[0-9a-f]{4}", # UUIDs
    r"v\d+\.\d+\.\d+",         # Versions
]
```

### Placeholder Strategy

When compressing, replace protected content w/ placeholders:
1. Scan for protected patterns
2. Replace w/ `__PROTECTED_N__`
3. Apply compression to non-protected text
4. Restore protected content

### Manual Override

If user explicitly requests compression of protected content:
1. Warn about risks
2. Require confirmation
3. Log the override