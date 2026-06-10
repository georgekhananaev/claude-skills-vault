---
name: n8n-cli
description: Safety-first n8n management skill — list/inspect workflows, executions, credentials, tags, projects, variables, source-control status; trigger runs (CLI/webhook); activate/deactivate; backup/restore; audit; diff. Two backends auto-detect: REST API (cloud + remote self-hosted, urllib stdlib) & `n8n` CLI (self-hosted only, full surface incl. encrypted/decrypted credential export). Read-only by default; mutations require `--confirm` + dry-run preview. Hard-blocks 14 destructive CLI prefixes (delete, reset, encryption-key, executionData, user-management role changes, mfa, ldap, db ops, license) and 22 DELETE/PUT/PATCH/POST API endpoints (workflows/credentials/executions/users/tags/variables/projects/source-control/license). CLI refusal guard uses flag-stripping + chain matching to block bypasses. URL paths validated against `/api/v1/` allowlist + traversal-resistant. Resource IDs regex-validated before URL interpolation. API key redacted from error output; HTTPS warning on http://. Decrypted credential export double-gated (--decrypted + --confirm-secrets). Output paths sanitized. n8n REST API uses `/activate`+`/deactivate` for both 1.x & 2.x — public API has no `run` endpoint, so trigger_workflow is CLI-only w/ webhook URL helper. Faster than n8n MCP for bulk reads, backups, exports, diffs, CI/cron; complements MCP which is better for workflow authoring.
---

# n8n CLI Skill

Comprehensive n8n instance management w/ strict safety guarantees. Optimized for the loop: **list → inspect → backup → trigger → diff → audit**, never destructive.

## When to Use

Invoke when the user wants to:

- List or inspect workflows, executions, credentials (metadata)
- Trigger workflow runs manually
- Publish / unpublish workflows
- Back up workflows + credentials (encrypted or decrypted for migration)
- Restore workflows from JSON
- Diff workflows between snapshots / environments
- Generate security audit report
- Pull execution stats / health checks
- Migrate between n8n instances

**Do NOT use for** authoring workflows from scratch — use the n8n MCP server (`mcp__n8n__*`) for that. See [`references/cli-vs-mcp.md`](references/cli-vs-mcp.md).

## Hard Safety Boundaries

| Tier | Op | Action |
|---|---|---|
| Read | list/get workflows, executions, credentials, audit | Allowed, no confirm |
| Read | health check, execution stats | Allowed |
| Read | encrypted credential export | Allowed |
| Additive write | `import_workflow.py` | Requires `--confirm` + dry-run |
| Additive write | `publish_workflow.py` (state change) | Requires `--confirm` |
| Additive write | `trigger_workflow.py` (causes side effects!) | Requires `--confirm` |
| Sensitive write | `export_credentials.py --decrypted` | Requires `--decrypted` AND `--confirm-secrets` |
| Destructive | `delete:*`, `*:reset`, `encryption-key:*`, `executionData:prune`, `user-management:reset/promote/revoke`, `mfa:disable`, `ldap:reset`, `db:*`, `license:clear` | **REFUSED** |
| Destructive | `DELETE /api/v1/(workflows|credentials|executions|users|projects|tags)/`, `POST /api/v1/users`, `PATCH /api/v1/users/`, `POST /api/v1/source-control/(pull|push)`, `POST/DELETE /api/v1/license` | **REFUSED** |

Defense in depth: also rejects any subcommand containing tokens `delete`, `drop`, `destroy`, `remove`, `purge`, `wipe`, `reset`, `force`, `kill`, `terminate`.

## Two Backends

The skill auto-detects which backend to use per call:

| Backend | When | Capabilities |
|---|---|---|
| **REST API** | `N8N_API_URL` + `N8N_API_KEY` env vars set | Full read surface, workflow CRUD via API. Works for cloud + remote self-hosted. |
| **CLI** (`n8n` binary) | n8n CLI on PATH | Self-hosted only. Adds: `n8n audit` (full markdown), `n8n export:credentials --decrypted`, separate-file export modes. |

