# Supabase Authentication

Comprehensive auth system with social providers, email/password, magic links, and enterprise SSO.

## Auth Methods

| Method | Use Case | Setup Complexity |
|--------|----------|------------------|
| Email/Password | Standard apps | Low |
| Magic Link | Passwordless | Low |
| Social OAuth | Consumer apps | Medium |
| Phone/SMS | Mobile-first | Medium |
| SSO/SAML | Enterprise | High |
| Anonymous | Guest access | Low |

## Email/Password

### Basic Setup

```typescript
// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password',
  options: {
    data: {
      full_name: 'John Doe',
      // Goes to user_metadata (user-editable)
    }
  }
});

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password'
});

// Sign out
await supabase.auth.signOut();
```

### Email Confirmation

```typescript
// Configure in Dashboard: Auth > Email Templates
// Or in config.toml for local development

// Resend confirmation
await supabase.auth.resend({
  type: 'signup',
  email: 'user@example.com'
});
```

### Password Reset

```typescript
// Request reset
await supabase.auth.resetPasswordForEmail('user@example.com', {
  redirectTo: 'https://yourapp.com/reset-password'
});

// Update password (after redirect)
await supabase.auth.updateUser({
  password: 'new-secure-password'
});
```

## Social OAuth

### Supported Providers

Google, GitHub, GitLab, Facebook, Twitter, Discord, Spotify, Slack, Azure, Apple, Bitbucket, LinkedIn, Notion, Twitch, Keycloak

### Setup

```typescript
// Initiate OAuth flow
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
  options: {
    redirectTo: 'https://yourapp.com/auth/callback',
    scopes: 'email profile',
    queryParams: {
      access_type: 'offline',
      prompt: 'consent'
    }
  }
});

// Handle callback
// In your /auth/callback route:
const { data: { session }, error } = await supabase.auth.exchangeCodeForSession(code);
```

### PKCE Flow (Recommended)

```typescript
// Server-side token exchange
const { data, error } = await supabase.auth.exchangeCodeForSession(code);

// Store session securely
// Never expose tokens in URLs
```

## Magic Links

```typescript
// Send magic link
const { data, error } = await supabase.auth.signInWithOtp({
  email: 'user@example.com',
  options: {
    emailRedirectTo: 'https://yourapp.com/welcome',
    shouldCreateUser: true // or false to only allow existing users
  }
});

// User clicks link, session is created automatically
```

## Phone/SMS Auth

```typescript
// Send OTP
const { data, error } = await supabase.auth.signInWithOtp({
  phone: '+1234567890'
});

// Verify OTP
const { data, error } = await supabase.auth.verifyOtp({
  phone: '+1234567890',
  token: '123456',
  type: 'sms'
});
```

## Anonymous Auth

```typescript
// Create anonymous session
const { data, error } = await supabase.auth.signInAnonymously();

// Later, link to permanent account
const { data, error } = await supabase.auth.updateUser({
  email: 'user@example.com',
  password: 'secure-password'
});
```

## Enterprise SSO (SAML 2.0)

### Prerequisites

- Pro plan or higher
- Identity Provider (Okta, Azure AD, OneLogin, etc.)

### Setup via CLI

```bash
# Create SSO provider
supabase sso add \
  --type saml \
  --metadata-url "https://idp.example.com/metadata" \
  --domains "company.com,subsidiary.com"

# List providers
supabase sso list

# Update provider
supabase sso update <provider-id> --domains "newdomain.com"

# Remove provider
supabase sso remove <provider-id>
```

### Sign In with SSO

```typescript
// SP-initiated flow
const { data, error } = await supabase.auth.signInWithSSO({
  domain: 'company.com',
  options: {
    redirectTo: 'https://yourapp.com/dashboard'
  }
});

// Redirect user to data.url
if (data?.url) {
  window.location.href = data.url;
}
```

### Multi-Tenant SSO

```typescript
// Each tenant has unique SSO provider
const { data, error } = await supabase.auth.signInWithSSO({
  providerId: tenant.sso_provider_id,
  options: {
    redirectTo: `https://${tenant.subdomain}.yourapp.com/dashboard`
  }
});

// Provider ID is included in JWT for RLS
// auth.jwt() -> 'amr' contains provider info
```

### Attribute Mapping

```yaml
# Map IdP attributes to Supabase user
attribute_mapping:
  keys:
    email:
      name: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    first_name:
      name: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
    last_name:
      name: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
    role:
      name: "http://schemas.example.com/claims/role"
      default: "member"
```

## Session Management

### Access and Refresh Tokens

```typescript
// Get current session
const { data: { session } } = await supabase.auth.getSession();

// Access token (short-lived, use for API calls)
session.access_token;

// Refresh token (long-lived, use to get new access token)
session.refresh_token;

