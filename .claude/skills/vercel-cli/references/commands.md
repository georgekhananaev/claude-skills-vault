# Vercel CLI — Command Reference & Doc URI Map

Complete command surface for the latest Vercel CLI, with risk tier and the
official doc URI for self-healing. Per-command page = `https://vercel.com/docs/cli/<command>`.
Overview: https://vercel.com/docs/cli · Global options: https://vercel.com/docs/cli/global-options.

Tiers: **S**=Safe · **W**=Write · **D**=Destructive · **F**=Forbidden
(see [safety-rules.md](safety-rules.md)). Self-heal recipe lives in SKILL.md.

## Core deploy & dev

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel` / `vercel deploy` | W | Deploy a preview (default command) | /docs/cli/deploy |
| `vercel deploy --prod` | D | Deploy to production | /docs/cli/deploy |
| `vercel build [--prod]` | W | Build locally / in CI | /docs/cli/build |
| `vercel dev [--port N]` | S | Run the dev environment locally | /docs/cli/dev |
| `vercel pull [--environment=production]` | W | Pull env vars + project settings | /docs/cli/pull |
| `vercel link [path]` | W | Link local dir to a project | /docs/cli/link |
| `vercel init [name]` | W | Scaffold an example project | /docs/cli/init |
| `vercel redeploy <url\|id>` | W | Rebuild & redeploy existing | /docs/cli/redeploy |

## Deployment lifecycle (production traffic)

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel ls` / `vercel list [project]` | S | List recent deployments | /docs/cli/list |
| `vercel inspect <url\|id> [--logs] [--wait]` | S | Deployment details | /docs/cli/inspect |
| `vercel logs <url> [--follow]` | S | Runtime logs | /docs/cli/logs |
| `vercel promote <id>` / `promote status` | D | Make a deployment current prod | /docs/cli/promote |
| `vercel rollback [id]` / `rollback status` | D | Roll back production | /docs/cli/rollback |
| `vercel remove <url\|project>` / `rm` | D | Delete deployment(s) | /docs/cli/remove |
| `vercel bisect` | S | Binary-search deployments for a bug | /docs/cli/bisect |
| `vercel rolling-release fetch` | S | Show rollout state | /docs/cli/rolling-release |
| `vercel rolling-release configure` | W | Configure rollout (`rr` alias) | /docs/cli/rolling-release |
| `vercel rolling-release start/approve/complete/abort` | D | Run/advance/abort a live rollout | /docs/cli/rolling-release |

## Environment variables

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel env ls` | S | List env var names | /docs/cli/env |
| `vercel env add <name> <env>` | W | Add an env var | /docs/cli/env |
| `vercel env update <name> <env>` | W | Update an env var | /docs/cli/env |
| `vercel env pull [file]` | W | Write env vars to a local file | /docs/cli/env |
| `vercel env run -- <cmd>` | W | Run a command with project env injected | /docs/cli/env |
| `vercel env rm <name> <env>` | D | Remove an env var | /docs/cli/env |

## Projects & teams

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel project ls` / `inspect [name]` | S | List / inspect projects | /docs/cli/project |
| `vercel project add` | W | Create a project | /docs/cli/project |
| `vercel project rm` | F | **Delete a project** (permanent) | /docs/cli/project |
| `vercel teams ls` | S | List teams | /docs/cli/teams |
| `vercel teams add` | W | Create a team | /docs/cli/teams |
| `vercel teams invite <email>` | D | Invite a member (grants team access) | /docs/cli/teams |
| `vercel switch [team]` | S | Switch active scope | /docs/cli/switch |
| `vercel whoami` | S | Current user | /docs/cli/whoami |
| `vercel login [email] [--github]` | W | Authenticate | /docs/cli/login |
| `vercel logout` | F | Sign out (loses session) | /docs/cli/logout |
| `vercel open` | S | Open project in dashboard | /docs/cli/open |

> No `vercel teams rm` — team/member removal is Dashboard-only.

