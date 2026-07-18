# Firebase MCP Server — Setup & Risk Tiers

The Firebase CLI ships an MCP server (`firebase mcp`; also installed via the official `firebase/agent-skills` plugin → tools appear as `mcp__firebase__*`). It can mutate data the CLI can't touch (Firestore docs, RTDB writes, Auth users, live Remote Config) — and **its tool calls NEVER pass through `scripts/firebase_risk.py`**, which only parses `firebase …` shell commands.

## The Rule

> Every MCP tool call gets a tier from the table below BEFORE invoking it, and the SAME protocols apply as for CLI commands: Write → inform first · Destructive → `AskUserQuestion` w/ project + resource + blast radius · Forbidden → triple typed confirmation. Wrong-project guard applies doubly — see "Project targeting".

## Setup Facts

- **Auth**: reuses the CLI's login session (`firebase login:list` shows who). No separate login. Headless/CI → `GOOGLE_APPLICATION_CREDENTIALS`. `firebase_login`/`firebase_logout` tools exist as fallback.
- **No read-only mode**: the server acts w/ the signed-in account's FULL permissions across ALL its projects. Client tool-approval prompts are the only native brake.
- **Project targeting**: active project comes from the workspace's `.firebaserc` (or `--dir`). No `.firebaserc` → tools error or ask. Pin a disposable default in test workspaces; `firebase_update_environment` can SWITCH the active project mid-session — treat as a wrong-project event & re-verify before the next mutation.
- **Tool detection**: default tool set depends on firebase.json features + enabled APIs; `--only core,firestore,…` forces groups (groups: core, auth, firestore, database, storage, messaging, remoteconfig, functions, apphosting, crashlytics, dataconnect).
- **Headless probe** (list live tools w/o an MCP client):

```bash
printf '%s\n%s\n%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1.0.0"}}}' \
 '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
 | perl -e 'alarm 40; exec @ARGV' firebase mcp --only core 2>/dev/null
```

## Tool Risk Tiers (v15 server, 57 tools)

### ✅ Safe — read-only / local; execute freely

`firebase_get_project` · `firebase_get_environment` · `firebase_get_sdk_config` (public config) · `firebase_get_security_rules` · `firebase_validate_security_rules` (local validation) · `firebase_list_apps` · `firebase_list_projects` · `firebase_read_resources` · `firestore_get_database` · `firestore_list_databases` · `firestore_get_document` · `firestore_list_documents` · `firestore_list_collections` · `firestore_query_collection` · `firestore_get_index` · `firestore_list_indexes` · `realtimedatabase_get_data` · `auth_get_users` (PII — file/summary only, don't echo dumps) · `functions_list_functions` · `functions_get_logs` · `remoteconfig_get_template` · `apphosting_list_backends` · `apphosting_fetch_logs` · `crashlytics_get_issue` · `crashlytics_get_report` · `crashlytics_list_events` · `crashlytics_batch_get_events` · `crashlytics_list_notes` · `dataconnect_list_services` · `dataconnect_build` (local compile) · `storage_get_object_download_url` (mints an access URL — treat the URL itself as sensitive)

### ✏️ Write — inform user, then execute

`firebase_create_app` · `firebase_create_android_sha` · `firebase_init` (local files) · `firebase_login` (interactive browser) · `firebase_update_environment` (switches active project/user — re-run wrong-project checks after!) · `firestore_add_document` (additive) · `firestore_update_document` (merges given fields of a LIVE doc — verify doc path first) · `firestore_create_index` · `auth_set_sms_region_policy` (can BLOCK sign-ins from whole regions — confirm scope) · `messaging_send_message` to a throwaway topic (no subscribers) · `crashlytics_create_note` · `crashlytics_update_issue` (triage state) · `firebase_deploy` (same rules-overwrite cautions as CLI `deploy`; scope it) · `firebase_deploy_status`

### ⚠️ Destructive — AskUserQuestion BEFORE the call

| Tool | Why |
|------|-----|
| `firestore_delete_document` | Permanent doc deletion — NO undo, no trash |
| `firestore_delete_index` | Live queries relying on it start failing |
| `firestore_create_database` / `firestore_update_database` | Billable DB / live settings (delete-protection, PITR) |
| `realtimedatabase_set_data` | REPLACE semantics — everything at the path is overwritten (root path → treat as ⛔) |
| `auth_update_user` | Mutates a REAL account (disable, email, claims) — lockout risk |
| `remoteconfig_update_template` | PUBLISHES config live to every app instance (CLI can only rollback; this can rewrite) |
| `messaging_send_message` w/ real `registration_token` or subscribed topic | Notifies real devices |
| `dataconnect_execute` | Arbitrary query/mutation against prod CloudSQL |
| `firebase_create_project` | Project ID consumed forever |
| `firebase_logout` | Kills the shared CLI session (breaks CLI + MCP both) |
| `crashlytics_delete_note` | Deletes team data |

### ⛔ Forbidden — triple typed confirmation, never auto-confirm

`firestore_delete_database` — deletes an ENTIRE Firestore database & all its data. Same protocol as CLI `firestore:databases:delete`.

## CLI vs MCP (division of labor)

| Prefer CLI (classifier-gated) | Prefer MCP |
|------------------------------|------------|
| Deploys, channels, rollbacks, CI | Single Firestore doc reads/writes/queries |
| Bulk ops, backups (`auth:export`, `database:get -o`), exports | Auth user lookup/update one-offs |
| Emulators, project/app admin, secrets | FCM sends (`messaging_send_message`) |
| Anything wanting the deterministic risk gate | Crashlytics triage, RC template edits |

Before any MCP Destructive op, the CLI is still the backup tool: `auth:export` before touching users, `database:get -o` before RTDB writes, `remoteconfig:get -o` before template updates.
