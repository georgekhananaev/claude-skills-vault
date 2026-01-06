# Specialized Testing Patterns

## Contract Testing (Pact)

Consumer-Driven Contract Testing (CDCT) for microservices - ensures service boundaries respected without full environments.

### Python Consumer

```python
# tests/contract/test_user_consumer.py
import pytest
from pact import Consumer, Provider

@pytest.fixture(scope="session")
def pact():
    pact = Consumer("UserService").has_pact_with(
        Provider("AuthService"),
        pact_dir="./pacts"
    )
    pact.start_service()
    yield pact
    pact.stop_service()

def test_get_user_auth(pact):
    expected = {"user_id": "123", "role": "admin", "valid": True}

    (pact
        .given("user 123 exists and is admin")
        .upon_receiving("a request for user auth")
        .with_request("GET", "/auth/user/123")
        .will_respond_with(200, body=expected))

    with pact:
        result = auth_client.get_user_auth("123")
        assert result["role"] == "admin"
```

### Python Provider Verification

```python
# tests/contract/test_auth_provider.py
from pact import Verifier

def test_provider_against_contracts():
    verifier = Verifier(
        provider="AuthService",
        provider_base_url="http://localhost:8000"
    )

    output, _ = verifier.verify_pacts(
        "./pacts/userservice-authservice.json",
        provider_states_setup_url="http://localhost:8000/_pact/setup"
    )
    assert output == 0
```

### TypeScript Consumer

```typescript
// tests/contract/user.consumer.spec.ts
import { PactV3, MatchersV3 } from '@pact-foundation/pact';
import { UserClient } from '@/clients/user.client';

const { like, eachLike } = MatchersV3;

const provider = new PactV3({
  consumer: 'Frontend',
  provider: 'UserAPI',
  dir: './pacts',
});

describe('User API Contract', () => {
  it('returns user by ID', async () => {
    await provider
      .given('user 123 exists')
      .uponReceiving('a request for user 123')
      .withRequest({ method: 'GET', path: '/api/users/123' })
      .willRespondWith({
        status: 200,
        body: like({ id: '123', name: 'John', email: 'john@test.com' }),
      });

    await provider.executeTest(async (mockServer) => {
      const client = new UserClient(mockServer.url);
      const user = await client.getUser('123');
      expect(user.id).toBe('123');
    });
  });
});
```

### Pact Broker (CI/CD)

```yaml
# .github/workflows/contract.yml
- name: Publish Pacts
  run: |
    pact-broker publish ./pacts \
      --broker-base-url=$PACT_BROKER_URL \
      --consumer-app-version=$GITHUB_SHA

- name: Can I Deploy?
  run: |
    pact-broker can-i-deploy \
      --pacticipant=UserService \
      --version=$GITHUB_SHA \
      --to-environment=production
```

```bash
# Packages
pip install pact-python
npm install -D @pact-foundation/pact
```

---

## Accessibility Testing (axe-core)

Automated a11y checks - mandatory for modern QA.

### Playwright + axe-core

```typescript
// tests/e2e/a11y/dashboard.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
  test('dashboard has no critical a11y violations', async ({ page }) => {
    await page.goto('/dashboard');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(results.violations).toEqual([]);
  });

  test('login form is accessible', async ({ page }) => {
    await page.goto('/login');

    const results = await new AxeBuilder({ page })
      .include('#login-form')
      .exclude('#captcha')  // Skip known issues
      .analyze();

    // Allow minor violations, fail on critical
    const critical = results.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious'
    );
    expect(critical).toHaveLength(0);
  });
});
```

### pytest + axe-core

```python
# tests/e2e/test_accessibility.py
import pytest
from playwright.sync_api import Page
from axe_playwright_python.sync_playwright import Axe

def test_homepage_a11y(page: Page):
    page.goto("/")
    axe = Axe()
    results = axe.run(page)

    violations = [v for v in results["violations"]
                  if v["impact"] in ("critical", "serious")]
    assert len(violations) == 0, f"A11y violations: {violations}"
```

### CI Integration

```yaml
# Report a11y issues without failing build (initially)
- name: A11y Audit
  run: npx playwright test --grep @a11y
  continue-on-error: true

- name: Upload A11y Report
  uses: actions/upload-artifact@v4
  with:
    name: a11y-report
    path: test-results/a11y/
```

```bash
# Packages
npm install -D @axe-core/playwright
pip install axe-playwright-python
```

