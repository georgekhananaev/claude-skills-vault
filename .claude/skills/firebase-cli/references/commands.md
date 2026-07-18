# firebase-tools v15 Command Inventory

Complete surface, enumerated from a live v15.24.0 install (`--help` tree walk). Tiers: ✅ safe · ✏️ write · ⚠️ destructive · ⛔ forbidden — as enforced by `scripts/firebase_risk.py`. Flag details evolve: trust `firebase <cmd> --help` over this file when they disagree.

## Global Flags (any command)

| Flag | Effect |
|------|--------|
| `-P, --project <alias\|id>` | Target project — ALWAYS pass explicitly on mutations |
| `--account <email>` | Pick among logged-in accounts (`login:list`) |
| `-j, --json` | Machine output; **implies `--non-interactive`**. Shape: `{"status":"success","result":…}` |
| `--non-interactive` | Prompts become errors (destructive cmds then need `--force`) |
| `-i, --interactive` | Force prompts even w/o TTY |
| `-c, --config <path>` | Alternate firebase.json |
| `--debug` | Verbose + `firebase-debug.log` |
| `--token <t>` | DEPRECATED — refuse; use service account |

**Auth precedence:** `--token` → `FIREBASE_TOKEN` → `firebase login` session → `GOOGLE_APPLICATION_CREDENTIALS` → gcloud ADC.
**Env vars:** `FIREBASE_TOKEN` (deprecated), `GOOGLE_APPLICATION_CREDENTIALS`, `FIREBASE_CLI_EXPERIMENTS`, `HTTPS_PROXY`; emulator redirection: `FIRESTORE_EMULATOR_HOST`, `FIREBASE_AUTH_EMULATOR_HOST`, `FIREBASE_DATABASE_EMULATOR_HOST`, `FIREBASE_STORAGE_EMULATOR_HOST`, `PUBSUB_EMULATOR_HOST`, `FIREBASE_DATA_CONNECT_EMULATOR_HOST`; `FIREBASE_EMULATOR_HUB` (set inside `emulators:exec`).

## Session & Meta

| Command | Tier | Notes |
|---------|------|-------|
| `login` / `login:add` / `login:use` | ✏️ | Browser OAuth — user must do it themselves |
| `login:list` | ✅ | |
| `login:ci` | ✏️ | Deprecated token mint — refuse, see safety-rules |
| `logout [email]` | ⚠️ | Breaks the authenticated session |
| `use` | ✅ | Shows active project |
| `use <alias\|id>` / `--add` / `--alias` / `--unalias` / `--clear` | ✏️ | Local `.firebaserc`; `--add` is interactive |
| `target [type]` | ✅ | `target:apply/clear/remove` ✏️ (local mapping) |
| `init [feature]` | ✏️ | Interactive wizard; features: hosting, firestore, functions, database, storage(rules), emulators, dataconnect, remoteconfig, apphosting, genkit, extensions, hosting:github |
| `open [link]` | ✅ | Browser to console |
| `experiments:list/describe` ✅ · `enable/disable` ✏️ | | Local CLI feature flags |
| `mcp [--only --tools --mode stdio\|sse]` | ✅ | Firebase MCP server (long-running) |
| `studio:export` | ✅ | Local Studio→Antigravity migration |

## Projects & Apps

| Command | Tier | Notes |
|---------|------|-------|
| `projects:list` | ✅ | Resolve display name → project ID here |
| `projects:create [id]` | ⚠️ | ID consumed FOREVER; no CLI delete |
| `projects:addfirebase <id>` | ✏️ | Effectively irreversible |
| `apps:list [platform]` / `apps:sdkconfig` | ✅ | sdkconfig = public client config |
| `apps:create [IOS\|ANDROID\|WEB] [name]` | ✏️ | No CLI delete exists |
| `apps:init` | ✏️ | Writes local app config (experimental) |
| `apps:android:sha:list` ✅ · `sha:create` ✏️ · `sha:delete` ⚠️ | | SHA delete breaks Sign-In for released builds |

## Deploy & Hosting