Pass `--backend api` or `--backend cli` to force a specific one. Otherwise: API preferred (faster, cloud-friendly).

## Prerequisites

### REST API mode (recommended)

```bash
# Get API key from n8n UI: Settings → n8n API → Create
export N8N_API_URL="https://n8n.example.com"     # no trailing slash, no /api/v1
export N8N_API_KEY="eyJ..."                      # JWT format (older installs: n8n_api_...)

# Verify
python3 .claude/skills/n8n-cli/scripts/validate_env.py
```

### CLI mode (self-hosted only)

```bash
npm install -g n8n
# or:  alias n8n='npx n8n'
n8n --version

# Verify
python3 .claude/skills/n8n-cli/scripts/validate_env.py --backend cli
```

Both can coexist — many ops are CLI-only or API-only, the skill picks the right one.

## Script Index

### Read-only

| Script | Backend | Purpose |
|---|---|---|
| `validate_env.py` | both | Check CLI install + API auth + version |
| `health_check.py` | API + CLI | `/healthz` probe, API auth check, n8n CLI version, recent execution success rate |
| `list_workflows.py` | API or CLI | List workflows w/ filters (active, tag, project, name) |
| `get_workflow.py` | API | Single workflow detail (nodes, connections, settings) |
| `list_executions.py` | API | Recent executions w/ status filter |
| `get_execution.py` | API | Single execution incl. per-node timings & errors |
| `execution_stats.py` | API | Aggregate stats (success rate, p50/p95/p99 duration, top errors) |
| `list_credentials.py` | API | Credential metadata (NEVER secret values) |
| `list_tags.py` | API | All tags (for tag-filter UX) |
| `list_projects.py` | API | All projects/workspaces (find projectId) |
| `list_variables.py` | API | n8n env variables ($vars.*) — values redacted in summary |
| `source_control_status.py` | API | Git source-control status (read-only; pull/push are REFUSED) |
| `audit_log.py` | both | Security audit (CLI form is richer markdown) |
| `compare_workflows.py` | local | Diff two workflow JSON files; default-strips noisy fields (versionId/updatedAt/webhookId) |

### Additive write (gated)

| Script | Backend | Purpose |
|---|---|---|
| `import_workflow.py` | API or CLI | Import from JSON. Forces top-level `active=False` on import. Pre-flight ID collision check via API; refuses on auth failure unless `--overwrite`. |
| `publish_workflow.py` | API | Activate/deactivate. `publish`/`unpublish` accepted as aliases. Calls `/activate` & `/deactivate` (the only real endpoints — both 1.x & 2.x). |
| `trigger_workflow.py` | CLI only | Public REST API has no run endpoint. CLI mode = `n8n execute`. `--print-webhook-hint` shows webhook URL for external triggers. WARNS that side effects WILL occur. |
| `export_workflows.py` | API or CLI | Backup workflows. Pure read of n8n; only writes local files. |
| `export_credentials.py` | CLI only | Encrypted backup by default. `--decrypted --confirm-secrets` for plain-text migration. `--output` path validated against shell-meaningful chars + system dirs. |

### Sensitive (double-gated)

`export_credentials.py --decrypted` requires both `--decrypted` AND `--confirm-secrets`. The decrypted JSON file contains plain-text API keys, OAuth tokens, passwords. Treat as a vault: never commit, never log, shred after use.

## Common Workflows

### Daily backup + diff

```bash
SKILL=.claude/skills/n8n-cli/scripts
DATE=$(date +%F)
mkdir -p backups/$DATE
python3 $SKILL/export_workflows.py --output backups/$DATE/workflows --separate
python3 $SKILL/export_credentials.py --output backups/$DATE/creds.enc.json
python3 $SKILL/health_check.py --json > backups/$DATE/health.json
python3 $SKILL/execution_stats.py --limit 1000 --json > backups/$DATE/stats.json
```

