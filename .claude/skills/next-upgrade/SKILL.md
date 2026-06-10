---
name: next-upgrade
description: Upgrade Next.js to the latest version following official migration guides and codemods
argument-hint: "[target-version]"
---

# Upgrade Next.js

Upgrade the current project to the latest Next.js version following official migration guides.

## Instructions

1. **Detect current version**: Read `package.json` to identify the current Next.js version and related dependencies (React, React DOM, etc.)

2. **Fetch the latest upgrade guide**: Use WebFetch to get the official upgrade documentation:
   - Codemods: https://nextjs.org/docs/app/guides/upgrading/codemods
   - Version-specific guides (adjust version as needed):
     - https://nextjs.org/docs/app/guides/upgrading/version-16
     - https://nextjs.org/docs/app/guides/upgrading/version-15

3. **Determine upgrade path**: Based on current version, identify which migration steps apply. For major version jumps, upgrade incrementally (e.g., 13 → 14 → 15 → 16).

4. **Prefer the automated path first**: the official upgrade codemod bumps deps AND runs the right transforms interactively:
   ```bash
   npx @next/codemod@latest upgrade latest   # or: upgrade patch|minor|major|<version>
   next upgrade                              # built-in self-upgrade command (Next 16.1+)
   ```
   Fall back to individual codemods when the automated path can't run:
   ```bash
   npx @next/codemod@latest <transform> <path>
   ```
   Common transforms:
   - `next-async-request-api` - Updates async Request APIs (v15)
   - `next-request-geo-ip` - Migrates geo/ip properties (v15)
   - `next-dynamic-access-named-export` - Transforms dynamic imports (v15)
   - `remove-experimental-ppr` / `remove-unstable-prefix` - PPR & unstable_* cleanup (v16)
   - `middleware-to-proxy` - middleware.ts → proxy.ts (v16)
   - `next-lint-to-eslint-cli` - migrate off `next lint` (v16)

5. **Update dependencies**: Upgrade Next.js and peer dependencies together:
   ```bash
   npm install next@latest react@latest react-dom@latest
   ```

6. **Review breaking changes**: Check the upgrade guide for manual changes needed:
   - API changes (e.g., async params in v15)
   - Configuration changes in `next.config.js`
   - Deprecated features being removed

7. **Update TypeScript types** (if applicable):
   ```bash
   npm install @types/react@latest @types/react-dom@latest
   ```

8. **Test the upgrade**:
   - ASK the user before running `npm run build` (builds are slow; some users forbid unprompted builds)
   - Run `npm run dev` and test key functionality
