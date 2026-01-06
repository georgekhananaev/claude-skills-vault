# Documentation Patterns

Use these patterns when a codebase lacks documentation structure.

## Minimal Viable Docs Structure

```
docs/
├── README.md              # Index of all documentation
├── architecture.md        # System overview
├── types.md               # Data types reference
├── style-guide.md         # Codebase conventions
├── features/              # Feature specifications
│   └── _template.md
└── adr/                   # Architecture Decision Records
    └── _template.md
```

## Pattern: docs/README.md (Index)

````markdown
# Project Documentation

## Overview
Brief description of what this project does.

## Quick Links
- [Architecture](./architecture.md)
- [Data Types](./types.md)
- [Style Guide](./style-guide.md)
- [Features](./features/)
- [Architecture Decisions](./adr/)

## Getting Started
Link to setup guide or inline instructions.
````

## Pattern: docs/architecture.md

````markdown
# Architecture Overview

## System Context
What this system does and how it fits into the larger ecosystem.

## High-Level Components
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Server    │────▶│  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Key Technologies
- **Frontend**: [framework, libraries]
- **Backend**: [language, framework]
- **Database**: [type, name]
- **Infrastructure**: [hosting, services]

## Directory Structure
```
src/
├── components/    # UI components
├── services/      # Business logic
├── models/        # Data models
└── utils/         # Shared utilities
```

## Data Flow
Describe how data moves through the system.

## External Integrations
List third-party services and their purposes.
````

## Pattern: docs/features/_template.md

````markdown
# Feature: [Name]

## Summary
One-line description of what this feature does.

## User Story
As a [user type], I want to [action] so that [benefit].

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Implementation Notes
Key files and components involved:
- `src/components/FeatureName/`
- `src/services/featureService.ts`

## API Endpoints (if applicable)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | /api/... | Fetches...  |
| POST   | /api/... | Creates...  |

## Related
- Link to related features
- Link to relevant ADRs
````

## Pattern: docs/adr/_template.md (Architecture Decision Record)

````markdown
# ADR-[NUMBER]: [Title]

**Date**: YYYY-MM-DD
**Status**: [Proposed | Accepted | Deprecated | Superseded]

## Context
What is the issue or decision we need to make?

## Decision
What decision was made?

## Consequences
### Positive
- Benefit 1
- Benefit 2

### Negative
- Tradeoff 1
- Tradeoff 2

## Alternatives Considered
1. **Alternative A**: Why rejected
2. **Alternative B**: Why rejected
````

## Fallback: When No ADRs Exist

If codebase lacks formal ADRs, extract decision context from:

### Alternative Sources

| Source | What to Look For |
|--------|------------------|
| `CHANGELOG.md` | Breaking changes, major version bumps w/ rationale |
| `git log` | Commit messages for large refactors, migrations |
| PR/MR descriptions | Discussion threads on architectural changes |
| Issue tracker | Closed issues tagged "architecture", "RFC", "proposal" |
| Release notes | "Why we changed X" explanations |
| Blog posts | Engineering blog posts about the project |
| Comments in code | `// DECISION:`, `// WHY:`, `// NOTE:` prefixes |

### Extracting Decisions from Changelog

Look for entries like:
```markdown
## [2.0.0] - 2024-01-15
### Changed
- **BREAKING**: Migrated from REST to GraphQL for better query flexibility
- Switched from MongoDB to PostgreSQL for ACID compliance
```

### Extracting from Git History

```bash
# Find commits with architectural keywords
git log --all --grep="migrate" --grep="refactor" --grep="replace" --oneline

# Find large changes (likely architectural)
git log --stat --diff-filter=A -- "*.config.*" "docker*" "**/schema.*"

# View decision context in commit messages
git log --format="%h %s%n%b" --grep="because" --grep="decided" --grep="chose"
```

### Reconstructing ADRs

When documenting implicit decisions, create retroactive ADRs:

````markdown
# ADR-001: [Reconstructed] Migration to TypeScript

**Date**: Reconstructed from git history (original: ~2023-06)
**Status**: Accepted (implemented)