---

## API Fuzzing (Schemathesis)

Property-based testing for OpenAPI/FastAPI endpoints.

```python
# tests/fuzz/test_api_fuzz.py
import schemathesis

schema = schemathesis.from_uri("http://localhost:8000/openapi.json")

@schema.parametrize()
def test_api_endpoint(case):
    """Auto-generates tests from OpenAPI spec."""
    response = case.call()
    case.validate_response(response)

# Targeted endpoint fuzzing
@schema.parametrize(endpoint="/api/users", method="POST")
def test_user_creation(case):
    response = case.call()
    case.validate_response(response)

    if response.status_code == 201:
        assert "id" in response.json()

# Stateful testing (sequences of API calls)
@schema.parametrize()
def test_stateful_api(case):
    case.call_and_validate()
```

### CLI Usage

```bash
# Fuzz all endpoints
schemathesis run http://localhost:8000/openapi.json

# Target specific endpoint
schemathesis run http://localhost:8000/openapi.json \
  --endpoint /api/users \
  --method POST

# Generate test cases for replay
schemathesis run http://localhost:8000/openapi.json \
  --cassette-path=test_cases.yaml

# Auth header
schemathesis run http://localhost:8000/openapi.json \
  --header "Authorization: Bearer $TOKEN"
```

```bash
pip install schemathesis
```

---

## Mutation Testing

Validate test quality by introducing bugs and checking detection.

### Python (mutmut)

```toml
# pyproject.toml
[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "pytest"
```

```bash
# Run mutation testing
mutmut run

# View results
mutmut results
mutmut show <id>

# Generate HTML report
mutmut html
```

### TypeScript (Stryker)

```json
// stryker.conf.json
{
  "$schema": "https://raw.githubusercontent.com/stryker-mutator/stryker/master/packages/core/schema/stryker-core.json",
  "mutate": ["src/**/*.ts", "!src/**/*.spec.ts"],
  "testRunner": "vitest",
  "reporters": ["html", "clear-text", "progress"],
  "coverageAnalysis": "perTest",
  "thresholds": { "high": 80, "low": 60, "break": 50 }
}
```

```bash
npx stryker run
```

### Interpreting Results

| Score | Meaning |
|-------|---------|
| 80%+ | Strong test suite |
| 60-80% | Needs improvement |
| <60% | Critical gaps |

**Surviving mutants indicate:**
- Missing assertions
- Inadequate edge case coverage
- Potential security risks

```bash
# Packages
pip install mutmut
npm install -D @stryker-mutator/core @stryker-mutator/vitest-runner
```

---

## Performance Testing Integration

### k6 (JavaScript-based)

```javascript
// tests/load/api-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },  // Ramp up
    { duration: '1m', target: 20 },   // Hold
    { duration: '10s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% under 500ms
    http_req_failed: ['rate<0.01'],    // <1% errors
  },
};

export default function () {
  const res = http.get('http://localhost:8000/api/users');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });
  sleep(1);
}
```

```bash
k6 run tests/load/api-load.js
```

### Locust (Python)

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_users(self):
        self.client.get("/api/users")

    @task(1)
    def create_user(self):
        self.client.post("/api/users", json={
            "email": "test@example.com",
            "name": "Test User"
        })
```

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

```bash
# Packages
brew install k6  # or download from k6.io
pip install locust
```

---

## Security Testing (Basic)

### OWASP ZAP Integration

```yaml
# .github/workflows/security.yml
- name: OWASP ZAP Scan
  uses: zaproxy/action-baseline@v0.10.0
  with:
    target: 'http://localhost:3000'
    rules_file_name: '.zap/rules.tsv'
    allow_issue_writing: false
```

### Security Headers Check

```typescript
// tests/security/headers.spec.ts
test('API has security headers', async ({ request }) => {
  const response = await request.get('/api/health');

  expect(response.headers()['x-content-type-options']).toBe('nosniff');
  expect(response.headers()['x-frame-options']).toBe('DENY');
  expect(response.headers()['strict-transport-security']).toBeDefined();
});
```

---

## Recommended Packages Summary

### Python
```bash
pip install pact-python schemathesis mutmut locust
pip install axe-playwright-python
```

### TypeScript/Node
```bash
npm install -D @pact-foundation/pact
npm install -D @axe-core/playwright
npm install -D @stryker-mutator/core @stryker-mutator/vitest-runner
```