# Authentication

## Auth.js (NextAuth v5) Setup

### Installation

```bash
npm install next-auth@beta
npx auth secret # Generate AUTH_SECRET
```

### Configuration

```typescript
// auth.ts (root)
import NextAuth from "next-auth"
import GitHub from "next-auth/providers/github"
import Google from "next-auth/providers/google"
import Credentials from "next-auth/providers/credentials"
import { PrismaAdapter } from "@auth/prisma-adapter"
import { db } from "@/lib/db/client"
import bcrypt from "bcryptjs"
import { z } from "zod"

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

export const { handlers, signIn, signOut, auth } = NextAuth({
  adapter: PrismaAdapter(db),
  session: { strategy: "jwt" },
  pages: {
    signIn: "/login",
    error: "/auth/error",
  },
  providers: [
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID,
      clientSecret: process.env.GITHUB_CLIENT_SECRET,
    }),
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const validated = loginSchema.safeParse(credentials)
        if (!validated.success) return null

        const { email, password } = validated.data

        const user = await db.user.findUnique({
          where: { email },
          select: { id: true, email: true, name: true, password: true },
        })

        if (!user?.password) return null

        const isValid = await bcrypt.compare(password, user.password)
        if (!isValid) return null

        return { id: user.id, email: user.email, name: user.name }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id
        // Fetch role from database
        const dbUser = await db.user.findUnique({
          where: { id: user.id },
          select: { role: true },
        })
        token.role = dbUser?.role ?? "user"
      }
      return token
    },
    async session({ session, token }) {
      if (token) {
        session.user.id = token.id as string
        session.user.role = token.role as string
      }
      return session
    },
    async authorized({ auth, request }) {
      const isLoggedIn = !!auth?.user
      const isOnDashboard = request.nextUrl.pathname.startsWith("/dashboard")

      if (isOnDashboard) {
        if (isLoggedIn) return true
        return false // Redirect to login
      }

      return true
    },
  },
})
```

### Type Extensions

```typescript
// types/next-auth.d.ts
import { DefaultSession, DefaultUser } from "next-auth"
import { JWT as DefaultJWT } from "next-auth/jwt"

declare module "next-auth" {
  interface Session {
    user: {
      id: string
      role: string
    } & DefaultSession["user"]
  }

  interface User extends DefaultUser {
    role?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id?: string
    role?: string
  }
}
```

### API Route Handler

```typescript
// app/api/auth/[...nextauth]/route.ts
import { handlers } from "@/auth"

export const { GET, POST } = handlers
```

## Middleware Protection

```typescript
// middleware.ts
import { auth } from "@/auth"
import { NextResponse } from "next/server"

// Routes that don't require auth
const publicRoutes = ["/", "/login", "/register", "/api/auth"]

// Routes requiring specific roles
const adminRoutes = ["/admin"]

export default auth((req) => {
  const { nextUrl, auth } = req
  const isLoggedIn = !!auth?.user
  const pathname = nextUrl.pathname

  // Allow public routes
  const isPublicRoute = publicRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  )
  if (isPublicRoute) return NextResponse.next()

  // Require authentication
  if (!isLoggedIn) {
    const loginUrl = new URL("/login", nextUrl)
    loginUrl.searchParams.set("callbackUrl", pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Check admin routes
  const isAdminRoute = adminRoutes.some((route) => pathname.startsWith(route))
  if (isAdminRoute && auth?.user?.role !== "admin") {
    return NextResponse.redirect(new URL("/unauthorized", nextUrl))
  }

  return NextResponse.next()
})

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
}
```

## Server-Side Auth Checks

### In Server Components

```typescript
// app/dashboard/page.tsx
import { auth } from "@/auth"
import { redirect } from "next/navigation"

export default async function DashboardPage() {
  const session = await auth()

  if (!session) {
    redirect("/login")
  }

  return (
    <div>
      <h1>Welcome, {session.user.name}</h1>
      <p>Role: {session.user.role}</p>
    </div>
  )
}
```

### In Server Actions

