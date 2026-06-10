# Code Quality & Best Practices

## Error Handling Strategy

### Error Boundary Hierarchy

```
app/
├── global-error.tsx    # Fatal errors (root layout failures)
├── error.tsx           # App-wide errors
├── (app)/
│   ├── error.tsx       # Authenticated section errors
│   └── dashboard/
│       └── error.tsx   # Route-specific errors
```

### Error Boundary Implementation

```tsx
// app/error.tsx
"use client"

import { useEffect } from "react"
import { reportError } from "@/lib/monitoring"

interface ErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log to error reporting service
    reportError(error, { digest: error.digest })
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <h2 className="text-xl font-semibold mb-4">Something went wrong</h2>
      <p className="text-muted-foreground mb-4">
        {process.env.NODE_ENV === "development"
          ? error.message
          : "An unexpected error occurred"}
      </p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-primary text-primary-foreground rounded"
      >
        Try again
      </button>
    </div>
  )
}
```

### Global Error (Root Layout Failures)

```tsx
// app/global-error.tsx
"use client"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <h2>Something went wrong!</h2>
        <button onClick={reset}>Try again</button>
      </body>
    </html>
  )
}
```

### Server Action Error Handling

```typescript
// lib/safe-action.ts
type ActionResult<T> =
  | { success: true; data: T }
  | { success: false; error: string; code?: string }

// NEVER expose internal errors to client
export function createSafeAction<TInput, TOutput>(
  schema: z.Schema<TInput>,
  handler: (data: TInput, userId: string) => Promise<TOutput>
) {
  return async (input: TInput): Promise<ActionResult<TOutput>> => {
    "use server"

    try {
      // ... validation, auth
      const data = await handler(result.data, session.user.id)
      return { success: true, data }
    } catch (error) {
      // Log full error internally
      console.error("[ACTION_ERROR]", error)

      // Return sanitized error to client
      if (error instanceof AppError) {
        return { success: false, error: error.userMessage, code: error.code }
      }

      return { success: false, error: "Something went wrong" }
    }
  }
}

// Custom error classes
export class AppError extends Error {
  constructor(
    public userMessage: string,
    public code: string,
    public internalMessage?: string
  ) {
    super(internalMessage || userMessage)
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, "NOT_FOUND")
  }
}

export class UnauthorizedError extends AppError {
  constructor() {
    super("You don't have permission", "UNAUTHORIZED")
  }
}
```

## State Management Hierarchy

Choose the right tool for the job:

| State Type | Tool | Example |
|------------|------|---------|
| URL State | `searchParams`, `useSearchParams` | Filters, pagination, tabs |
| Server State | Server Components, fetch | User data, posts |
| Form State | `useActionState` (React 19; replaces deprecated `useFormState`), `useFormStatus` | Form submissions |
| UI State | `useState` | Modals, dropdowns |
| Shared Client State | Context or Zustand | Theme, cart |

### URL State (Preferred for Shareable State)

```tsx
// app/products/page.tsx
interface Props {
  searchParams: Promise<{ category?: string; sort?: string; page?: string }>
}

export default async function ProductsPage({ searchParams }: Props) {
  const params = await searchParams
  const { category, sort = "newest", page = "1" } = params

  const products = await getProducts({ category, sort, page: parseInt(page) })

  return (
    <>
      <FilterBar category={category} sort={sort} />
      <ProductGrid products={products} />
      <Pagination currentPage={parseInt(page)} />
    </>
  )
}

// components/FilterBar.interactive.tsx
"use client"

import { useRouter, useSearchParams, usePathname } from "next/navigation"

export function FilterBar({ category, sort }: Props) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const updateParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString())
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    params.set("page", "1") // Reset pagination
    router.push(`${pathname}?${params.toString()}`)
  }

  return (
    <select
      value={sort}
      onChange={(e) => updateParam("sort", e.target.value)}
    >
      <option value="newest">Newest</option>
      <option value="price-asc">Price: Low to High</option>
      <option value="price-desc">Price: High to Low</option>
    </select>
  )
}
```

### Form State with useActionState (React 19; replaces useFormState)

```tsx
// features/contact/components/ContactForm.interactive.tsx
"use client"

import { useActionState } from "react"
import { useFormStatus } from "react-dom"
import { submitContact } from "../actions/submit-contact"

const initialState = { success: false, error: null }

export function ContactForm() {
  const [state, formAction] = useActionState(submitContact, initialState)

  return (
    <form action={formAction}>
      {state.error && (
        <div className="text-red-500">{state.error}</div>
      )}
      {state.success && (
        <div className="text-green-500">Message sent!</div>
      )}

      <input name="email" type="email" required />
      <textarea name="message" required />

      <SubmitButton />
    </form>
  )
}

function SubmitButton() {
  const { pending } = useFormStatus()

  return (
    <button type="submit" disabled={pending}>
      {pending ? "Sending..." : "Send Message"}
    </button>
  )
}
```

