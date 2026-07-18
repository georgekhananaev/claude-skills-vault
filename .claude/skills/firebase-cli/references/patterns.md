# Firebase CLI Patterns & Recipes

## Session Setup

```bash
bash scripts/firebase_preflight.sh              # who am I, which project
bash scripts/firebase_preflight.sh my-proj-id   # + verify target exists
firebase projects:list --json                   # display name → project ID
```

Not logged in → the user must run `firebase login` themselves (browser OAuth). CI → service account:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/sa-key.json   # roles: least-privilege (e.g. Firebase Hosting Admin)
firebase deploy --only hosting -P <id> --non-interactive
```

`FIREBASE_TOKEN`/`login:ci`/`--token` are deprecated — refuse & migrate to service accounts.

## Project Aliases (.firebaserc)

```bash
firebase use --add                 # interactive — user runs it
firebase use staging               # switch active alias
firebase deploy -P staging …       # better: explicit per command
```

`{"projects": {"default": "…", "staging": "…", "prod": "…"}}`. Ambient state is how wrong-project accidents happen → mutations always get explicit `-P`.

## Deploy Workflows

```bash
firebase deploy --dry-run --only hosting,functions -P <id>       # 1. validate + build only
firebase hosting:channel:deploy pr-42 --expires 7d -P <id>       # 2. preview URL (safe, auto-expires)
firebase deploy --only hosting -m "release: v1.2" -P <id> --non-interactive   # 3. live
```

- Scope EVERY deploy w/ `--only` — bare `deploy` pushes ALL configured targets incl. security rules
- Function subsets: `--only functions:fnA,functions:fnB` (or `codebase:fn`)
- **Rollbacks**: hosting → console release history or `hosting:clone <site>:<old-channel> <site>:live`; functions → redeploy previous git commit; Remote Config → `remoteconfig:rollback -v <N>`. No generic undo.
- CI previews: `firebase init hosting:github` scaffolds the GitHub Action (PR channels + live on merge)

## Emulator-First Testing (never iterate against prod)

```bash
firebase emulators:exec "npm test" --only firestore,auth,functions   # start → test → shutdown
firebase emulators:exec "node seed.js" --only firestore --import ./seed --export-on-exit
firebase emulators:start --only firestore,ui   # long-running → run_in_background
```

Point SDKs at emulators via env: `FIRESTORE_EMULATOR_HOST=127.0.0.1:8080`, `FIREBASE_AUTH_EMULATOR_HOST`, `FIREBASE_DATABASE_EMULATOR_HOST`, `FIREBASE_STORAGE_EMULATOR_HOST`. Inside `emulators:exec` they're set automatically. Emulator ports/config: `firebase.json → "emulators"`.

## Data Operations

```bash
# RTDB — backup, then mutate
firebase database:get / -o backup-$(date +%F).json -P <id>        # full backup first
firebase database:get /users --limit-to-first 10 --pretty -P <id>
firebase database:push /logs -d '{"evt":"x"}' -P <id>             # additive
firebase database:update /cfg -d '{"flag":true}' -P <id>          # merge listed keys
echo '<json>' | firebase database:set /cfg -P <id> --force --non-interactive   # REPLACE subtree (post-confirmation)

# Auth — export before any import
firebase auth:export users-$(date +%F).json -P <id>
firebase auth:import new-users.json --hash-algo SCRYPT --hash-key <key> -P <id>   # confirmed first!