## Domains, DNS, certs, aliases

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel domains ls` / `inspect <d>` | S | List / inspect domains | /docs/cli/domains |
| `vercel domains check/price <d>` | S | Availability / price (no buy) | /docs/cli/domains |
| `vercel domains add <d> [project]` | W | Add a domain (`--force` to move from another project) | /docs/cli/domains |
| `vercel domains rm <d>` | D | Remove a domain | /docs/cli/domains |
| `vercel domains buy <d>` | F | **Purchase** a domain | /docs/cli/domains |
| `vercel domains transfer-in <d>` | F | **Paid** inbound registrar transfer | /docs/cli/domains |
| `vercel domains move <d> <scope>` | F | Move a domain to another scope | /docs/cli/domains |
| `vercel dns ls [domain]` | S | List DNS records | /docs/cli/dns |
| `vercel dns add <domain> <name> <type> <value>` | W | Add a DNS record | /docs/cli/dns |
| `vercel dns rm <record-id>` | D | Remove a DNS record | /docs/cli/dns |
| `vercel certs ls` | S | List certificates | /docs/cli/certs |
| `vercel certs issue <domain>` | W | Issue a certificate | /docs/cli/certs |
| `vercel certs rm <id>` | D | Remove a certificate | /docs/cli/certs |
| `vercel alias ls` | S | List aliases | /docs/cli/alias |
| `vercel alias set <url> <domain>` | W | Point alias at a deployment | /docs/cli/alias |
| `vercel alias rm <domain>` | D | Remove an alias | /docs/cli/alias |

## Git integration

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel git ls` | S | List Git connections | /docs/cli/git |
| `vercel git connect` | W | Connect a Git repo | /docs/cli/git |
| `vercel git disconnect <provider>` | F | Disconnect (breaks auto-deploy) | /docs/cli/git |

## Routing, redirects, flags, targets

Routes & redirects mutations are **staged** until published — see staging model in
[safety-rules.md](safety-rules.md).

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel routes list`/`list-versions`/`inspect`/`export` | S | View routing rules | /docs/cli/routes |
| `vercel routes add`/`edit`/`delete`/`enable`/`disable`/`reorder`/`discard-staging` | W | Stage routing changes | /docs/cli/routes |
| `vercel routes publish` / `restore <version-id>` | D | Push staged routes live to prod | /docs/cli/routes |
| `vercel redirects list`/`list-versions` | S | View redirects | /docs/cli/redirects |
| `vercel redirects add`/`upload` | W | Stage redirects | /docs/cli/redirects |
| `vercel redirects remove <source>` | W | Remove a staged redirect | /docs/cli/redirects |
| `vercel redirects promote`/`restore <version-id>` | D | Push staged redirects live to prod | /docs/cli/redirects |
| `vercel flags list` | S | List feature flags | /docs/cli/flags |
| `vercel flags create/set/open` | W | Manage feature flags | /docs/cli/flags |
| `vercel target ls` | S | List custom environments | /docs/cli/target |
| `vercel target rm` | D | Delete a custom environment | /docs/cli/target |
| `vercel microfrontends pull` | S | Pull microfrontends config | /docs/cli/microfrontends |

## Security: firewall & cache

Firewall `rules`/`ip-blocks` mutations are **staged** (revert via `firewall discard`)
until `firewall publish`. `system-bypass`/`attack-mode`/`system-mitigations` apply **immediately**.

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel firewall overview`/`diff`/`rules list`/`ip-blocks list`/`system-bypass list` | S | View firewall state | /docs/cli/firewall |
| `vercel firewall rules add/edit/remove/enable/disable/reorder` | W | Stage custom-rule changes | /docs/cli/firewall |
| `vercel firewall ip-blocks block/unblock <ip>` | W | Stage IP block changes | /docs/cli/firewall |
| `vercel firewall discard` | W | Discard staged changes | /docs/cli/firewall |
| `vercel firewall publish` | D | Publish staged rule/IP changes | /docs/cli/firewall |
| `vercel firewall system-bypass add/remove <ip>` | D | Immediately exempt IPs from mitigations | /docs/cli/firewall |
| `vercel firewall attack-mode enable/disable` | D | Immediate live challenge mode | /docs/cli/firewall |
| `vercel firewall system-mitigations resume` | W | Re-enable DDoS protection | /docs/cli/firewall |
| `vercel firewall system-mitigations pause` | F | **Removes DDoS protection** (24h, no publish); you owe usage fees | /docs/cli/firewall |
| `vercel cache purge [--type cdn\|data]` | D | Purge cache | /docs/cli/cache |
| `vercel cache invalidate --tag <t>` | D | Invalidate by tag | /docs/cli/cache |
| `vercel cache dangerously-delete --tag <t>` | F | Hard-delete cached data | /docs/cli/cache |

