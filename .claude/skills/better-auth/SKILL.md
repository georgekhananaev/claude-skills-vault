---
name: better-auth
description: Better Auth integration guide for TypeScript/JavaScript authentication. Covers server/client configuration, database adapters, session management, plugins, OAuth, and scaffolding auth from scratch. Use when setting up authentication with Better Auth, configuring auth.ts, adding OAuth providers, or creating sign-in/sign-up flows.
metadata:
  author: Better Auth
  source: https://github.com/better-auth/skills
  version: "1.0"
---

# Better Auth Skills

Complete authentication setup and integration guide using Better Auth for TypeScript/JavaScript applications.

## Available Sub-Skills

| Skill | File | Use When |
|-------|------|----------|
| Best Practices | [best-practices-SKILL.md](best-practices-SKILL.md) | Configuring Better Auth, database adapters, sessions, plugins, security |
| Create Auth | [create-auth-SKILL.md](create-auth-SKILL.md) | Scaffolding auth from scratch, adding login/signup to a project |

## Quick Reference

### Setup
1. `npm install better-auth`
2. Set `BETTER_AUTH_SECRET` and `BETTER_AUTH_URL` env vars
3. Create `auth.ts` with database + config
4. Create route handler for your framework
5. Run `npx @better-auth/cli@latest migrate`

### Supported Frameworks
Next.js (App/Pages Router), SvelteKit, Nuxt, Astro, Express, Hono, SolidStart

### Supported Databases
PostgreSQL, MySQL, SQLite, MongoDB (via Prisma, Drizzle, or direct drivers)

### Key Plugins
twoFactor, organization, passkey, magicLink, emailOtp, username, admin, apiKey, bearer, jwt, sso

## Source

From [better-auth/skills](https://github.com/better-auth/skills).