## Context
(Extracted from PR #234 and CHANGELOG v1.5.0)

Team faced increasing type-related bugs in production.
JavaScript codebase had grown to 50k+ LOC.

## Decision
Migrate entire codebase from JavaScript to TypeScript.

## Evidence
- PR #234: "Add TypeScript support"
- CHANGELOG v1.5.0: "Migrated to TypeScript for type safety"
- Commit abc123: "chore: initial tsconfig setup"
````

### Code Comment Patterns for Implicit Decisions

Search codebase for decision markers:

```bash
# Common decision comment patterns
grep -r "// DECISION" --include="*.ts" --include="*.js"
grep -r "// WHY:" --include="*.ts" --include="*.js"
grep -r "// NOTE:" --include="*.ts" --include="*.js"
grep -r "// HACK:" --include="*.ts" --include="*.js"  # Often explains constraints
grep -r "TODO.*because" --include="*.ts" --include="*.js"
```

## Pattern: API Documentation

````markdown
# API Reference

## Authentication
Describe auth method (JWT, API key, etc.)

## Base URL
```
Production: https://api.example.com/v1
Development: http://localhost:3000/api
```

## Endpoints

### Resource Name

#### GET /resource
Fetch all resources.

**Response**
```json
{
  "data": [],
  "meta": { "total": 0 }
}
```

#### POST /resource
Create new resource.

**Request Body**
```json
{
  "name": "string",
  "value": "number"
}
```
````

## Pattern: Database Schema

````markdown
# Database Schema

## Entity Relationship

```
┌─────────┐       ┌─────────┐
│  User   │──────<│  Order  │
└─────────┘       └─────────┘
     │                 │
     │            ┌────┴────┐
     │            ▼         ▼
     │       ┌────────┐ ┌────────┐
     └──────>│ Profile│ │  Item  │
             └────────┘ └────────┘
```

## Tables

### users
| Column     | Type         | Constraints      |
|------------|--------------|------------------|
| id         | UUID         | PK               |
| email      | VARCHAR(255) | UNIQUE, NOT NULL |
| created_at | TIMESTAMP    | DEFAULT NOW()    |

### orders
| Column  | Type      | Constraints          |
|---------|-----------|----------------------|
| id      | UUID      | PK                   |
| user_id | UUID      | FK → users.id        |
| status  | ENUM      | DEFAULT 'pending'    |
````

## Pattern: Data Types / Models

````markdown
# Data Types Reference

## Core Entities

### User
```typescript
interface User {
  id: string;           // UUID v4
  email: string;        // Unique, lowercase
  role: UserRole;       // 'admin' | 'user' | 'guest'
  profile: Profile;     // One-to-one relation
  createdAt: Date;
  updatedAt: Date;
}
```

### Order
```typescript
interface Order {
  id: string;
  userId: string;       // FK → User.id
  status: OrderStatus;  // 'pending' | 'confirmed' | 'cancelled'
  items: OrderItem[];   // One-to-many
  total: number;        // Calculated, stored in cents
  currency: string;     // ISO 4217 (USD, EUR, etc.)
}
```

## Enums

### UserRole
| Value   | Description              |
|---------|--------------------------|
| admin   | Full system access       |
| user    | Standard authenticated   |
| guest   | Limited read-only        |

### OrderStatus
| Value     | Description                | Next States        |
|-----------|----------------------------|--------------------|
| pending   | Awaiting confirmation      | confirmed, cancelled |
| confirmed | Payment received           | shipped, cancelled |
| shipped   | In transit                 | delivered          |
| delivered | Complete                   | —                  |
| cancelled | Terminated                 | —                  |

## Value Objects

### Money
```typescript
type Money = {
  amount: number;    // Integer, smallest unit (cents)
  currency: string;  // ISO 4217
}
```

### Address
```typescript
type Address = {
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postalCode: string;
  country: string;   // ISO 3166-1 alpha-2
}
```

## Validation Rules

| Field        | Rule                          |
|--------------|-------------------------------|
| email        | Valid email format, lowercase |
| password     | Min 8 chars, 1 upper, 1 number |
| phone        | E.164 format                  |
| currency     | ISO 4217 (3 letters)          |
| country      | ISO 3166-1 alpha-2            |

## Type Relationships

```
User ──────── 1:1 ──────── Profile
  │
  └── 1:N ──── Order ──── 1:N ──── OrderItem
                │                      │
                └── N:1 ────────── Product
```
````

## Pattern: Codebase Style Guide

````markdown
# Codebase Style Guide

## Naming Conventions

### Files & Directories
| Type           | Convention        | Example                    |
|----------------|-------------------|----------------------------|
| Components     | PascalCase        | `UserProfile.tsx`          |
| Hooks          | camelCase, use-   | `useAuth.ts`               |
| Utilities      | camelCase         | `formatDate.ts`            |
| Constants      | SCREAMING_SNAKE   | `API_ENDPOINTS.ts`         |
| Types/Models   | PascalCase        | `User.ts`, `OrderTypes.ts` |
| Directories    | kebab-case        | `user-profile/`            |

### Code Identifiers
| Type           | Convention        | Example                    |
|----------------|-------------------|----------------------------|
| Variables      | camelCase         | `userData`, `isLoading`    |
| Functions      | camelCase         | `fetchUser()`, `handleClick()` |
| Classes        | PascalCase        | `UserService`              |
| Interfaces     | PascalCase        | `UserProfile`              |
| Type aliases   | PascalCase        | `UserId`, `OrderStatus`    |
| Enums          | PascalCase        | `UserRole`                 |
| Enum members   | PascalCase        | `UserRole.Admin`           |
| Constants      | SCREAMING_SNAKE   | `MAX_RETRIES`, `API_URL`   |
| Private fields | _camelCase        | `_internalState`           |

### Naming Patterns
| Pattern              | Use for                    | Example                    |
|----------------------|----------------------------|----------------------------|
| `is/has/can/should`  | Booleans                   | `isActive`, `hasPermission`|
| `handle*`            | Event handlers             | `handleSubmit`, `handleClick` |
| `on*`                | Callback props             | `onSuccess`, `onChange`    |
| `get/fetch`          | Data retrieval             | `getUser()`, `fetchOrders()` |
| `set/update`         | Data mutation              | `setUser()`, `updateOrder()` |
| `create/delete`      | CRUD operations            | `createUser()`, `deleteOrder()` |
| `*Service`           | Service classes            | `AuthService`, `EmailService` |
| `*Repository`        | Data access                | `UserRepository`           |
| `*Controller`        | Request handlers           | `UserController`           |
| `*Middleware`        | Middleware functions       | `AuthMiddleware`           |
| `use*`               | React hooks                | `useAuth()`, `useForm()`   |
| `with*`              | HOCs                       | `withAuth()`, `withLayout()` |

## Project Structure

```
src/
├── components/          # UI components
│   ├── common/          # Shared/reusable
│   └── features/        # Feature-specific
├── hooks/               # Custom React hooks
├── services/            # Business logic, API calls
├── models/              # Types, interfaces, schemas
├── utils/               # Pure utility functions
├── constants/           # App-wide constants
├── config/              # Configuration files
├── styles/              # Global styles, themes
└── tests/               # Test utilities, mocks
```

## Import Order

```typescript
// 1. External packages
import React from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. Internal aliases (@/)
import { Button } from '@/components/common';
import { useAuth } from '@/hooks';

// 3. Relative imports
import { UserCard } from './UserCard';
import { formatName } from './utils';

// 4. Types (type-only imports last)
import type { User } from '@/models';
```

## Component Structure

```typescript
// 1. Types
interface Props {
  user: User;
  onUpdate: (user: User) => void;
}

// 2. Component
export function UserProfile({ user, onUpdate }: Props) {
  // 2a. Hooks
  const { t } = useTranslation();
  const [isEditing, setIsEditing] = useState(false);

  // 2b. Derived state
  const fullName = `${user.firstName} ${user.lastName}`;

  // 2c. Effects
  useEffect(() => {
    // ...
  }, [user.id]);

  // 2d. Handlers
  const handleSave = () => {
    // ...
  };

  // 2e. Render
  return (
    <div>...</div>
  );
}
```

## Error Handling Pattern

```typescript
// Service layer - throw typed errors
class UserService {
  async getUser(id: string): Promise<User> {
    const user = await db.user.find(id);
    if (!user) throw new NotFoundError('User', id);
    return user;
  }
}

// API layer - catch and format
async function handler(req, res) {
  try {
    const user = await userService.getUser(req.params.id);
    return res.json(user);
  } catch (error) {
    if (error instanceof NotFoundError) {
      return res.status(404).json({ error: error.message });
    }
    throw error; // Let global handler catch
  }
}
```

## Comment Standards

```typescript
// ✅ Good: Explains WHY
// Retry 3 times because external API has intermittent failures
const MAX_RETRIES = 3;

// ❌ Bad: Explains WHAT (obvious from code)
// Set max retries to 3
const MAX_RETRIES = 3;

/**
 * Calculates shipping cost based on destination and weight.
 *
 * @param destination - ISO country code
 * @param weightKg - Package weight in kilograms
 * @returns Shipping cost in cents (USD)
 *
 * @example
 * calculateShipping('US', 2.5) // => 1500
 */
function calculateShipping(destination: string, weightKg: number): number
```
````

## Quick Setup Commands

Create minimal docs structure:

```bash
mkdir -p docs/{features,adr}
touch docs/README.md docs/architecture.md docs/types.md docs/style-guide.md
touch docs/features/_template.md docs/adr/_template.md
```

Or use the init script:

```bash
python3 scripts/init_docs.py [project-path]
```