// Auto-refresh is handled by the client
// Configure refresh threshold:
const supabase = createClient(url, key, {
  auth: {
    autoRefreshToken: true,
    persistSession: true
  }
});
```

### Session Listeners

```typescript
// Listen for auth changes
supabase.auth.onAuthStateChange((event, session) => {
  switch (event) {
    case 'SIGNED_IN':
      console.log('User signed in:', session.user);
      break;
    case 'SIGNED_OUT':
      console.log('User signed out');
      break;
    case 'TOKEN_REFRESHED':
      console.log('Token refreshed');
      break;
    case 'USER_UPDATED':
      console.log('User updated:', session.user);
      break;
  }
});
```

### Session Security

```typescript
// Set session timeouts in Dashboard
// Auth > Settings > Session Timebox / Inactivity Timeout

// Force re-authentication for sensitive actions
const { data, error } = await supabase.auth.reauthenticate();
```

## Custom JWT Claims

### Server-Side (Edge Function)

```typescript
// Set app_metadata (not user-editable)
const { data, error } = await supabaseAdmin.auth.admin.updateUserById(userId, {
  app_metadata: {
    tenant_id: 'tenant-uuid',
    role: 'admin',
    permissions: ['read', 'write', 'delete']
  }
});
```

### Using in RLS

```sql
-- Access app_metadata in policies
CREATE POLICY "tenant_access" ON items
  USING (
    tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::UUID
  );

CREATE POLICY "admin_only" ON settings
  USING (
    auth.jwt() -> 'app_metadata' ->> 'role' = 'admin'
  );
```

## Security Best Practices

### Password Requirements

```typescript
// Configure in Dashboard: Auth > Settings
// Minimum length, require uppercase, numbers, symbols

// Or validate client-side before signup
const validatePassword = (password: string) => {
  const minLength = 8;
  const hasUppercase = /[A-Z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSymbol = /[!@#$%^&*]/.test(password);

  return password.length >= minLength && hasUppercase && hasNumber && hasSymbol;
};
```

### Rate Limiting

```typescript
// Built-in rate limiting for auth endpoints
// Configurable in Dashboard: Auth > Rate Limits

// Custom rate limiting in Edge Functions
import { RateLimiter } from 'some-rate-limiter';

const limiter = new RateLimiter({ points: 5, duration: 60 });

Deno.serve(async (req) => {
  const ip = req.headers.get('x-forwarded-for');

  try {
    await limiter.consume(ip);
  } catch {
    return new Response('Too many requests', { status: 429 });
  }

  // Process request...
});
```

### Secure Headers

```typescript
// Configure allowed redirect URLs
// Dashboard: Auth > URL Configuration

// Prevent open redirects
const allowedDomains = ['yourapp.com', 'app.yourapp.com'];

const isAllowedRedirect = (url: string) => {
  try {
    const { hostname } = new URL(url);
    return allowedDomains.some(d => hostname === d || hostname.endsWith(`.${d}`));
  } catch {
    return false;
  }
};
```

## Hooks (Server-Side)

```typescript
// Auth hooks run on Supabase servers
// Configure in Dashboard: Auth > Hooks

// Custom access token hook
// Modify JWT claims before token is issued
export async function customAccessTokenHook(event) {
  const { user_id, claims } = event;

  // Fetch additional user data
  const { data: profile } = await supabase
    .from('profiles')
    .select('role, tenant_id')
    .eq('id', user_id)
    .single();

  return {
    ...claims,
    app_metadata: {
      ...claims.app_metadata,
      role: profile?.role,
      tenant_id: profile?.tenant_id
    }
  };
}
```

## Migration from Other Auth Systems

### Firebase Auth

```typescript
// Export Firebase users
// Import to Supabase with preserved UIDs

const { data, error } = await supabaseAdmin.auth.admin.createUser({
  id: firebaseUser.uid, // Preserve UID
  email: firebaseUser.email,
  email_confirm: true,
  app_metadata: {
    provider: 'firebase-import'
  }
});
```

### Auth0 / Cognito

```typescript
// Use custom JWT hook to verify external tokens
// Or migrate users gradually with "link account" flow
```

## Multi-Factor Authentication (MFA)

### TOTP Setup (Authenticator Apps)

```typescript
// 1. Enroll user in MFA
const { data, error } = await supabase.auth.mfa.enroll({
  factorType: 'totp',
  friendlyName: 'Authenticator App'
});

// data contains:
// - id: factor UUID
// - totp.qr_code: Base64 QR code for authenticator apps
// - totp.secret: Manual entry key
// - totp.uri: otpauth:// URI

// Display QR code to user
<img src={data.totp.qr_code} alt="Scan with authenticator app" />

// 2. Verify enrollment with code from authenticator
const { data: challenge } = await supabase.auth.mfa.challenge({
  factorId: data.id
});

const { data: verify, error } = await supabase.auth.mfa.verify({
  factorId: data.id,
  challengeId: challenge.id,
  code: userEnteredCode // 6-digit code
});
```

### MFA Login Flow

```typescript
// After password login, check if MFA is required
const { data: factors } = await supabase.auth.mfa.listFactors();

if (factors.totp.length > 0) {
  // User has MFA enabled, require verification
  const factor = factors.totp[0];

  // Create challenge
  const { data: challenge } = await supabase.auth.mfa.challenge({
    factorId: factor.id
  });

  // Verify with user's code
  const { data, error } = await supabase.auth.mfa.verify({
    factorId: factor.id,
    challengeId: challenge.id,
    code: userCode
  });

  if (error) {
    console.error('MFA verification failed');
  }
}
```

### Assurance Levels (AAL)

```typescript
// Check current assurance level
const { data: { currentLevel } } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel();

// aal1: Password or OAuth only
// aal2: Password/OAuth + MFA verified

// Require AAL2 for sensitive operations
if (currentLevel !== 'aal2') {
  // Prompt for MFA verification
}
```

### MFA in RLS Policies

```sql
-- Require MFA for sensitive data access
CREATE POLICY "require_mfa" ON sensitive_data
  FOR ALL USING (
    auth.jwt() ->> 'aal' = 'aal2'
  );

-- Or check specific MFA method
CREATE POLICY "require_totp" ON financial_data
  FOR ALL USING (
    auth.jwt() -> 'amr' ? 'totp'
  );
```

### Unenroll MFA

```typescript
// Remove MFA factor
const { data, error } = await supabase.auth.mfa.unenroll({
  factorId: factorId
});
```

## Bot Protection (Captcha)

### Cloudflare Turnstile Setup

```typescript
// 1. Configure in Dashboard: Auth > Bot Protection
// 2. Add Turnstile widget to your signup/login form

// Client-side: Include Turnstile script
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer />

// Turnstile widget
<div
  className="cf-turnstile"
  data-sitekey="your-site-key"
  data-callback="onTurnstileVerify"
/>

// 3. Pass captcha token to Supabase auth
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password',
  options: {
    captchaToken: turnstileToken
  }
});