```typescript
// features/posts/actions/create-post.ts
"use server"

import { auth } from "@/auth"
import { z } from "zod"
import { revalidateTag } from "next/cache"

const createPostSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(1),
})

export async function createPost(input: z.infer<typeof createPostSchema>) {
  // 1. Auth check - ALWAYS in Server Actions
  const session = await auth()
  if (!session?.user) {
    return { success: false, error: "Unauthorized" }
  }

  // 2. Validate input
  const validated = createPostSchema.safeParse(input)
  if (!validated.success) {
    return { success: false, error: "Invalid input" }
  }

  // 3. Authorization (optional - check ownership, roles, etc.)
  // ...

  // 4. Perform mutation
  const post = await db.post.create({
    data: {
      ...validated.data,
      authorId: session.user.id,
    },
  })

  // 5. Revalidate
  revalidateTag("posts")

  return { success: true, data: post }
}
```

## Client-Side Auth

### Session Provider

```typescript
// app/providers.tsx
"use client"

import { SessionProvider } from "next-auth/react"

export function Providers({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>
}

// app/layout.tsx
import { Providers } from "./providers"

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

### useSession Hook

```typescript
// components/UserMenu.interactive.tsx
"use client"

import { useSession, signIn, signOut } from "next-auth/react"

export function UserMenu() {
  const { data: session, status } = useSession()

  if (status === "loading") {
    return <div>Loading...</div>
  }

  if (!session) {
    return (
      <button onClick={() => signIn()}>Sign In</button>
    )
  }

  return (
    <div>
      <span>{session.user.name}</span>
      <button onClick={() => signOut()}>Sign Out</button>
    </div>
  )
}
```

## Login/Register Forms

### Login Form

```typescript
// features/auth/components/LoginForm.interactive.tsx
"use client"

import { useActionState } from "react"
import { useFormStatus } from "react-dom"
import { login } from "../actions/login"

const initialState = { error: null }

export function LoginForm() {
  const [state, formAction] = useActionState(login, initialState)

  return (
    <form action={formAction} className="space-y-4">
      {state.error && (
        <div className="text-red-500">{state.error}</div>
      )}

      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
        />
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoComplete="current-password"
        />
      </div>

      <SubmitButton />

      <div className="text-center">
        <button
          type="button"
          onClick={() => signIn("github", { callbackUrl: "/dashboard" })}
        >
          Sign in with GitHub
        </button>
      </div>
    </form>
  )
}

function SubmitButton() {
  const { pending } = useFormStatus()

  return (
    <button type="submit" disabled={pending}>
      {pending ? "Signing in..." : "Sign In"}
    </button>
  )
}
```

### Login Action

```typescript
// features/auth/actions/login.ts
"use server"

import { signIn } from "@/auth"
import { AuthError } from "next-auth"
import { z } from "zod"

const loginSchema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Password required"),
})

export async function login(prevState: any, formData: FormData) {
  const validated = loginSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  })

  if (!validated.success) {
    return { error: validated.error.errors[0].message }
  }

  try {
    await signIn("credentials", {
      email: validated.data.email,
      password: validated.data.password,
      redirectTo: "/dashboard",
    })
  } catch (error) {
    if (error instanceof AuthError) {
      switch (error.type) {
        case "CredentialsSignin":
          return { error: "Invalid email or password" }
        default:
          return { error: "Something went wrong" }
      }
    }
    throw error
  }
}
```

### Register Action

```typescript
// features/auth/actions/register.ts
"use server"

import { db } from "@/lib/db/client"
import bcrypt from "bcryptjs"
import { z } from "zod"

const registerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Password must contain uppercase letter")
    .regex(/[0-9]/, "Password must contain number"),
})

export async function register(prevState: any, formData: FormData) {
  const validated = registerSchema.safeParse({
    name: formData.get("name"),
    email: formData.get("email"),
    password: formData.get("password"),
  })

  if (!validated.success) {
    return {
      error: validated.error.errors[0].message,
      fieldErrors: validated.error.flatten().fieldErrors,
    }
  }

  const { name, email, password } = validated.data

  // Check if user exists
  const existingUser = await db.user.findUnique({
    where: { email },
  })

  if (existingUser) {
    return { error: "Email already registered" }
  }

  // Hash password
  const hashedPassword = await bcrypt.hash(password, 12)

  // Create user
  await db.user.create({
    data: {
      name,
      email,
      password: hashedPassword,
    },
  })

  return { success: true }
}
```

## Role-Based Access Control (RBAC)

### Database Schema

```prisma
enum Role {
  USER
  EDITOR
  ADMIN
}

