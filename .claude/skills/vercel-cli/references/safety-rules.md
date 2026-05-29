# Vercel CLI — Safety Rules

Full risk classification and confirmation protocols. Load when handling
Destructive/Forbidden operations.

## Four Tiers

### Tier 1 — Safe (read-only, execute immediately)

`ls`/`list`, `inspect`, `project ls`/`inspect`, `env ls`, `domains ls`,
`dns ls`, `certs ls`, `alias ls`, `logs`, `whoami`, `teams ls`, `git ls`,
`activity`, `alerts`, `usage`, `contract`, `metrics`, `traces`, `flags list`,
`redirects list`/`list-versions`, `routes list`/`list-versions`/`inspect`/`export`,
`firewall overview`/`diff`/`rules list`/`ip-blocks list`/`system-bypass list`,
`target ls`, `webhooks list`/`get`, `integration list`/`discover`/`balance`,
`blob list`/`get`, `domains check`/`price`, `rolling-release fetch`,
`telemetry status`, `guidance status`, `help`, `api <GET>`.

### Tier 2 — Write (inform, then execute)

Reversible, not production-traffic-affecting. State what will happen, then run:

`deploy` (preview, no `--prod`), `build`, `pull`, `link`, `env add`/`update`/`pull`,
`alias set`, `domains add`, `dns add`, `certs issue`, `redeploy`, `flags create`/`set`,
`redirects add`/`upload`, `routes add`/`edit`/`delete`/`enable`/`disable`/`reorder`/`discard-staging`
(all staged — not live until `publish`), `firewall rules add`/`edit`/`remove`/`enable`/`disable`/`reorder`
and `firewall ip-blocks block`/`unblock` (staged — revert via `firewall discard` before `publish`),
`firewall system-mitigations resume`, `git connect`, `blob put`/`copy`, `init`,
`integration add`/`install`, `mcp`, `webhooks create`, `rolling-release configure`,
`api -X POST/PUT/PATCH`.

### Tier 3 — Destructive (AskUserQuestion required BEFORE running)

Always call `AskUserQuestion` first with a "Cancel" option. Removes resources
or alters live production traffic (reversible only with effort):

| Command | Why gated |
|---------|-----------|
| `deploy --prod` | Publishes to production traffic |
| `promote <id>` | Switches live production to another deployment |
| `rollback [id]` | Reverts production to a prior deployment |
| `rolling-release start`/`approve`/`complete`/`abort` | Gradual prod rollout (reversible via `abort`) |
| `remove` / `rm` | Deletes deployment(s) |
| `env rm` | Removes an env var (may break builds) |
| `alias rm` | Detaches a custom domain from a deployment |
| `domains rm` | Removes a domain from the scope/project |
| `dns rm` | Deletes a DNS record (can break mail/site) |
| `certs rm` | Removes a TLS certificate |
| `cache purge` / `invalidate` | Drops cached responses |
| `routes publish` / `restore` | Pushes staged routes live to production |
| `redirects promote` / `restore` | Pushes staged redirects live to production |
| `firewall publish` | Publishes staged rule/IP-block changes |
| `firewall attack-mode enable`/`disable` | Immediate live challenge posture change |
| `firewall system-bypass add`/`remove` | Immediate — exempts IPs from system mitigations |
| `flags rm` | Removes a feature flag |
| `integration remove`, `integration-resource remove`/`disconnect` | Tears down provisioned resources |
| `blob del` | Deletes stored files |
| `webhooks rm` | Removes a webhook |
| `target rm` | Deletes a custom environment |
| `teams invite` | Grants team-wide access (reversible; invite expires ~7d) |
| `api -X DELETE` | Deletes via API |

> Team/member **removal** is Dashboard-only — there is no `vercel teams rm`.

### Tier 4 — Forbidden (multi-step typed confirmation, NEVER auto-confirm)

Permanent, costly, or protection-removing. Require the triple-confirmation
protocol below; never pass `--yes`. "Force it"/"yolo" does not skip steps.

| Command | Why |
|---------|-----|
| `project rm` | Deletes the project AND all its deployments — permanent |
| `domains buy` | Spends money; registers a domain |
| `domains transfer-in` | Spends money; inbound registrar transfer |
| `buy` (`credits`/`addon`/`pro`/`domain`) | Spends money / changes billing |
| `domains move` | Transfers a domain to another scope |
| `cache dangerously-delete` | Hard-deletes cached data (no soft purge) |
| `firewall system-mitigations pause` | Removes DDoS protection immediately (no publish gate); you owe usage fees for abusive traffic |
| `git disconnect` | Breaks auto-deploy on push |
| `logout` | Destroys the local session |
| Any bulk destructive loop | Multiplies blast radius |

## Staging Model (routes / redirects / firewall)

- `routes` and `redirects` **add/edit/delete/upload** are **staged** → Write.
  They go live only via `publish` (routes), `promote` (redirects), or `restore` → Destructive.
- `firewall rules` and `ip-blocks` mutations are **staged** → Write; revert with
  `firewall discard`. They go live via `firewall publish` → Destructive.
- `firewall system-bypass`, `attack-mode`, and `system-mitigations` apply
  **immediately** (no publish). `system-mitigations pause` → Forbidden; the
  others → Destructive; `system-mitigations resume` → Write (safe direction).

## Confirmation Templates

### Destructive — AskUserQuestion

```text
Question: "Remove deployment <url>? This deletes it permanently."
Options:
  - "Remove it"  → vercel remove <url> --yes
  - "Cancel"

Question: "Deploy to PRODUCTION? This changes live traffic."
Options:
  - "Deploy to production"   → vercel deploy --prod
  - "Preview deploy instead" → vercel deploy
  - "Cancel"
```

### Forbidden — Triple-Confirmation Protocol

1. **Warn:** state exactly what is permanent/costly and the blast radius
   (e.g. "Deleting project `acme-web` removes ALL its deployments, domain
   bindings, and env vars — irreversible").
2. **Typed confirmation:** require the user to type the resource name or
   `DELETE`/`BUY`/`PAUSE`. A thumbs-up is not enough.
3. **Final confirm:** restate the command verbatim, ask once more, then run.
   Never use `--yes` to skip.

If any step is unanswered or ambiguous → **do not run**. Offer the Vercel
Dashboard instead.

## Hard Rules

- Never auto-deploy/promote to production without per-action confirmation.
- Never run a Forbidden command inside a script/loop.
- Never echo a token; prefer `VERCEL_TOKEN` over `--token`.
- Always confirm the active **scope/team** before delete or production ops —
  the same command in the wrong team hits the wrong project.
- When an audit suggests deleting something, **surface it, don't act.**

## Refusal Pattern

When asked to bypass confirmation on a Forbidden op:

```text
REFUSED: `vercel <command>` is a permanent/costly/protection-removing op.
  I won't skip confirmation. Either (1) walk the confirmation steps, or
  (2) run it directly in the Vercel Dashboard.
```