# Firestore data: CLI only DELETES. Reads/writes → Firebase MCP server or Admin SDK.
gcloud firestore export gs://<bucket>/$(date +%F) --project <id>   # the real Firestore backup
```

## JSON Output & Parsing

`--json` → `{"status":"success","result":…}` (and implies non-interactive):

```bash
firebase apps:list --json -P <id> | jq -r '.result[].appId'
firebase functions:list --json -P <id> | jq -r '.result[] | "\(.id) \(.runtime) \(.status)"'
firebase hosting:sites:list --json -P <id> | jq -r '.result.sites[].name'
firebase projects:list --json | jq -r '.result[].projectId'
```

## Secrets

```bash
printf '%s' "$VALUE" | firebase functions:secrets:set MY_KEY --data-file - -P <id>   # never on argv
firebase functions:secrets:access MY_KEY -P <id> > /tmp/secret.txt                    # value → file, not chat
firebase functions:secrets:get MY_KEY -P <id>                                         # metadata is fine to show
```

New secret versions apply on next deploy (`--force` on set auto-redeploys — surprise, avoid).

## Error → Fix Table

| Error | Cause | Fix |
|-------|-------|-----|
| `Command requires authentication` / `Authentication Error` | No/expired session | User runs `firebase login --reauth`; CI → `GOOGLE_APPLICATION_CREDENTIALS` |
| `Failed to get Firebase project <x>` / `Invalid project id` | Wrong ID (display name?) or no access | `firebase projects:list`; check `--account` |
| `HTTP Error: 403, Permission denied` / `PERMISSION_DENIED` | Missing IAM role or API disabled | Grant role in console; enable API: `https://console.cloud.google.com/apis/library?project=<id>` |
| `HTTP Error: 404` on resource op | Feature never provisioned (no RTDB instance, no default site) | Provision in console/`init`, or wrong `--instance`/`--site` |
| `Your project must be on the Blaze plan` | Functions/extensions/etc. need billing | User upgrades in console — never assume consent to spend |
| `HTTP Error: 429` / quota | Rate limits | Backoff & retry; check quotas page |
| Prompt appeared in non-interactive run (exit 1) | Destructive cmd w/o `--force` | Correct behavior! Confirm w/ user, then rerun w/ `--force --non-interactive` |
| Hangs forever | Interactive cmd in agent context (`init`, `login`, `use --add`, shells) | Kill; use non-interactive alternative or ask user to run it |
| `functions:config` errors | Runtime Config API shut down Dec 2025 | `functions:config:export` → dotenv; use env vars/secrets |
| Deploy stuck on functions | Cloud Build in progress | Check `functions:log` + console Cloud Build tab; retry idempotent |
| `firebase: command not found` | Not installed | `npm i -g firebase-tools` or `curl -sL https://firebase.tools \| bash` |

## Self-Healing

Surface evolves; on any unknown command/flag error:

1. `firebase <cmd> --help` (authoritative for installed version); namespace overview: `firebase <ns> --help`
2. `firebase --version` vs latest: `npm view firebase-tools version`; upgrade w/ user consent
3. WebFetch docs: `https://firebase.google.com/docs/cli` · GitHub: `https://github.com/firebase/firebase-tools` (README + issues)
4. Changelog: `https://github.com/firebase/firebase-tools/releases`

## CLI vs Firebase MCP Server

The CLI ships an MCP server (`firebase mcp`, tools for Firestore doc CRUD, auth user lookup, storage, messaging). Division:

| Use CLI (this skill) | Use MCP |
|----------------------|---------|
| Deploys, rules, channels, CI | Single Firestore doc reads/writes |
| Bulk ops, backups, exports, scripting | "Query my data" conversational tasks |
| Emulators, project/app admin | Auth user lookup/update one-offs |
| Anything needing the risk gate & audit trail | |

MCP has NO read-only mode (full user permissions) — for mutations, the CLI + classifier path is the safer route.

## Self-Test (this skill testing itself)

```bash
S=.claude/skills/firebase-cli/scripts
bash $S/self_test.sh                                          # static: syntax + 60-case classifier battery
bash $S/self_test.sh --live --project <id>                    # + read-only live probes
bash $S/self_test.sh --live-write --project <id> --confirm <id>   # + write/cleanup round-trip
```

`--live-write` is for DISPOSABLE projects only: it double-checks the project id (`--confirm` must repeat it), touches only namespaced resources (`skill-selftest` hosting channel, `/__skill_selftest__` RTDB path), pre-classifies each mutation through the risk gate, cleans up after itself (incl. on abort via trap), & refuses to create anything permanent (skips RTDB round if no instance exists). Run after CLI upgrades to catch surface changes.
