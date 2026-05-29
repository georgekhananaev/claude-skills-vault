---
name: vercel-cli
description: Safety-first Vercel CLI (`vercel`/`vc`) skill to fully manage projects from the terminal — deploys, env vars, domains, DNS, certs, projects, teams, logs, rollbacks, promotions, firewall, and `vercel api`. Classifies each command by risk tier and gates destructive/forbidden ops behind confirmation. Self-heals via embedded doc URIs.
author: George Khananaev
---

# Vercel CLI

Safety-first wrapper for the Vercel CLI (`vercel`, alias `vc`). Every command is classified by risk tier before execution — full project control, with anything irreversible gated behind explicit confirmation.

## When to Use

- Deploy projects (preview/production), build locally, or run `vercel dev`
- Manage env vars, secrets, and pull project settings (`env`, `pull`)
- Manage domains, DNS records, certificates, and aliases
- Manage projects, teams/scopes, and Git connections
- Inspect deployments, read logs, roll back, promote, or redeploy
- Configure firewall, routes, redirects, cache, flags, rolling releases
- Make authenticated `vercel api` calls or manage blob storage & integrations

## Prerequisites

1. **Install:** `npm i -g vercel` (or pnpm/yarn). Native binary (experimental): `pnpm i -g @vercel/vc-native -f`
2. **Auth:** `vercel login` — or for CI/CD set `VERCEL_TOKEN` (preferred over the `--token` flag, which leaks into process lists). Tokens: https://vercel.com/account/tokens
3. **Verify:** `vercel --version` and `vercel whoami`
4. **Link:** `vercel link` in the project dir (creates `.vercel/`)
5. **Scope:** confirm the active team with `vercel teams ls`; switch with `vercel switch`

## Safety Model

| Tier | Action Required | Examples |
|------|----------------|----------|
| **Safe** | Execute immediately | `vercel ls`, `inspect`, `env ls`, `whoami` |
| **Write** | Inform user, then execute | `deploy` (preview), `env add`, `alias set`, `dns add`, staged `routes`/`firewall rules` edits |
| **Destructive** | `AskUserQuestion` BEFORE executing | `deploy --prod`, `remove`, `rollback`, `promote`, `env rm`, `alias rm`, `domains rm`, `certs rm`, `cache purge`, `firewall publish` |
| **Forbidden** | Multi-step typed confirmation, NEVER auto-confirm | `project rm`, `domains buy`/`transfer-in`, `buy`, `cache dangerously-delete`, `firewall system-mitigations pause`, `git disconnect`, bulk destructive loops |

Full classification + confirmation templates: [references/safety-rules.md](references/safety-rules.md).

## Decision Flow

```text
Command received
  → Classify risk tier (see Safety Model + references/commands.md)
  → Safe?        Execute immediately
  → Write?       State what will happen → execute
  → Destructive? AskUserQuestion with options → wait → execute or cancel
  → Forbidden?   Warn → typed confirmation → final confirm → execute or cancel
On failure → Self-Healing (fetch the command's doc URI)
```

## Forbidden Commands (never auto-confirm)

These need typed multi-step confirmation — keep them visible. The full
Destructive list and per-command tiers live in [references/safety-rules.md](references/safety-rules.md)
and [references/commands.md](references/commands.md).

| Command | Why |
|---------|-----|
| `vercel project rm` | Deletes project AND all its deployments — permanent |
| `vercel domains buy` / `domains transfer-in` / `buy` | Spends money |
| `vercel domains move` | Transfers domain to another scope |
| `vercel cache dangerously-delete` | Hard-deletes cached data |
| `vercel firewall system-mitigations pause` | Removes DDoS protection; you owe fees for abusive traffic |
| `vercel git disconnect` | Breaks auto-deploy on push |
| `vercel logout` | Destroys the local session |
| Bulk destructive loops | Multiplies blast radius |

## AskUserQuestion Integration

For **Destructive** ops, present tailored options with a "Cancel". Examples:

```text
Q: "Roll back production for <project>?"
  - "Roll back to previous" — vercel rollback
  - "Roll back to specific deployment" — vercel rollback <id>
  - "Cancel"

Q: "Remove env var <NAME> from <environment>?"
  - "Remove it" — vercel env rm <NAME> <env>
  - "Cancel"
```

For **Forbidden** ops, follow the triple-confirmation protocol in
[references/safety-rules.md](references/safety-rules.md).

## Production Deploy Protocol

`--prod`, `promote`, `rollback`, and `*-release`/`publish` change live traffic. Before running:

1. Confirm linked project & active scope (`vercel project inspect`, `vercel teams ls`)
2. Confirm git state (right branch/commit)
3. `AskUserQuestion` to confirm production intent (template in safety-rules.md)
4. After deploy, verify with `vercel inspect <url>` and `vercel logs <url>`

## Self-Healing

The CLI changes often (subcommands get renamed). On any error or unexpected
behavior: read the error → `vercel help <command>` → if still unclear,
WebFetch `https://vercel.com/docs/cli/<command>` → adjust → re-run. If a
command was renamed/removed, surface that with the doc link rather than
guessing repeatedly. Key URIs:

- Overview & command list: https://vercel.com/docs/cli
- Per-command: `https://vercel.com/docs/cli/<command>`
- Global options: https://vercel.com/docs/cli/global-options
- `vercel.json` config: https://vercel.com/docs/project-configuration
- REST API (for `vercel api`): https://vercel.com/docs/rest-api

Full URI map: [references/commands.md](references/commands.md).

## Common Flags

| Flag | Description |
|------|-------------|
| `--token <t>` | Auth token (prefer `VERCEL_TOKEN` env var) |
| `--scope <team>` | Team/scope to operate in |
| `--cwd <dir>` | Run as if in a different directory |
| `--target <env>` | Target a custom environment |
| `--yes` / `-y` | Skip prompts (NEVER on Forbidden ops) |
| `--debug` | Verbose output for troubleshooting |
| `--json` | Machine-readable output where supported |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `command not found: vercel` | Not installed | `npm i -g vercel` |
| `Not authorized` / `No existing credentials` | Not logged in | `vercel login` or set `VERCEL_TOKEN` |
| `Your codebase isn't linked` | Dir not linked | `vercel link` |
| `The provided token is not valid` | Bad/expired token | Regenerate at /account/tokens |
| `Can't find the specified scope` | Wrong team | `vercel teams ls` → `vercel switch` |
| `unknown or unexpected option` | Flag renamed | Self-heal: fetch `/docs/cli/<command>` |

## Shell Safety

- Never pass `--yes`/`-y` to Destructive or Forbidden ops
- Prefer `VERCEL_TOKEN` env var over `--token` (argv is visible in process lists)
- Quote multi-word values, env values, and DNS records
- Append `| cat` if a command might invoke a pager
- Verify team/project before any production or delete op

## Integration

Pairs with: **github-cli** (repo/PRs that trigger deploys), **nextjs-senior-dev** / **next-upgrade** (the apps deployed), **supabase-cli** / **neon-postgres-agent-platforms** (data services), **code-quality** (review before a prod deploy).
