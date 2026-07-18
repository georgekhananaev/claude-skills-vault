---
name: firebase-cli
description: Safety-first Firebase CLI (firebase-tools v15) skill for full project control — deploy, Hosting (sites/channels/rollback), Cloud Functions (+secrets), Firestore (databases/indexes/backups/delete), Realtime Database, Auth import/export, Remote Config, App Distribution, App Hosting, Extensions, Data Connect, Emulator Suite & MCP server. Classifies every command by risk tier via a deterministic classifier script and gates destructive/irreversible/cost-incurring ops behind AskUserQuestion confirmation; enforces the --non-interactive/--force contract so nothing hangs and nothing is auto-confirmed. Wrong-project preflight prevents deploying to prod by accident. Ships a 3-level self-test (static classifier battery, live read-only, guarded live-write w/ cleanup). Use when running, planning, or debugging any `firebase` command.
author: George Khananaev
---

# Firebase CLI

Safety-first wrapper for `firebase` (firebase-tools). Every command is classified by risk tier BEFORE execution — full Firebase control, w/ anything irreversible, live-traffic-affecting, or cost-incurring gated behind explicit `AskUserQuestion`. Blast radius: a project's entire data (Firestore/RTDB wipes have NO undo), live sites, prod app config served to every user, & real money (Blaze).

## When to Use

- Deploy hosting/functions/rules/indexes; preview channels; rollbacks
- Inspect or mutate Firestore, Realtime DB, Auth users, Remote Config, secrets
- Manage projects, apps, sites, backends, extensions, testers
- Local dev: Emulator Suite, `serve`, functions shell
- NOT for single-doc conversational data edits — Firebase MCP server fits better; see [references/mcp.md](references/mcp.md) (CLI vs MCP)

## Prerequisites (run once per session)

```bash
bash scripts/firebase_preflight.sh [target-project-id]
```

Reports CLI/Node version, **account**, **active project**, & verifies the target project exists. NEVER run a write op w/o knowing which account+project you're pointed at. Not logged in → user runs `firebase login` themselves (browser). CI → `GOOGLE_APPLICATION_CREDENTIALS` service account; `--token`/`FIREBASE_TOKEN` are deprecated — refuse.

## Safety Model

| Tier | Action Required | Examples |
|------|----------------|----------|
| **Safe** | Execute immediately | `*:list`, `*:get`, `database:get`, `functions:log`, `remoteconfig:get`, `deploy --dry-run`, all `emulators:*` |
| **Write** | Inform user, then execute | `deploy --only hosting`, `hosting:channel:deploy`, `database:push/update`, `apps:create`, `functions:secrets:set` |
| **Destructive** | `AskUserQuestion` BEFORE executing | `firestore:delete`, `database:set/remove`, `functions:delete`, `hosting:disable`, `auth:import` (UID overwrite!), `remoteconfig:rollback`, `deploy --force`, `projects:create` (cost/permanent) |
| **Forbidden** | Triple typed confirmation, NEVER auto-confirm | `firestore:delete --all-collections`, `firestore:databases:delete`, `firestore:backups:delete`, `hosting:sites:delete`, `functions:secrets:destroy`, `database:set /`, `database:remove /`, unfiltered `functions:delete`, bulk destructive loops |

Full classification + protocols: [references/safety-rules.md](references/safety-rules.md). Complete command inventory w/ tiers & flags: [references/commands.md](references/commands.md).

**Firebase MCP server connected?** (`mcp__firebase__*` tools): those calls BYPASS the classifier & can mutate what the CLI can't (Firestore docs, RTDB writes, Auth users, live Remote Config). Tier every MCP call from the map in [references/mcp.md](references/mcp.md) & apply the same confirmation protocols — e.g. `firestore_delete_database` = Forbidden, `realtimedatabase_set_data`/`auth_update_user`/`remoteconfig_update_template` = Destructive.

## Decision Flow

```text
Command received
  → bash scripts/firebase_preflight.sh          (once per session — account/project)
  → python3 scripts/firebase_risk.py "<cmd>"    (deterministic tier + reason)
  → Safe?        Execute immediately
  → Write?       State target project + what changes → execute
  → Destructive? AskUserQuestion (project, resource, blast radius, backup offer) → execute or cancel
  → Forbidden?   Warn → typed confirmation → final confirm → execute or cancel
On failure → Self-Healing (firebase <cmd> --help → docs)
```

The classifier is advisory — apply judgment on top: prod-looking targets, security-rules deploys, first Blaze deploys, or ambiguous resources deserve a question even at "write" tier.

## Risk Classifier

```bash
python3 scripts/firebase_risk.py "firebase firestore:delete --all-collections -P prod"
# FORBIDDEN: wipes EVERY collection in the Firestore database [firestore:delete project=prod]
# exit codes: 0=safe 10=write 20=destructive 30=forbidden
```

Exact-command table over the full v15 surface (unknown cmds fail closed to `write`) + escalations: `--force`, `--all-collections`, RTDB root paths (`/`), unfiltered `functions:delete`, `hosting:clone → :live`, distribute-to-testers, compound commands (`&&`, `;`, `|`, `$()` — highest tier wins), `xargs`/loop bulk ops (→ forbidden), `-P` extraction for confirmation prompts, sensitive-output & interactive-command flags.