| Command | Tier | Notes |
|---------|------|-------|
| `deploy` | ✏️ | `--only <t1,t2>` (`hosting`, `functions[:fn]`, `firestore[:rules\|:indexes]`, `database`, `storage`, `remoteconfig`, `extensions`, `dataconnect`), `--except`, `-m <msg>` |
| `deploy --dry-run` | ✅ | Validates + builds only (may still enable APIs) |
| `deploy -f/--force` | ⚠️ | DELETES functions missing from source + auto-accepts all prompts |
| `hosting:channel:create/deploy [ch]` | ✏️ | `-e <dur>` ≤30d (deploy default 7d) — THE safe preview path |
| `hosting:channel:list/open` | ✅ | |
| `hosting:channel:delete <ch>` | ⚠️ | |
| `hosting:clone <src-site:ch> <dst-site:ch>` | ✏️/⚠️ | → `:live` target = instant prod release (⚠️) |
| `hosting:sites:create` ✏️ · `sites:list/get` ✅ · `sites:delete` ⛔ | | |
| `hosting:disable [-s site]` | ⚠️ | Live traffic goes dark |
| `serve` | ✅ | Local; long-running |

## Cloud Functions

| Command | Tier | Notes |
|---------|------|-------|
| `functions:list` / `functions:log [--only]` | ✅ | |
| `functions:shell` | ✏️ | Local REPL but Admin SDK hits PROD |
| `functions:delete [filters] [--region r]` | ⚠️ | No region = matches ALL regions; **no filter = ⛔** |
| `functions:config:get` | ✅ | LEGACY (API shut down Dec 2025; experiment-gated) |
| `functions:config:set/unset/clone` | ✏️/⚠️/⚠️ | Legacy — migrate via `functions:config:export` (✏️, → dotenv) |
| `functions:secrets:get/describe` | ✅ | Metadata only |
| `functions:secrets:access <KEY>[@v]` | ✅ | SECRET VALUE — redaction rules apply |
| `functions:secrets:set <KEY> [--data-file -]` | ✏️ | New version; `-f` auto-redeploys dependents |
| `functions:secrets:destroy` ⛔ · `prune` ⚠️ | | Unrecoverable |
| `functions:lifecycle:list` ✅ · `run` ✏️ | | |
| `functions:artifacts:setpolicy [--days]` | ✏️ | Cost-SAVING image cleanup — recommend proactively |

## Firestore

| Command | Tier | Notes |
|---------|------|-------|
| `firestore:indexes` / `locations` | ✅ | `--database <id>` |
| `firestore:delete [path]` | ⚠️ | `-r` recursive · `--shallow` · `--all-collections` ⛔ · `-f` |
| `firestore:bulkdelete --collection-ids a,b` | ⚠️ | Server-side bulk delete of collection groups |
| `firestore:operations:list/describe` ✅ · `cancel` ⚠️ | | Cancel may leave partial state |
| `firestore:databases:list/get` | ✅ | |
| `firestore:databases:create <db> --location <loc>` | ⚠️ | Named DBs have NO free tier; location immutable; `--delete-protection`, `--point-in-time-recovery`, `--edition standard\|enterprise` |
| `firestore:databases:update <db>` | ⚠️ | Toggle delete-protection/PITR |
| `firestore:databases:delete <db>` | ⛔ | |
| `firestore:databases:restore -d <db> -b <backup>` / `clone <src> <dst>` | ⚠️ | New billable DB |
| `firestore:backups:list/get` ✅ · `delete` ⛔ | | |
| `firestore:backups:schedules:list` ✅ · `create/update` ✏️ · `delete` ⚠️ | | |

No CLI data export — `gcloud firestore export gs://<bucket>`. No CLI doc reads — use MCP/Admin SDK, or `firestore:delete` is the ONLY data command.

## Realtime Database

| Command | Tier | Notes |
|---------|------|-------|
| `database:get <path>` | ✅ | `-o file --shallow --order-by --limit-to-first/last --start-at --end-at --equal-to --instance <i>` |
| `database:profile` | ✅ | Usage report |
| `database:push <path>` | ✏️ | Additive, never overwrites |
| `database:update <path>` | ✏️ | Merges ONLY given keys |
| `database:import <path> <file>` | ✏️ | Chunked bulk write; conflicting keys overwritten; `--disable-triggers` defaults TRUE; root → ⚠️ |
| `database:set <path>` | ⚠️ | REPLACES whole subtree (root → ⛔); `-d '<json>'` or file/stdin |
| `database:remove <path>` | ⚠️ | Root → ⛔ |
| `database:instances:list` | ✅ | |
| `database:instances:create <name> [-l loc]` | ⚠️ | Name reserved FOREVER; multi-instance = Blaze |
| `database:settings:get` ✅ · `set` ✏️ | | |

## Auth

