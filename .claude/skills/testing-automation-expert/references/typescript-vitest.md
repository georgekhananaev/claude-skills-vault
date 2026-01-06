# TypeScript Testing with Vitest

## Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node', // or 'jsdom' for browser
    include: ['src/**/*.{test,spec}.ts', 'tests/**/*.{test,spec}.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.ts'],
      exclude: ['src/**/*.d.ts', 'src/**/*.test.ts'],
      thresholds: { branches: 80, functions: 80, lines: 80, statements: 80 },
    },
    setupFiles: ['./tests/setup.ts'],
    mockReset: true,
    restoreMocks: true,
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
});
```

```json
// tsconfig.json additions
{
  "compilerOptions": {
    "types": ["vitest/globals", "node"]
  }
}
```

## Basic Test Structure

```typescript
// tests/services/user.service.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UserService } from '@/services/user.service';
import type { UserRepository } from '@/repositories/user.repository';

describe('UserService', () => {
  let userService: UserService;
  let mockRepo: UserRepository;

  beforeEach(() => {
    mockRepo = {
      findById: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    };
    userService = new UserService(mockRepo);
  });

  describe('getUser', () => {
    it('should return user when found', async () => {
      const mockUser = { id: '1', email: 'test@test.com' };
      vi.mocked(mockRepo.findById).mockResolvedValue(mockUser);

      const result = await userService.getUser('1');

      expect(result).toEqual(mockUser);
      expect(mockRepo.findById).toHaveBeenCalledWith('1');
    });

    it('should throw when user not found', async () => {
      vi.mocked(mockRepo.findById).mockResolvedValue(null);

      await expect(userService.getUser('1')).rejects.toThrow('User not found');
    });
  });
});
```

## Testcontainers (Real DB)

Superior to mocking for integration tests - real PostgreSQL/Redis/etc:

```typescript
// tests/setup/testcontainers.ts
import { PostgreSqlContainer, StartedPostgreSqlContainer } from '@testcontainers/postgresql';
import { beforeAll, afterAll } from 'vitest';

let postgresContainer: StartedPostgreSqlContainer;

beforeAll(async () => {
  postgresContainer = await new PostgreSqlContainer('postgres:16-alpine')
    .withDatabase('test_db')
    .start();

  process.env.DATABASE_URL = postgresContainer.getConnectionUri();
}, 60000);  // 60s timeout for container startup

afterAll(async () => {
  await postgresContainer.stop();
});

// tests/integration/user.repository.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { PrismaClient } from '@prisma/client';
import { UserRepository } from '@/repositories/user.repository';

describe('UserRepository (Integration)', () => {
  let prisma: PrismaClient;
  let repo: UserRepository;

  beforeEach(async () => {
    prisma = new PrismaClient({ datasources: { db: { url: process.env.DATABASE_URL } } });
    repo = new UserRepository(prisma);
    await prisma.user.deleteMany();  // Clean state
  });

  it('should create and retrieve user', async () => {
    const user = await repo.create({ email: 'test@test.com', name: 'Test' });
    const found = await repo.findById(user.id);

    expect(found).toEqual(user);
  });
});
```

```bash
npm install -D @testcontainers/postgresql
# Also available: @testcontainers/redis, @testcontainers/mongodb, etc.
```

## Mocking

### Mock Functions

```typescript
import { vi } from 'vitest';

// Simple mock
const mockFn = vi.fn();
mockFn.mockReturnValue('value');
mockFn.mockResolvedValue('async value');
mockFn.mockRejectedValue(new Error('fail'));

// Implementation
mockFn.mockImplementation((x) => x * 2);

// Chain returns
mockFn
  .mockReturnValueOnce('first')
  .mockReturnValueOnce('second')
  .mockReturnValue('default');

// Type-safe mocking
vi.mocked(mockFn).mockReturnValue('typed');
```

### Mock Modules

```typescript
// Auto-mock module
vi.mock('@/services/email.service');

// Partial mock
vi.mock('@/utils/logger', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/utils/logger')>();
  return { ...actual, error: vi.fn() };
});

// Factory mock
vi.mock('@/config', () => ({
  config: { apiUrl: 'http://test-api.com', timeout: 1000 },
}));

// Hoisted mock (for ESM)
const mockSend = vi.hoisted(() => vi.fn());
vi.mock('@/services/email.service', () => ({
  EmailService: vi.fn(() => ({ send: mockSend })),
}));
```

### Spies

```typescript
const spy = vi.spyOn(userService, 'validateEmail');

userService.createUser('test@test.com');

expect(spy).toHaveBeenCalledWith('test@test.com');
spy.mockRestore();
```

## Async Testing

```typescript
// Async/await
it('should fetch user', async () => {
  const user = await userService.getUser('1');
  expect(user).toBeDefined();
});

// Promises
it('should reject invalid id', () => {
  return expect(userService.getUser('')).rejects.toThrow('Invalid ID');
});