## The --non-interactive / --force Contract

firebase prompts on destructive ops; in agent context prompts = hangs, & `--force` silently skips them. Rules:

1. ALWAYS add `--non-interactive` (or `--json`) — prompts become errors, never hangs
2. NEVER add `--force` to a Destructive/Forbidden op w/o completed confirmation flow
3. After user confirms → rerun w/ `--force --non-interactive`
4. An "Error: … --force" response is the guard WORKING — confirm w/ user, don't just retry w/ force
5. `--force` surprises: `deploy --force` DELETES functions missing locally; `functions:secrets:set -f` auto-redeploys dependents

## Wrong-Project Guard

#1 Firebase accident. Before EVERY write+:

1. Preflight once; **display name ≠ project ID** — resolve via `firebase projects:list`
2. Explicit `-P <project-id>` on every mutating command — never trust `.firebaserc` ambient state
3. Aliases named `prod`/`production`/`live` → escalate caution one tier
4. Multiple accounts (`login:list`) → pass `--account <email>`

## AskUserQuestion Integration

Show project, resource & blast radius; include "Cancel" + a safer alternative:

```text
Q: "Delete Firestore path /users recursively on fir-cli-test-73b0a? NO undo."
  - "Delete it" — firebase firestore:delete /users -r -P fir-cli-test-73b0a --force --non-interactive
  - "Export first (gcloud firestore export), then delete"
  - "Cancel"

Q: "Import 500 users into prod-app? Matching UIDs are silently REPLACED (no CLI prompt exists)."
  - "Backup first: auth:export, then import" (Recommended)
  - "Import now" / "Cancel"
```

Also ask (not just deletes): rules deploys to prod, Remote Config changes (live for all users), anything Blaze-billable, choosing among multiple sites/instances/databases, extension installs.

## Sensitive Output

`functions:secrets:access` / `apphosting:secrets:access` (secret VALUES), `auth:export` (PII), `functions:config:get` (keys) → redirect to files, never echo into chat/logs unless explicitly requested. `apps:sdkconfig` is public client config — fine to show. Never put secrets on argv — `--data-file -` w/ stdin.

## Emulator-First & Dry-Run

Prefer previews before touching cloud state: `deploy --dry-run` validates+builds; `hosting:channel:deploy` gives a prod-identical preview URL (auto-expires); `emulators:exec "npm test" --only firestore,auth` runs against local emulators w/ auto-shutdown — the default answer for "test my rules/functions/data code". Long-running (`emulators:start`, `serve`) → background. Recipes: [references/patterns.md](references/patterns.md).

## Self-Test

```bash
bash scripts/self_test.sh                                            # static — no network, ~60 classifier assertions
bash scripts/self_test.sh --live --project <id>                      # + read-only live probes
bash scripts/self_test.sh --live-write --project <id> --confirm <id> # + write/cleanup round-trip (DISPOSABLE project only)
```

Run static after any skill edit; run `--live` after CLI upgrades. `--live-write` double-confirms the project id, touches only namespaced resources, pre-classifies its own mutations through the risk gate, & cleans up (trap-guarded).

## Self-Healing

CLI surface evolves: on any error → `firebase <cmd> --help` (authoritative for installed version) → [references/patterns.md](references/patterns.md) error table → WebFetch `https://firebase.google.com/docs/cli` / `https://github.com/firebase/firebase-tools`. Commands that DON'T exist (don't invent): project/app/user/bucket deletion, RTDB instance deletion, Firestore data export (→ `gcloud firestore export`).

## Error Handling (quick)

| Error | Fix |
|-------|-----|
| `Command requires authentication` | User: `firebase login --reauth`; CI: service account |
| `Failed to get Firebase project` | Display name ≠ ID → `projects:list`; check `--account` |
| `HTTP 403 / PERMISSION_DENIED` | IAM role missing or API disabled in GCP console |
| `Blaze plan required` | User upgrades billing — never assume consent to spend |
| Non-interactive error demanding `--force` | Guard working → run confirmation flow first |
| Hang | Interactive cmd (`init`, `login`, `use --add`, shells) → non-interactive alt or user runs it |

Full table: [references/patterns.md](references/patterns.md).

## Shell Safety

- Quote JSON args in single quotes; prefer `--data-file`/stdin for payloads & secrets
- `--json` for machine-readable output (`{"status":"success","result":…}` → `jq .result`)
- Bulk ops: print resource list FIRST, confirm once w/ exact count, then loop
- Timeouts on every live call (self_test wraps w/ 180s alarm) — no unbounded waits

## Integration

Pairs w/: **gemini-cli / agy-cli** (Google-stack second opinions), **aws-cli / supabase-cli / mongodb-atlas-cli** (other data planes), **github-cli** (CI/CD wiring, `init hosting:github`), **owasp-security** (rules & auth audits), **file-converter** (transform exported JSON/CSV), **nextjs-senior-dev** (App Hosting deploys).