| Command | Tier | Notes |
|---------|------|-------|
| `auth:export [file] [--format csv\|json]` | ✅ | PII — file only, never echo |
| `auth:import <file> [--hash-algo …]` | ⚠️ | NO prompt; UID match silently REPLACES the account. Hash flags: `--hash-algo --hash-key --salt-separator --rounds --mem-cost` |

No user deletion via CLI (Admin SDK/console).

## Remote Config

`remoteconfig:get [-v N] [-o file]` ✅ · `versions:list` ✅ · `rollback [-v N]` ⚠️ (live config flips for every app) · `rollouts:get/list` ✅ · `rollouts:delete` ⚠️ · `experiments:get/list` ✅ · `experiments:delete` ⚠️. Template publish = `deploy --only remoteconfig`.

## Emulators (local-only, all ✅)

| Command | Notes |
|---------|-------|
| `emulators:start [--only …]` | Long-running; emulators: apphosting, auth, functions, firestore, database, hosting, pubsub, storage, eventarc, dataconnect, tasks (+ ui) |
| `emulators:exec "<script>" [--only --import <dir> --export-on-exit]` | THE safe-test primitive: start → run script → shutdown |
| `emulators:export <path>` | Snapshot emulator data (local disk) |
| `setup:emulators:<database\|firestore\|pubsub\|storage\|ui\|dataconnect>` | Download emulator binaries |

## App Distribution & Testing

`appdistribution:distribute <binary> [--app <id>]` ✏️ — becomes ⚠️ w/ `--testers/--groups[-file]` (notifies real people). `testers:list` ✅ · `testers:add` ✏️ · `testers:remove` ⚠️ · `groups:list` ✅ · `groups:create` ✏️ · `groups:delete` ⚠️ · `testcases:export` ✅ · `testcases:import` ✏️ · `apptesting:execute <binary>` ✏️ (billable device time).

## App Hosting

`apphosting:backends:list/get` ✅ · `backends:create` ⚠️ (billable Cloud Run+Build) · `backends:delete` ⚠️ (live serving stops) · `rollouts:create` ⚠️ (deploys to LIVE traffic) · `secrets:set` ✏️ · `secrets:describe` ✅ · `secrets:access` ✅ (secret value!) · `secrets:grantaccess/revokeaccess` ⚠️ (IAM).

## Crashlytics

`crashlytics:symbols:upload <files>` ✏️ · `mappingfile:upload <file>` ✏️ · `mappingfile:generateid` ✅ (local).

## Data Connect

`dataconnect:services:list` ✅ · `compile` ✅ · `sdk:generate` ✅ · `sql:diff` ✅ · `sql:setup` ⚠️ (CloudSQL ≈$9+/mo) · `sql:migrate` ⚠️ (schema drops lose data) · `sql:grant` ⚠️ · `sql:shell` ⚠️ (interactive prod SQL) · `execute [file]` ⚠️ (runs mutations on prod; emulator only when `FIREBASE_DATA_CONNECT_EMULATOR_HOST` set).

## Extensions

`ext` / `ext:list` / `ext:info` ✅ · `ext:export` ✅ (→ firebase.json) · `ext:install <ref>` ✏️ (Blaze; deploys billable infra on next deploy) · `ext:update` / `ext:configure` ✏️ · `ext:uninstall` ⚠️ (may delete extension data) · `ext:sdk:install` ✅ · publisher: `ext:dev:init` ✅ · `register` ✏️ · `upload` ⚠️ (public registry) · `deprecate` ⚠️ · `undeprecate` ✏️ · `list/usage` ✅.

## Hidden / Experiment-Gated

Enable w/ `firebase experiments:enable <name>`: `legacyRuntimeConfigCommands` (functions:config:*), `appsinit`, `deletegcfartifacts` (`functions:deletegcfartifacts`), `webframeworks`, `apphosting`, `apptesting`, `genkit`, `mcpalpha`. List: `firebase experiments:list`.

## Cost Triggers (flag in confirmations)

Blaze required / bills money: `deploy --only functions` (Cloud Build min + Artifact Registry + invocations) · `ext:install/update` · `apphosting:backends:create`, `rollouts:create` · `firestore:databases:create/restore/clone` (named DBs: no free tier; PITR extra) · `firestore:backups:schedules:create` (backup storage) · `database:instances:create` (multi-instance) · `dataconnect:sql:setup` (CloudSQL) · `apptesting:execute` (device time). Cost-SAVER: `functions:artifacts:setpolicy`.
