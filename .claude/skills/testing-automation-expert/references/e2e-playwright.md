# E2E Testing with Playwright

## Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html'], ['list']],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile', use: { ...devices['iPhone 14'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('User Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should login successfully', async ({ page }) => {
    await page.getByLabel('Email').fill('user@test.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome back')).toBeVisible();
  });

  test('should show error on invalid credentials', async ({ page }) => {
    await page.getByLabel('Email').fill('invalid@test.com');
    await page.getByLabel('Password').fill('wrong');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page.getByRole('alert')).toHaveText('Invalid credentials');
  });
});
```

## Locator Strategies

```typescript
// Preferred: Role-based (accessible)
page.getByRole('button', { name: 'Submit' });
page.getByRole('link', { name: 'Home' });
page.getByRole('textbox', { name: 'Email' });
page.getByRole('checkbox', { name: 'Remember me' });

// Text-based
page.getByText('Welcome');
page.getByText(/welcome/i);  // regex

// Label-based (forms)
page.getByLabel('Email');
page.getByPlaceholder('Enter email');

// Test IDs (when semantic locators don't work)
page.getByTestId('submit-btn');

// CSS/XPath (last resort)
page.locator('.btn-primary');
page.locator('//button[@type="submit"]');

// Chaining
page.getByRole('listitem').filter({ hasText: 'Product A' }).getByRole('button');
```

## Page Object Model

```typescript
// tests/e2e/pages/login.page.ts
import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitBtn: Locator;
  readonly errorMsg: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitBtn = page.getByRole('button', { name: 'Sign In' });
    this.errorMsg = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitBtn.click();
  }

  async expectError(message: string) {
    await expect(this.errorMsg).toHaveText(message);
  }
}

// tests/e2e/pages/dashboard.page.ts
export class DashboardPage {
  readonly page: Page;
  readonly welcomeMsg: Locator;
  readonly logoutBtn: Locator;

  constructor(page: Page) {
    this.page = page;
    this.welcomeMsg = page.getByTestId('welcome-message');
    this.logoutBtn = page.getByRole('button', { name: 'Logout' });
  }

  async expectWelcome(name: string) {
    await expect(this.welcomeMsg).toContainText(name);
  }
}

// Usage in tests
test('login flow', async ({ page }) => {
  const loginPage = new LoginPage(page);
  const dashboard = new DashboardPage(page);

  await loginPage.goto();
  await loginPage.login('user@test.com', 'password123');
  await dashboard.expectWelcome('John');
});
```

## Fixtures

```typescript
// tests/e2e/fixtures.ts
import { test as base, Page } from '@playwright/test';
import { LoginPage } from './pages/login.page';
import { DashboardPage } from './pages/dashboard.page';

type Fixtures = {
  loginPage: LoginPage;
  dashboard: DashboardPage;
  authenticatedPage: Page;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  dashboard: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  authenticatedPage: async ({ page }, use) => {
    // Pre-authenticate
    await page.goto('/login');
    await page.getByLabel('Email').fill('user@test.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('/dashboard');
    await use(page);
  },
});

export { expect } from '@playwright/test';

// Usage
import { test, expect } from './fixtures';

test('dashboard loads', async ({ authenticatedPage }) => {
  await expect(authenticatedPage.getByText('Dashboard')).toBeVisible();
});
```

## API Mocking

```typescript
test('handles API error', async ({ page }) => {
  // Mock API response
  await page.route('**/api/users', (route) => {
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Server error' }),
    });
  });

  await page.goto('/users');
  await expect(page.getByText('Failed to load users')).toBeVisible();
});

test('mocks user data', async ({ page }) => {
  await page.route('**/api/users/1', (route) => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({ id: 1, name: 'Test User' }),
    });
  });

  await page.goto('/users/1');
  await expect(page.getByText('Test User')).toBeVisible();
});

// Modify request
await page.route('**/api/**', (route) => {
  route.continue({
    headers: { ...route.request().headers(), 'X-Test-Header': 'value' },
  });
});