### Shared Client State (When Needed)

```tsx
// lib/stores/cart-store.ts
import { create } from "zustand"
import { persist } from "zustand/middleware"

interface CartItem {
  id: string
  quantity: number
}

interface CartStore {
  items: CartItem[]
  addItem: (id: string) => void
  removeItem: (id: string) => void
  clear: () => void
}

export const useCartStore = create<CartStore>()(
  persist(
    (set) => ({
      items: [],
      addItem: (id) =>
        set((state) => {
          const existing = state.items.find((item) => item.id === id)
          if (existing) {
            return {
              items: state.items.map((item) =>
                item.id === id
                  ? { ...item, quantity: item.quantity + 1 }
                  : item
              ),
            }
          }
          return { items: [...state.items, { id, quantity: 1 }] }
        }),
      removeItem: (id) =>
        set((state) => ({
          items: state.items.filter((item) => item.id !== id),
        })),
      clear: () => set({ items: [] }),
    }),
    { name: "cart-storage" }
  )
)
```

## TypeScript Strict Patterns

### tsconfig.json

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

### Type-Safe Props

```tsx
// Always type props explicitly
interface UserCardProps {
  user: User
  onEdit?: (user: User) => void
  className?: string
}

export function UserCard({ user, onEdit, className }: UserCardProps) {
  // ...
}

// Use satisfies for type checking with inference
const config = {
  apiUrl: process.env.API_URL,
  timeout: 5000,
} satisfies Config
```

### Type-Safe Server Actions

```typescript
// features/posts/actions/create-post.ts
"use server"

import { z } from "zod"

const createPostSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(1).max(10000),
  published: z.boolean().default(false),
})

type CreatePostInput = z.infer<typeof createPostSchema>

export async function createPost(
  input: CreatePostInput
): Promise<ActionResult<Post>> {
  // Zod validates at runtime, TypeScript at compile time
  const validated = createPostSchema.parse(input)
  // ...
}
```

### Type-Safe API Responses

```typescript
// types/api.ts
export type ApiResponse<T> =
  | { success: true; data: T }
  | { success: false; error: ApiError }

export interface ApiError {
  message: string
  code: string
  details?: Record<string, string[]>
}

// lib/api/client.ts
export async function fetchApi<T>(
  url: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(url, options)

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error }
    }

    const data = await response.json()
    return { success: true, data }
  } catch {
    return {
      success: false,
      error: { message: "Network error", code: "NETWORK_ERROR" },
    }
  }
}
```

## Testing Strategy

### Testing Pyramid for Next.js

```
        /\
       /  \   E2E (Playwright)
      /    \  - Critical user journeys
     /------\ - Auth flows, checkout
    /        \ Integration (Vitest + Testing Library)
   /          \ - Page renders with data
  /            \ - Server Action flows
 /--------------\ Unit (Vitest)
/                \ - Utilities, hooks
/------------------\ - Business logic
```

### Unit Tests

```typescript
// lib/utils/__tests__/format.test.ts
import { describe, it, expect } from "vitest"
import { formatCurrency, formatDate } from "../format"

describe("formatCurrency", () => {
  it("formats USD by default", () => {
    expect(formatCurrency(1234.56)).toBe("$1,234.56")
  })

  it("handles zero", () => {
    expect(formatCurrency(0)).toBe("$0.00")
  })
})
```

### Component Tests

```tsx
// features/auth/components/__tests__/LoginForm.test.tsx
import { render, screen, fireEvent } from "@testing-library/react"
import { LoginForm } from "../LoginForm.interactive"

describe("LoginForm", () => {
  it("shows validation errors for empty fields", async () => {
    render(<LoginForm />)

    fireEvent.click(screen.getByRole("button", { name: /sign in/i }))

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument()
  })

  it("disables submit while pending", async () => {
    // Mock the server action
    const mockLogin = vi.fn(() => new Promise(() => {})) // Never resolves

    render(<LoginForm loginAction={mockLogin} />)

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: "test@example.com" },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    })
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }))

    expect(screen.getByRole("button")).toBeDisabled()
  })
})
```

### E2E Tests