model User {
  id    String @id
  role  Role   @default(USER)
  // ...
}
```

### Permission Checking

```typescript
// lib/auth/permissions.ts
type Permission = "posts:read" | "posts:write" | "users:manage" | "admin:access"

const rolePermissions: Record<string, Permission[]> = {
  USER: ["posts:read"],
  EDITOR: ["posts:read", "posts:write"],
  ADMIN: ["posts:read", "posts:write", "users:manage", "admin:access"],
}

export function hasPermission(role: string, permission: Permission): boolean {
  return rolePermissions[role]?.includes(permission) ?? false
}

// Usage in Server Action
export async function deletePost(postId: string) {
  const session = await auth()
  if (!session?.user) {
    return { error: "Unauthorized" }
  }

  if (!hasPermission(session.user.role, "posts:write")) {
    return { error: "Insufficient permissions" }
  }

  // ... delete post
}
```

### Server Component with RBAC

```typescript
// app/admin/page.tsx
import { auth } from "@/auth"
import { redirect } from "next/navigation"
import { hasPermission } from "@/lib/auth/permissions"

export default async function AdminPage() {
  const session = await auth()

  if (!session) {
    redirect("/login")
  }

  if (!hasPermission(session.user.role, "admin:access")) {
    redirect("/unauthorized")
  }

  return <AdminDashboard />
}
```

## Session Strategies

| Strategy | Pros | Cons |
|----------|------|------|
| **JWT** | Stateless, scalable | Can't revoke instantly, larger cookies |
| **Database** | Revocable, smaller cookies | DB lookup per request |

### JWT Strategy (Default)

```typescript
// auth.ts
export const { handlers, auth } = NextAuth({
  session: { strategy: "jwt" },
  // ...
})
```

### Database Strategy

```typescript
// auth.ts
export const { handlers, auth } = NextAuth({
  adapter: PrismaAdapter(db),
  session: {
    strategy: "database",
    maxAge: 30 * 24 * 60 * 60, // 30 days
    updateAge: 24 * 60 * 60, // 24 hours
  },
  // ...
})
```

## Security Best Practices

### Password Hashing

```typescript
import bcrypt from "bcryptjs"

// Hash with sufficient rounds (12+)
const hash = await bcrypt.hash(password, 12)

// Compare securely
const isValid = await bcrypt.compare(password, hash)
```

### CSRF Protection

Auth.js handles CSRF automatically for Server Actions. For custom API routes:

```typescript
// app/api/protected/route.ts
import { auth } from "@/auth"

export async function POST(request: Request) {
  const session = await auth()
  if (!session) {
    return new Response("Unauthorized", { status: 401 })
  }

  // CSRF token is validated automatically by Auth.js
  // ...
}
```

### Rate Limiting

```typescript
// features/auth/actions/login.ts
import { Ratelimit } from "@upstash/ratelimit"
import { Redis } from "@upstash/redis"
import { headers } from "next/headers"

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(5, "1 m"), // 5 attempts per minute
})

export async function login(prevState: any, formData: FormData) {
  const headersList = await headers()
  const ip = headersList.get("x-forwarded-for") ?? "127.0.0.1"

  const { success, remaining } = await ratelimit.limit(ip)

  if (!success) {
    return { error: "Too many attempts. Please try again later." }
  }

  // ... rest of login logic
}
```

### Secure Cookie Settings

```typescript
// auth.ts
export const { handlers, auth } = NextAuth({
  cookies: {
    sessionToken: {
      name: "__Secure-authjs.session-token",
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: process.env.NODE_ENV === "production",
      },
    },
  },
  // ...
})
```

## Auth Checklist

- [ ] Use Auth.js v5 (beta) for Next.js 14+
- [ ] Store passwords with bcrypt (12+ rounds)
- [ ] Always verify auth in Server Actions
- [ ] Implement rate limiting on auth endpoints
- [ ] Use httpOnly, secure cookies
- [ ] Set up proper CORS for API routes
- [ ] Implement RBAC for protected resources
- [ ] Add email verification for new accounts
- [ ] Set appropriate session expiry times
- [ ] Log authentication events for auditing