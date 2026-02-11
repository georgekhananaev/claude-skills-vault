# TypeScript Standards

Strict TypeScript with zero `any` tolerance.

## Core Principles

- **No `any`**: Use `unknown`, generics, or proper types
- **No type assertions**: Use type guards instead
- **Strict mode**: All `strict` flags enabled
- **Exhaustive checks**: Use `never` for switch exhaustiveness

## Type Safety Rules

### Never Use `any`

```typescript
// CRITICAL: Never use any
const bad: any = data;           // Error
const good: unknown = data;      // OK - forces type checking

// If you need flexibility, use generics
function process<T>(data: T): T {
    return data;
}
```

### No Type Assertions

```typescript
// CRITICAL: No type assertions without runtime checks
const bad = data as User;        // Error - no runtime check

// Use type guards
function isUser(data: unknown): data is User {
    return typeof data === 'object' && data !== null && 'id' in data;
}
const good = isUser(data) ? data : null;  // OK - runtime verified
```

### No Non-Null Assertions

```typescript
// ERROR: Non-null assertions hide bugs
const bad = user!.name;          // Error

// Use optional chaining + nullish coalescing
const good = user?.name ?? '';   // OK
const alsoGood = user?.name;     // OK if undefined acceptable
```

### Explicit Return Types

```typescript
// ERROR: Missing return type on public functions
export function process(x: number) {  // Error
    return x * 2;
}

// OK: Explicit return type
export function process(x: number): number {  // OK
    return x * 2;
}

// Private/internal functions can infer
const helper = (x: number) => x * 2;  // OK - inferred
```

## ESLint Configuration (Strict)

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/strict-type-checked",
    "plugin:jsx-a11y/strict"
  ],
  "plugins": ["jsx-a11y"],
  "parserOptions": {
    "project": "./tsconfig.json"
  },
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unsafe-assignment": "error",
    "@typescript-eslint/no-unsafe-member-access": "error",
    "@typescript-eslint/no-unsafe-return": "error",
    "@typescript-eslint/no-unsafe-call": "error",
    "@typescript-eslint/no-unsafe-argument": "error",
    "@typescript-eslint/strict-boolean-expressions": "error",
    "@typescript-eslint/no-floating-promises": "error",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/explicit-function-return-type": ["error", {
      "allowExpressions": true,
      "allowTypedFunctionExpressions": true
    }],
    "@typescript-eslint/consistent-type-imports": ["error", {
      "prefer": "type-imports"
    }],
    "@typescript-eslint/no-non-null-assertion": "error",
    "@typescript-eslint/prefer-nullish-coalescing": "error",
    "@typescript-eslint/prefer-optional-chain": "error",
    "complexity": ["error", { "max": 10 }],
    "max-depth": ["error", 3],
    "max-lines-per-function": ["warn", { "max": 50, "skipBlankLines": true }],
    "eqeqeq": ["error", "always"],
    "no-console": "warn",
    "no-debugger": "error",
    "no-eval": "error",
    "no-implied-eval": "error"
  }
}
```

## tsconfig.json (Strict)

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "useUnknownInCatchVariables": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noPropertyAccessFromIndexSignature": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  }
}
```

## Accessibility (jsx-a11y)

When using JSX/React:

```typescript
// ERROR: Missing alt text
<img src={url} />                    // Error

// OK: Descriptive alt
<img src={url} alt="User avatar" />  // OK

// ERROR: Non-interactive elements with click handlers
<div onClick={handleClick}>...</div>  // Error

// OK: Use button or add role
<button onClick={handleClick}>...</button>  // OK
<div role="button" tabIndex={0} onClick={handleClick} onKeyDown={handleKey}>...</div>  // OK

// ERROR: Form inputs without labels
<input type="text" />                // Error

// OK: Associated label
<label>
  Name
  <input type="text" />
</label>  // OK
```

## Type Patterns

### Exhaustive Switch

```typescript
type Status = 'pending' | 'active' | 'disabled';

function handleStatus(status: Status): string {
    switch (status) {
        case 'pending':
            return 'Waiting...';
        case 'active':
            return 'Running';
        case 'disabled':
            return 'Stopped';
        default:
            // Compile error if new status added
            const _exhaustive: never = status;
            throw new Error(`Unhandled status: ${_exhaustive}`);
    }
}
```

### Discriminated Unions

```typescript
type Result<T, E = Error> =
    | { success: true; data: T }
    | { success: false; error: E };

function handle<T>(result: Result<T>): T {
    if (result.success) {
        return result.data;  // TypeScript knows data exists
    }
    throw result.error;  // TypeScript knows error exists
}
```

### Type-Safe Event Handlers

```typescript
type EventMap = {
    'user:login': { userId: string };
    'user:logout': { userId: string; reason?: string };
};

function emit<K extends keyof EventMap>(
    event: K,
    payload: EventMap[K]
): void {
    // Type-safe event emission
}

emit('user:login', { userId: '123' });  // OK
emit('user:login', { wrong: true });    // Error
```

## Anti-Patterns

| Bad | Good | Why |
|-----|------|-----|
| `any` | `unknown` | Forces type checking |
| `as Type` | Type guard | Runtime verification |
| `!` non-null | `?.` + `??` | Handles null safely |
| `== null` | `=== null` | Strict equality |
| Implicit returns | Explicit types | Self-documenting |
| `Function` type | Specific signature | Type safety |
| `Object` type | `Record<K,V>` | Precise typing |

## Imports

```typescript
// Type-only imports (tree-shaking friendly)
import type { User, Config } from './types';

// Mixed imports
import { createUser, type UserInput } from './users';

// Organize: external → internal → types
import { z } from 'zod';
import { db } from '@/lib/db';
import type { User } from '@/types';
```
