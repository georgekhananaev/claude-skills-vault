# Firebase CLI Safety Rules

Full risk classification & confirmation protocol. The deterministic source of truth is `scripts/firebase_risk.py` (complete v15 command table; exit 0=safe 10=write 20=destructive 30=forbidden). This file explains the WHY & the human protocol.

## Tier Definitions

| Tier | Meaning | Protocol |
|------|---------|----------|
| **Safe** | Read-only, or local-only (emulators, init scaffolding, downloads) | Execute immediately |
| **Write** | Mutates cloud state, recoverable / additive | State target project + what changes → execute |
| **Destructive** | Irreversible data/config loss, live-traffic impact, cost commitment, outward-facing (notifies people) | `AskUserQuestion` BEFORE executing — include project, resource, blast radius, "Cancel" option |
| **Forbidden** | Whole-datastore wipes, backup deletion, unrecoverable secrets | Triple confirmation (below), NEVER auto-confirm |

## The `--force` / `--non-interactive` Contract (core Firebase-specific rule)

firebase-tools' own prompts are the last line of defense; the flags interact:

- `--non-interactive` (or `--json`, which implies it) → destructive commands **ERROR instead of prompting** unless `--force` is present
- `-f`/`--force` → skips ALL of the CLI's own confirmations

Therefore, in agent context:

1. ALWAYS pass `--non-interactive` (prevents hangs — a prompt you can't see never returns)
2. NEVER pass `--force` on a Destructive/Forbidden-tier command until the user has confirmed via `AskUserQuestion`
3. AFTER explicit confirmation, run w/ `--force --non-interactive` (the confirmed intent replaces the prompt)
4. `--force` has per-command surprise semantics — check before proposing:
   - `deploy --force` → **deletes** Cloud Functions missing from local source
   - `functions:secrets:set --force` → auto-**redeploys** every function using the secret
   - `deploy --only firestore:indexes` + force → deletes indexes missing from local file

## Forbidden Ops (never auto-confirm)

| Command | Why |
|---------|-----|
| `firestore:delete --all-collections` | Wipes EVERY collection — entire Firestore database gone |
| `firestore:databases:delete <db>` | Deletes a whole Firestore database |
| `firestore:backups:delete <backup>` | Deletes the BACKUP — removes the safety net itself |
| `hosting:sites:delete <site>` | Site, all versions, all URLs — permanent |
| `functions:secrets:destroy <KEY>[@v]` / bulk `prune` | Secret material unrecoverable; running functions referencing it break |
| `database:set /` · `database:remove /` | Replaces/wipes the ENTIRE Realtime Database |
| `functions:delete` (no filter) | Could target every deployed function |
| Bulk loops (`xargs`/`for`/`while`) over any destructive op | Multiplied blast radius |

### Triple-Confirmation Protocol (Forbidden tier)

1. **Warn** — state exactly what is destroyed, that there is NO undo, & what breaks downstream
2. **Typed confirmation** — user must type the resource identifier (project id, db name, site id) back; `AskUserQuestion` w/ "Type the exact name to proceed" via Other/free-text
3. **Final confirm** — restate `project + command`, offer backup-first alternative (below), then execute or cancel

Never chain the three into one question. Never pre-fill the typed value.

## Backup-Before-Destroy Map

Offer the backup FIRST — it's usually one command:

| Before | Run first |
|--------|-----------|
| `firestore:delete` / `bulkdelete` / `databases:delete` | `gcloud firestore export gs://<bucket>` (CLI has no Firestore export!) or verify `firestore:backups:list` has a recent backup |
| `database:remove` / `database:set` | `firebase database:get / -o backup-$(date +%F).json --instance <i>` |
| `auth:import` | `firebase auth:export pre-import-$(date +%F).json` |
| `functions:delete` / `deploy --force` | confirm source is committed in git (`functions:list` for inventory) |
| `functions:config:unset` | `firebase functions:config:get > config-backup.json` |
| `remoteconfig:rollback` | `firebase remoteconfig:get -o rc-current.json` |
| `hosting:sites:delete` / `hosting:disable` | note current release in console; `hosting:clone <site>:live <backup-site>:live` |
| `ext:uninstall` | `firebase ext:export` (manifest → firebase.json) |

## Commands With NO Prompt Of Their Own (classifier is the ONLY gate)

- `auth:import` — matching UIDs **silently replace** existing accounts (password hashes included); duplicate emails create additional accounts. No prompt, no dry-run. ALWAYS `auth:export` first + confirm.
- `hosting:clone ... <site>:live` — instant prod release on the target site.
- `remoteconfig:rollouts:delete`, `appdistribution:testers:remove` — immediate.

## Irreversibility Traps (look reversible, aren't)

| Action | Trap |
|--------|------|
| `projects:create` | Project IDs are consumed FOREVER (even after console deletion). No CLI delete exists. |
| `database:instances:create` | Instance names reserved forever; instances can only be DISABLED, never deleted |
| `apps:create` | Apps cannot be deleted via CLI (console only) |
| `firestore:databases:create --location` | Location is immutable after creation |
| `ext:dev:upload` | Published extension versions are public & permanent (only deprecatable) |
| `apps:android:sha:delete` | Released builds using that SHA lose Google Sign-In until re-added |

## NOT Possible Via CLI (don't invent commands)

Project deletion · app deletion · RTDB instance deletion (disable only, console) · Auth user deletion (Admin SDK/console; no `auth:delete`) · Storage bucket deletion · Firestore data export (use `gcloud firestore export`) · undo of `projects:addfirebase`.

## Wrong-Project Guard

The #1 Firebase accident: right command, wrong project.

1. `scripts/firebase_preflight.sh [target-id]` once per session — shows account, active project, & verifies target exists
2. **Display name ≠ project ID** (e.g. "firebase-cli-test" → `fir-cli-test-73b0a`). Resolve via `projects:list` before every first use of a project
3. Explicit `-P <project-id>` on EVERY mutating command — never rely on `.firebaserc` ambient state
4. `.firebaserc` aliases named `prod`/`production`/`live` → treat any write to them as one tier higher in caution (a "write" earns an `AskUserQuestion`)
5. `--account <email>` when multiple accounts are logged in (`login:list`)

## Sensitive Output (redaction rules)

| Command | Contains | Rule |
|---------|----------|------|
| `functions:secrets:access` / `apphosting:secrets:access` | secret VALUE | Redirect to file/env var; NEVER echo into chat/logs unless user explicitly asks for the value |
| `auth:export` | PII: emails, phones, password hashes | Write to file only; never paste contents; don't commit |
| `functions:config:get` | often API keys | Don't echo; redirect to file |
| `login:ci` / `--token` | long-lived credential | Deprecated — refuse & recommend service account (`GOOGLE_APPLICATION_CREDENTIALS`) |
| `apps:sdkconfig` | client config | Public by design — fine to show |

## Escalate Beyond The Classifier (model judgment)

The classifier is advisory & escalation-only. ALWAYS `AskUserQuestion` even on "write" tier when:

- Target project alias/ID suggests production & the change affects live users (rules deploy, RC template, hosting live channel)
- Deploying **security rules** (`deploy` incl. `firestore`/`database`/`storage` targets) — a bad rules file silently opens or bricks the datastore
- First deploy on a Blaze-plan project (creates billable infra: Cloud Build, Artifact Registry, Cloud Run)
- Ambiguous resource match (several sites/instances/databases & user named none)
- `ext:install`/`ext:update` major version (extensions run code w/ service-account powers)