Cron: `0 3 * * * cd /repo && bash nightly-n8n.sh`

### Investigate failing workflow

```bash
# Recent failures
python3 $SKILL/list_executions.py --status error --limit 50

# Drill into one
python3 $SKILL/get_execution.py --id <execId> --include-data

# Aggregate stats for the parent workflow
python3 $SKILL/execution_stats.py --workflow <wfid>
```

### Migrate between instances

```bash
# Export from old (decrypted creds — vault file)
python3 $SKILL/export_workflows.py --output /vault/workflows --separate
python3 $SKILL/export_credentials.py --output /vault/creds.json --decrypted --confirm-secrets

# Switch creds, import to new
export N8N_API_URL=https://new... N8N_API_KEY=...
for f in /vault/workflows/*.json; do
  python3 $SKILL/import_workflow.py --file "$f" --confirm
done
n8n import:credentials --input=/vault/creds.json
shred -u /vault/creds.json
```

### Refuse destructive op cleanly

```
$ python3 -c "from _common import refuse_if_destructive_cli; refuse_if_destructive_cli(['delete:workflow', '--id=42'])"
N8nError: REFUSED: `n8n delete:workflow --id=42` is a destructive op blocked by this skill.
  Matched forbidden prefix: delete:workflow
  Run it manually if you intend to.
```

## AskUserQuestion Integration

Script gates (`--confirm`, `--confirm-secrets`) are the hard layer; on top,
`AskUserQuestion` BEFORE any mutation w/ blast radius: activating/deactivating
production workflows, restores that overwrite, decrypted credential export.
Always include a "Cancel" option and name the target instance URL.

## Error Handling

When scripts detect missing creds:

```
MISSING: N8N_API_URL
ASK_USER: Base URL of your n8n instance, e.g. https://n8n.example.com
LOCATION: Self-hosted: your domain. Cloud: https://<workspace>.app.n8n.cloud
```

Permission errors:
```
n8n API GET /api/v1/audit failed (HTTP 403): Forbidden
```

Refused ops:
```
REFUSED: `<command>` is a destructive op blocked by this skill.
  Matched forbidden prefix: <prefix>
  Run it manually if you intend to.
```

Never bypass — even w/ "I'm sure", "force it". Tell the user to do it in the n8n UI.

## Complementary Tools

| Need | Tool |
|---|---|
| Build / edit workflows from scratch | n8n MCP server (`mcp__n8n__*`) |
| Validate node configurations | n8n MCP `validate_workflow` |
| Search node catalog & templates | n8n MCP `search_nodes`, `get_node_types` |
| Bulk reads / backups / CI / cron | **this skill** (faster, no MCP server needed) |
| Decrypted credential export for migration | **this skill** (CLI-only feature) |
| Workflow diffs between environments | **this skill** (`compare_workflows.py`) |

See [`references/cli-vs-mcp.md`](references/cli-vs-mcp.md) for the decision matrix.

## References

| Topic | File |
|---|---|
| Full CLI command map | [`references/cli-commands.md`](references/cli-commands.md) |
| REST API endpoints + auth | [`references/rest-api.md`](references/rest-api.md) |
| Safety boundaries detail | [`references/safety-boundaries.md`](references/safety-boundaries.md) |
| Backup & restore strategy | [`references/backup-strategy.md`](references/backup-strategy.md) |
| CLI vs MCP comparison | [`references/cli-vs-mcp.md`](references/cli-vs-mcp.md) |
| Quick recipes | [`references/quick-recipes.md`](references/quick-recipes.md) |
| Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Integration

Pairs w/:
- **n8n MCP server** — for workflow authoring/validation (this skill is for management)
- `mongodb-atlas-cli` — same safety pattern; if your n8n stores in MongoDB
- `senior-backend` / `code-quality` — for reviewing Code-node JS/Python
