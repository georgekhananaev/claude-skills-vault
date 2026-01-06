# TypeScript Testing with Jest

## Configuration

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: ['**/*.test.ts', '**/*.spec.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: ['src/**/*.ts', '!src/**/*.d.ts'],
  coverageThreshold: {
    global: { branches: 80, functions: 80, lines: 80, statements: 80 },
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  clearMocks: true,
  restoreMocks: true,
};
```

```json
// tsconfig.json (test specific)
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "types": ["jest", "node"]
  },
  "include": ["tests/**/*", "src/**/*"]
}
```

## Basic Test Structure

```typescript
// tests/services/user.service.test.ts
import { UserService } from '@/services/user.service';
import { UserRepository } from '@/repositories/user.repository';

describe('UserService', () => {
  let userService: UserService;
  let mockRepo: jest.Mocked<UserRepository>;

  beforeEach(() => {
    mockRepo = {
      findById: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
    } as jest.Mocked<UserRepository>;

    userService = new UserService(mockRepo);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('getUser', () => {
    it('should return user when found', async () => {
      const mockUser = { id: '1', email: 'test@test.com' };
      mockRepo.findById.mockResolvedValue(mockUser);

      const result = await userService.getUser('1');

      expect(result).toEqual(mockUser);
      expect(mockRepo.findById).toHaveBeenCalledWith('1');
    });

    it('should throw when user not found', async () => {
      mockRepo.findById.mockResolvedValue(null);

      await expect(userService.getUser('1')).rejects.toThrow('User not found');
    });
  });
});
```

## Mocking

### Mock Functions

```typescript
// Simple mock
const mockFn = jest.fn();
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
```

### Mock Modules

```typescript
// Auto-mock entire module
jest.mock('@/services/email.service');

// Partial mock
jest.mock('@/utils/logger', () => ({
  ...jest.requireActual('@/utils/logger'),
  error: jest.fn(),
}));

// Mock with factory
jest.mock('@/config', () => ({
  config: {
    apiUrl: 'http://test-api.com',
    timeout: 1000,
  },
}));
```

### Mock Classes

```typescript
// Mock class
jest.mock('@/services/email.service');
const MockEmailService = EmailService as jest.MockedClass<typeof EmailService>;

beforeEach(() => {
  MockEmailService.mockClear();
  MockEmailService.prototype.send.mockResolvedValue(true);
});
```

### Spies

```typescript
const spy = jest.spyOn(userService, 'validateEmail');

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

// Callbacks (legacy)
it('should callback with data', (done) => {
  fetchData((err, data) => {
    expect(err).toBeNull();
    expect(data).toBeDefined();
    done();
  });
});
```

## Matchers

```typescript
// Equality
expect(value).toBe(exact);           // ===
expect(value).toEqual(deep);         // Deep equal
expect(value).toStrictEqual(strict); // Deep + type

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
// tests/setup.ts
import { prisma } from '@/lib/prisma';

beforeAll(async () => {
  await prisma.$connect();
});

afterAll(async () => {
  await prisma.$disconnect();
});

beforeEach(async () => {
  await prisma.user.deleteMany();
});

// Per-file setup
describe('UserAPI', () => {
  let app: Express;

  beforeAll(() => {
    app = createApp();
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
// Built-in fake timers
beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

it('should timeout after 5s', () => {
  const callback = jest.fn();
  setTimeout(callback, 5000);

  jest.advanceTimersByTime(5000);

  expect(callback).toHaveBeenCalled();
});

// Mock Date
jest.useFakeTimers().setSystemTime(new Date('2024-01-15'));
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
import { User } from '@/types';

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

## Commands

```bash
npm test                    # Run all
npm test -- --watch         # Watch mode
npm test -- --coverage      # Coverage
npm test -- user.test.ts    # Specific file
npm test -- -t "should"     # Match test name
npm test -- --updateSnapshot # Update snapshots
```

## Required Packages

```bash
npm install -D jest ts-jest @types/jest
npm install -D supertest @types/supertest
npm install -D @faker-js/faker
```