```typescript
// e2e/auth.spec.ts
import { test, expect } from "@playwright/test"

test.describe("Authentication", () => {
  test("user can sign in", async ({ page }) => {
    await page.goto("/login")

    await page.fill('[name="email"]', "test@example.com")
    await page.fill('[name="password"]', "password123")
    await page.click('button[type="submit"]')

    await expect(page).toHaveURL("/dashboard")
    await expect(page.getByText("Welcome back")).toBeVisible()
  })

  test("protected routes redirect to login", async ({ page }) => {
    await page.goto("/dashboard")

    await expect(page).toHaveURL(/\/login\?callbackUrl/)
  })
})
```

## Accessibility Patterns

### Semantic HTML First

```tsx
// WRONG: div soup
<div onClick={handleClick}>
  <div className="title">Products</div>
  <div className="list">
    {products.map(p => <div key={p.id}>{p.name}</div>)}
  </div>
</div>

// RIGHT: Semantic elements
<section aria-labelledby="products-heading">
  <h2 id="products-heading">Products</h2>
  <ul role="list">
    {products.map(p => (
      <li key={p.id}>
        <a href={`/products/${p.id}`}>{p.name}</a>
      </li>
    ))}
  </ul>
</section>
```

### Focus Management

```tsx
"use client"

import { useRef, useEffect } from "react"

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  children: React.ReactNode
}

export function Modal({ isOpen, onClose, children }: ModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (isOpen) {
      closeButtonRef.current?.focus()
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <button
        ref={closeButtonRef}
        onClick={onClose}
        aria-label="Close modal"
      >
        &times;
      </button>
      {children}
    </div>
  )
}
```

### Loading & Error States

```tsx
// Always communicate state to assistive technology
function DataTable({ data, isLoading, error }) {
  if (isLoading) {
    return (
      <div role="status" aria-live="polite">
        <span className="sr-only">Loading data...</span>
        <Skeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div role="alert">
        <p>Error loading data: {error.message}</p>
      </div>
    )
  }

  return (
    <table aria-label="User data">
      {/* ... */}
    </table>
  )
}
```

## Senior-Level Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Prop drilling 5+ levels | Maintenance nightmare | Context or composition |
| "use client" at route level | No SSR benefits | Push to leaves |
| Catching all errors silently | Hides bugs | Log + user feedback |
| `any` types | No type safety | Proper types or `unknown` |
| Barrel exports everywhere | Slow builds, tree-shaking | Direct imports |
| Over-abstraction | Hard to understand | YAGNI principle |
| Copy-paste validation | Inconsistent, buggy | Shared schemas |
| Inline styles for theming | Hard to maintain | CSS variables |
| setTimeout for data sync | Race conditions | Server state tools |
| localStorage for auth | XSS vulnerable | httpOnly cookies |

## Code Review Checklist

### Before Merging

**Performance**
- [ ] No unnecessary "use client"
- [ ] Images use next/image with dimensions
- [ ] Heavy components are dynamic imported
- [ ] No N+1 queries

**Security**
- [ ] Server Actions validate input with Zod
- [ ] Auth checked in actions, not just middleware
- [ ] No secrets in client bundles
- [ ] IDOR prevention (user owns resource)

**Quality**
- [ ] No `any` types
- [ ] Error boundaries for async components
- [ ] Loading states for async operations
- [ ] Tests for critical paths

**Accessibility**
- [ ] Semantic HTML used
- [ ] Images have alt text
- [ ] Interactive elements are focusable
- [ ] Color contrast meets WCAG AA

**Maintenance**
- [ ] No dead code
- [ ] DRY (but not prematurely)
- [ ] Clear naming
- [ ] Appropriate comments (why, not what)

## Logging Standards

### Structured Logging

```typescript
// lib/logger.ts
type LogLevel = "debug" | "info" | "warn" | "error"

interface LogEntry {
  level: LogLevel
  message: string
  timestamp: string
  context?: Record<string, unknown>
  userId?: string
  requestId?: string
}

export function log(
  level: LogLevel,
  message: string,
  context?: Record<string, unknown>
) {
  const entry: LogEntry = {
    level,
    message,
    timestamp: new Date().toISOString(),
    context,
  }

  // In development, pretty print
  if (process.env.NODE_ENV === "development") {
    console[level](JSON.stringify(entry, null, 2))
    return
  }

  // In production, structured JSON for log aggregation
  console[level](JSON.stringify(entry))
}

// Usage
log("info", "User signed in", { userId: user.id, method: "oauth" })
log("error", "Payment failed", { orderId, error: error.message })
```

### What to Log

| Event | Level | Include |
|-------|-------|---------|
| User sign in/out | info | userId, method |
| API errors | error | endpoint, status, requestId |
| Slow queries | warn | query, duration, table |
| Security events | warn | action, userId, IP |
| Business events | info | action, entityId, userId |

### What NOT to Log

- Passwords or tokens
- Full credit card numbers
- PII (unless required and encrypted)
- Request/response bodies with sensitive data