// Concurrent tests
it.concurrent('test 1', async () => { /* ... */ });
it.concurrent('test 2', async () => { /* ... */ });
```

## Matchers

```typescript
// Equality
expect(value).toBe(exact);           // ===
expect(value).toEqual(deep);         // Deep equal
expect(value).toStrictEqual(strict); // Deep + undefined props

// Truthiness
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeNull();
expect(value).toBeUndefined();
expect(value).toBeDefined();

// Numbers
expect(num).toBeGreaterThan(3);
expect(num).toBeLessThanOrEqual(5);
expect(0.1 + 0.2).toBeCloseTo(0.3);

// Strings
expect(str).toMatch(/regex/);
expect(str).toContain('substring');

// Arrays/Objects
expect(arr).toContain(item);
expect(arr).toHaveLength(3);
expect(obj).toHaveProperty('key', 'value');
expect(obj).toMatchObject({ partial: 'match' });

// Errors
expect(() => fn()).toThrow();
expect(() => fn()).toThrow('message');
expect(() => fn()).toThrow(CustomError);

// Mocks
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledTimes(2);
expect(mockFn).toHaveBeenCalledWith(arg1, arg2);
expect(mockFn).toHaveBeenLastCalledWith(arg);

// Snapshots
expect(component).toMatchSnapshot();
expect(data).toMatchInlineSnapshot(`{ "id": 1 }`);
```

## Setup & Teardown

```typescript
// tests/setup.ts (global)
import { beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { prisma } from '@/lib/prisma';

beforeAll(async () => {
  await prisma.$connect();
});

afterAll(async () => {
  await prisma.$disconnect();
});

// Per-file setup
describe('UserAPI', () => {
  let app: Express;

  beforeAll(() => {
    app = createApp();
  });

  beforeEach(async () => {
    await prisma.user.deleteMany();
  });

  // tests...
});
```

## Testing HTTP (Supertest)

```typescript
import request from 'supertest';
import { app } from '@/app';

describe('GET /api/users', () => {
  it('should return users', async () => {
    const response = await request(app)
      .get('/api/users')
      .set('Authorization', 'Bearer token')
      .expect('Content-Type', /json/)
      .expect(200);

    expect(response.body).toHaveLength(2);
  });

  it('should create user', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ email: 'new@test.com', password: 'pass123' })
      .expect(201);

    expect(response.body.email).toBe('new@test.com');
  });
});
```

## Time Mocking

```typescript
import { vi, beforeEach, afterEach } from 'vitest';

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

it('should timeout after 5s', () => {
  const callback = vi.fn();
  setTimeout(callback, 5000);

  vi.advanceTimersByTime(5000);

  expect(callback).toHaveBeenCalled();
});

// Set specific date
vi.setSystemTime(new Date('2024-01-15'));
```

## In-Source Testing

```typescript
// src/utils/math.ts
export function add(a: number, b: number) {
  return a + b;
}

// In-source tests (dev only)
if (import.meta.vitest) {
  const { describe, it, expect } = import.meta.vitest;

  describe('add', () => {
    it('adds two numbers', () => {
      expect(add(1, 2)).toBe(3);
    });
  });
}
```

Enable in config:
```typescript
// vitest.config.ts
export default defineConfig({
  test: { includeSource: ['src/**/*.ts'] },
  define: { 'import.meta.vitest': 'undefined' }, // strip in prod
});
```

## Directory Structure

```
tests/
├── setup.ts                 # Global setup
├── factories/               # Test data factories
│   └── user.factory.ts
├── fixtures/                # Static test data
│   └── users.json
├── unit/
│   ├── services/
│   │   └── user.service.test.ts
│   └── utils/
│       └── validator.test.ts
├── integration/
│   └── api/
│       └── users.test.ts
└── e2e/
    └── auth.flow.test.ts
```

## Test Factories

```typescript
// tests/factories/user.factory.ts
import { faker } from '@faker-js/faker';
import type { User } from '@/types';

export const createUser = (overrides: Partial<User> = {}): User => ({
  id: faker.string.uuid(),
  email: faker.internet.email(),
  name: faker.person.fullName(),
  createdAt: new Date(),
  ...overrides,
});

// Usage
const user = createUser({ role: 'admin' });
```

## Vitest vs Jest

| Feature | Vitest | Jest |
|---------|--------|------|
| Speed | Faster (native ESM) | Slower |
| Config | Vite-based | Separate |
| HMR | Yes | No |
| TypeScript | Native | ts-jest |
| ESM | Native | Experimental |
| API | Jest-compatible | - |
| In-source | Yes | No |
| Browser mode | Yes | jsdom only |

## Commands

```bash
npx vitest                   # Run in watch mode
npx vitest run               # Run once
npx vitest run --coverage    # Coverage
npx vitest user.test.ts      # Specific file
npx vitest -t "should"       # Match test name
npx vitest --update          # Update snapshots
npx vitest --ui              # Browser UI
npx vitest bench             # Benchmarks
```

## Required Packages

```bash
npm install -D vitest @vitest/coverage-v8
npm install -D supertest @types/supertest
npm install -D @faker-js/faker
npm install -D @vitest/ui  # optional UI
```