// Same for signIn
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password',
  options: {
    captchaToken: turnstileToken
  }
});
```

### hCaptcha Integration

```typescript
// 1. Enable hCaptcha in Dashboard: Auth > Bot Protection
// 2. Add hCaptcha widget

<script src="https://js.hcaptcha.com/1/api.js" async defer />

<div
  className="h-captcha"
  data-sitekey="your-hcaptcha-site-key"
  data-callback="onHCaptchaVerify"
/>

// 3. Pass token to auth
const { data, error } = await supabase.auth.signUp({
  email,
  password,
  options: {
    captchaToken: hcaptchaToken
  }
});
```

### React Integration Example

```tsx
import { Turnstile } from '@marsidev/react-turnstile';
import { useState } from 'react';

function SignupForm() {
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);

  const handleSignup = async (email: string, password: string) => {
    if (!captchaToken) {
      alert('Please complete the captcha');
      return;
    }

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { captchaToken }
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <Turnstile
        siteKey={process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY!}
        onSuccess={(token) => setCaptchaToken(token)}
      />
      <button type="submit">Sign Up</button>
    </form>
  );
}
```

## Server-Side Auth (SSR)

### @supabase/ssr Package

For server-rendered apps (Next.js, SvelteKit, Remix), use `@supabase/ssr` for secure cookie-based sessions.

```bash
npm install @supabase/ssr
```

### Next.js App Router Setup

```typescript
// lib/supabase/server.ts
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          } catch {
            // Called from Server Component
          }
        },
      },
    }
  );
}

// lib/supabase/client.ts
import { createBrowserClient } from '@supabase/ssr';

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
```

### Middleware for Session Refresh

```typescript
// middleware.ts
import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            request.cookies.set(name, value)
          );
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // Refresh session if expired
  const { data: { user } } = await supabase.auth.getUser();

  // Protect routes
  if (!user && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return supabaseResponse;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

### Server Component Usage

```typescript
// app/dashboard/page.tsx
import { createClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const supabase = await createClient();

  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect('/login');
  }

  const { data: posts } = await supabase
    .from('posts')
    .select('*')
    .eq('user_id', user.id);

  return <PostsList posts={posts} />;
}
```

### Route Handlers

```typescript
// app/api/profile/route.ts
import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

export async function GET() {
  const supabase = await createClient();

  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single();

  return NextResponse.json(profile);
}
```

### Auth Callback Handler

```typescript
// app/auth/callback/route.ts
import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get('code');
  const next = searchParams.get('next') ?? '/dashboard';

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/auth/error`);
}
```

### Cookie Security Best Practices

```typescript
// Cookies are HttpOnly by default (not accessible via JavaScript)
// Additional security options:
{
  cookies: {
    setAll(cookiesToSet) {
      cookiesToSet.forEach(({ name, value, options }) =>
        cookieStore.set(name, value, {
          ...options,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          httpOnly: true
        })
      );
    }
  }
}
```
