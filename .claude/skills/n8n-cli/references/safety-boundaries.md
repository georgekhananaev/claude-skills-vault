# Safety Boundaries

Exactly what this skill will & won't do.

## Three Tiers

### Tier 1 — Read (allowed, no confirmation)

- List/get workflows, executions, credentials (metadata only), tags, projects
- Health check, audit reports
- Execution stats & filtering
- Encrypted credential export (no plain-text values)
- Workflow exports (additive — only writes local files)

### Tier 2 — Additive write (requires `--confirm` + dry-run preview)

- `import_workflow.py` — imports workflows; defaults to inactive
- `publish_workflow.py` — publish/unpublish a workflow (state change)
- `trigger_workflow.py` — runs a workflow once (causes side effects in integrations!)
- `export_credentials.py --decrypted` — requires BOTH `--decrypted` AND `--confirm-secrets`

### Tier 3 — Destructive (REFUSED — never run, even on request)

#### CLI subcommands blocked
- `delete:workflow` — deletes workflows
- `delete:credentials` — deletes credentials
- `user-management:reset` / `:promote` / `:revoke`
- `mfa:disable`
- `ldap:reset`
- `db:revert` / `db:drop`
- `encryption-key:reset` / `:rotate` (breaks all credentials)
- `license:clear`
- `executionData:prune` / `:delete`

Plus generic destructive tokens scanned in any subcommand: `delete`, `drop`, `destroy`, `remove`, `purge`, `wipe`, `reset`, `force`, `kill`, `terminate`.

#### REST API endpoints blocked
- `DELETE /api/v1/workflows/<id>`
- `DELETE /api/v1/credentials/<id>`
- `DELETE /api/v1/executions/<id>`
- `DELETE /api/v1/users/<id>`, `POST /api/v1/users`, `PATCH /api/v1/users/<id>`
- `DELETE /api/v1/projects/<id>`
- `DELETE /api/v1/tags/<id>`
- `POST /api/v1/source-control/pull` (overwrites local)
- `POST /api/v1/source-control/push` (writes to remote)
- `POST /api/v1/license` / `DELETE /api/v1/license`

## Why these are hard-blocked

| Op | Risk if mistaken |
|---|---|
| Delete workflow | Loss of automation; downstream business logic breaks |
| Delete credentials | Workflows depending on them silently fail / can't reconnect |
| Encryption key rotation | All existing credentials become unreadable |
| User mgmt | Lock out admin or grant unintended access |
| DB ops | Data loss / migration corruption |
| License changes | Loss of paid features |
| Source-control pull | Overwrites local workflows w/ remote state |
| Audit prune | Loss of debugging history |

## Refusal pattern

Refused ops produce:
```
REFUSED: `n8n <command>` is a destructive op blocked by this skill.
  Matched forbidden prefix: <prefix>
  Run it manually if you intend to.
```

For API:
```
REFUSED: `<METHOD> <path>` is destructive — blocked.
  Use the n8n UI or REST client directly if you intend to.
```

Never bypass — even w/ "I'm sure", "force it", "yolo". Tell the user to do it manually in the n8n UI.

## What if a workflow audit suggests deleting something?

Surface the suggestion. Don't act. Recommend dropping unused workflows manually:
1. Verify the workflow is truly unused (check `list_executions.py --workflow <id>` for recent runs)
2. **Disable / unpublish first** via `publish_workflow.py --action unpublish --confirm`
3. Wait several days to confirm nothing breaks
4. Delete manually in n8n UI

## Defense in depth

`scripts/_common.py` enforces both:
1. **Forbidden prefix list** — exact match on first positional (CLI) or method+path (API)
2. **Generic destructive token scan** — catches future commands containing dangerous verbs

Run on every `run_n8n_cli()` and `request()` call.