// Abort request
await page.route('**/analytics/**', (route) => route.abort());
```

## Authentication State

```typescript
// Save auth state
// scripts/global-setup.ts
import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto('http://localhost:3000/login');
  await page.getByLabel('Email').fill('admin@test.com');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Sign In' }).click();
  await page.waitForURL('/dashboard');

  // Save storage state
  await page.context().storageState({ path: './tests/e2e/.auth/admin.json' });
  await browser.close();
}

export default globalSetup;

// playwright.config.ts
export default defineConfig({
  globalSetup: require.resolve('./scripts/global-setup'),
  projects: [
    { name: 'setup', testMatch: /global-setup\.ts/ },
    {
      name: 'authenticated',
      use: { storageState: './tests/e2e/.auth/admin.json' },
      dependencies: ['setup'],
    },
  ],
});
```

## Visual Testing

```typescript
test('homepage visual regression', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png');
});

test('component snapshot', async ({ page }) => {
  await page.goto('/components');
  const card = page.getByTestId('user-card');
  await expect(card).toHaveScreenshot('user-card.png', {
    maxDiffPixels: 100,
    threshold: 0.2,
  });
});

// Update snapshots: npx playwright test --update-snapshots
```

## Assertions

```typescript
// Page assertions
await expect(page).toHaveURL('/dashboard');
await expect(page).toHaveTitle(/Dashboard/);
await expect(page).toHaveScreenshot();

// Locator assertions
await expect(locator).toBeVisible();
await expect(locator).toBeHidden();
await expect(locator).toBeEnabled();
await expect(locator).toBeDisabled();
await expect(locator).toBeChecked();
await expect(locator).toBeFocused();
await expect(locator).toHaveText('Hello');
await expect(locator).toContainText('Hello');
await expect(locator).toHaveValue('input value');
await expect(locator).toHaveAttribute('href', '/home');
await expect(locator).toHaveClass(/active/);
await expect(locator).toHaveCount(5);
await expect(locator).toHaveCSS('color', 'rgb(0, 0, 0)');

// Soft assertions (don't stop on failure)
await expect.soft(locator).toHaveText('Hello');
await expect.soft(locator).toBeVisible();
```

## Actions

```typescript
// Click
await page.click('button');
await page.dblclick('button');
await page.click('button', { button: 'right' });
await page.click('button', { modifiers: ['Shift'] });

// Type
await page.fill('input', 'text');
await page.type('input', 'text', { delay: 100 });
await page.press('input', 'Enter');

// Select
await page.selectOption('select', 'value');
await page.selectOption('select', { label: 'Option' });

// Check
await page.check('input[type="checkbox"]');
await page.uncheck('input[type="checkbox"]');

// Upload
await page.setInputFiles('input[type="file"]', 'path/to/file.pdf');

// Drag
await page.dragAndDrop('#source', '#target');

// Hover
await page.hover('.menu');

// Focus
await page.focus('input');
```

## Waiting

```typescript
// Auto-waiting (preferred - built into actions)
await page.click('button');  // waits for element

// Explicit waits
await page.waitForURL('/dashboard');
await page.waitForSelector('.loaded');
await page.waitForLoadState('networkidle');
await page.waitForResponse('**/api/users');
await page.waitForFunction(() => document.title === 'Done');

// Custom timeout
await page.click('button', { timeout: 10000 });

// Wait for multiple
await Promise.all([
  page.waitForNavigation(),
  page.click('a[href="/next"]'),
]);
```

## Network

```typescript
// Intercept requests
page.on('request', (request) => {
  console.log(request.url(), request.method());
});

// Intercept responses
page.on('response', (response) => {
  console.log(response.url(), response.status());
});

// Wait for specific request
const [response] = await Promise.all([
  page.waitForResponse('**/api/submit'),
  page.click('#submit'),
]);
expect(response.status()).toBe(200);