## Storage, integrations, webhooks

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel blob list` / `get <url>` | S | List / download blobs | /docs/cli/blob |
| `vercel blob put <file>` / `copy` | W | Upload / copy a blob | /docs/cli/blob |
| `vercel blob del <url>` | D | Delete a blob | /docs/cli/blob |
| `vercel integration list/discover/guide/balance` | S | Explore integrations | /docs/cli/integration |
| `vercel integration add <name>` / `vercel install <name>` | W | Provision an integration | /docs/cli/integration |
| `vercel integration remove <name>` | D | Remove an integration | /docs/cli/integration |
| `vercel integration-resource remove/disconnect` | D | Remove a provisioned resource | /docs/cli/integration-resource |
| `vercel integration-resource create-threshold` | W | Set auto-recharge threshold | /docs/cli/integration-resource |
| `vercel webhooks list/get <id>` | S | View webhooks (beta) | /docs/cli/webhooks |
| `vercel webhooks create <url> --event <e>` | W | Create a webhook (beta) | /docs/cli/webhooks |
| `vercel webhooks rm <id>` | D | Remove a webhook (beta) | /docs/cli/webhooks |

## Observability & account

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel activity [ls]` | S | Activity events | /docs/cli/activity |
| `vercel alerts [--all] [--project]` | S | Recent alerts | /docs/cli/alerts |
| `vercel metrics <name>` / `metrics schema` | S | Observability metrics | /docs/cli/metrics |
| `vercel traces get <request-id>` | S | Request traces | /docs/cli/traces |
| `vercel usage [--from --to]` | S | Billing usage & costs | /docs/cli/usage |
| `vercel contract` | S | Contract commitment info | /docs/cli/contract |
| `vercel buy <product> ...` | F | **Purchase** credits/addons/plans/domains | /docs/cli/buy |

## Networking helpers (beta)

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel api <endpoint>` | S/W/D | Authenticated API call — tier by HTTP method | /docs/cli/api |
| `vercel curl <path>` | S | HTTP request to your deployment | /docs/cli/curl |
| `vercel httpstat <path>` | S | HTTP timing stats | /docs/cli/httpstat |

`vercel api` tier follows the method: GET=Safe, POST/PUT/PATCH=Write,
DELETE=Destructive. Backed by https://vercel.com/docs/rest-api.

## Config & misc

| Command | Tier | Purpose | Doc URI |
|---------|------|---------|---------|
| `vercel mcp [--project]` | W | Set up MCP client config | /docs/cli/mcp |
| `vercel telemetry status/enable/disable` | S/W | Telemetry toggle | /docs/cli/telemetry |
| `vercel guidance enable/disable/status` | S/W | Post-command guidance toggle | /docs/cli/guidance |
| `vercel help [command]` | S | Built-in help | /docs/cli/help |
| `vercel --version` | S | CLI version | /docs/cli |

## Config files

- `vercel.json` (project config): https://vercel.com/docs/project-configuration
- `.vercel/project.json` (created by `vercel link`): identifies the linked project
- Env file written by `vercel env pull` (default `.env.local`)