// HAR recording
await page.routeFromHAR('tests/data/api.har', { update: true });
```

## Directory Structure

```
tests/
└── e2e/
    ├── fixtures.ts          # Custom fixtures
    ├── pages/               # Page objects
    │   ├── login.page.ts
    │   ├── dashboard.page.ts
    │   └── settings.page.ts
    ├── specs/               # Test files
    │   ├── auth.spec.ts
    │   ├── dashboard.spec.ts
    │   └── settings.spec.ts
    ├── .auth/               # Auth state (gitignored)
    │   └── admin.json
    └── screenshots/         # Visual snapshots
        └── homepage.png
```

## Commands

```bash
npx playwright test                    # Run all
npx playwright test auth.spec.ts       # Specific file
npx playwright test --project=chromium # Specific browser
npx playwright test --headed           # Show browser
npx playwright test --debug            # Debug mode
npx playwright test --ui               # UI mode
npx playwright show-report             # View report
npx playwright codegen                 # Record tests
npx playwright test --update-snapshots # Update screenshots
```

## CI Configuration

### Basic CI

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

### Sharding (Parallel CI Machines)

For test suites >10 minutes - split across multiple CI machines:

```yaml
# .github/workflows/e2e-sharded.yml
name: E2E Tests (Sharded)
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shard: [1/4, 2/4, 3/4, 4/4]  # 4 parallel machines
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test --shard=${{ matrix.shard }}
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report-${{ strategy.job-index }}
          path: playwright-report/

  merge-reports:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          pattern: playwright-report-*
          path: all-reports
      - run: npx playwright merge-reports --reporter=html ./all-reports
      - uses: actions/upload-artifact@v4
        with:
          name: playwright-report-merged
          path: playwright-report/
```

### Trace Artifacts (Debugging CI Failures)

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    trace: 'on-first-retry',      // Capture trace on retry
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  retries: process.env.CI ? 2 : 0,
});
```

```yaml
# Upload traces for debugging
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-traces
    path: |
      test-results/**/trace.zip
      test-results/**/*.png
      test-results/**/*.webm
    retention-days: 7
```

**Debugging traces locally:**
```bash
# Open trace viewer
npx playwright show-trace test-results/*/trace.zip
```

### Docker for Consistent Screenshots

Visual regression across Mac/Linux differences:

```dockerfile
# Dockerfile.playwright
FROM mcr.microsoft.com/playwright:v1.40.0-jammy
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
```

```yaml
# CI with Docker
- name: Run E2E in Docker
  run: |
    docker build -f Dockerfile.playwright -t e2e-tests .
    docker run --rm -v $(pwd)/test-results:/app/test-results e2e-tests \
      npx playwright test --update-snapshots
```

### Flakiness Dashboard

```yaml
# Track flaky tests over time
- name: Upload Test Results
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: test-results/

# Use Playwright's built-in flaky test detection
- run: npx playwright test --retries=3 --reporter=json > results.json
```

```typescript
// playwright.config.ts - Quarantine flaky tests
export default defineConfig({
  projects: [
    { name: 'stable', testIgnore: /\.flaky\.spec\.ts/ },
    { name: 'flaky', testMatch: /\.flaky\.spec\.ts/, retries: 3 },
  ],
});
```

## Required Packages

```bash
npm init playwright@latest
# or
npm install -D @playwright/test
npx playwright install
```

## Python (pytest-playwright)

```python
# conftest.py
import pytest
from playwright.sync_api import Page

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1920, "height": 1080}}

# tests/test_auth.py
def test_login(page: Page):
    page.goto("/login")
    page.get_by_label("Email").fill("user@test.com")
    page.get_by_label("Password").fill("password123")
    page.get_by_role("button", name="Sign In").click()

    expect(page).to_have_url("/dashboard")

# Async version
import pytest
from playwright.async_api import Page

@pytest.mark.asyncio
async def test_login_async(page: Page):
    await page.goto("/login")
    await page.get_by_label("Email").fill("user@test.com")
```

```bash
pip install pytest-playwright
playwright install
```