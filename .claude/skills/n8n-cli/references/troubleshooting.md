# Troubleshooting

## `n8n: command not found`

```bash
npm install -g n8n
# or use without install:
alias n8n='npx n8n'
```

If you're on Linux & the global install fails, prefix npm w/ `sudo` or use `nvm`.

## `MISSING: N8N_API_URL` / `N8N_API_KEY`

Set both env vars:

```bash
export N8N_API_URL="https://n8n.example.com"     # no trailing slash
export N8N_API_KEY="n8n_api_..."                 # from Settings → n8n API
```

Don't include `/api/v1` in the URL — the skill appends it.

## HTTP 401 — `Unauthorized`

API key is invalid, expired, or revoked.

1. Settings → n8n API → revoke + recreate
2. Update `N8N_API_KEY`
3. Re-run `validate_env.py`

## HTTP 403 — `Forbidden`

Key valid, but user lacks permission for the endpoint. Common cases:
- Audit endpoints: only owners/admins can hit `/api/v1/audit`
- User mgmt endpoints: admins only (this skill blocks these anyway)

Check the API user's role in n8n UI → Settings → Users.

## HTTP 429 — `Too Many Requests`

n8n Cloud rate-limits API calls. Add a delay between bulk ops:

```python
import time; time.sleep(1)   # in your loop
```

Or increase `N8N_TIMEOUT` so retries don't compound.

## `import_workflow.py` says "DUPLICATE"

The workflow file has an `id` field that matches an existing workflow. Options:

1. **Strip the ID** to create a new workflow w/ a fresh ID:
   ```bash
   jq 'del(.id)' workflow.json > workflow-fresh.json
   python3 import_workflow.py --file workflow-fresh.json --confirm
   ```

2. **Overwrite intentionally** (CLI mode only):
   ```bash
   python3 import_workflow.py --file workflow.json --backend cli --overwrite --confirm
   ```

## `trigger_workflow.py` returns `404`

Common causes:
- Wrong workflow ID
- Workflow is unpublished (some n8n versions reject runs of unpublished workflows)
- API user can't see the workflow's project

Check w/:
```bash
python3 .claude/skills/n8n-cli/scripts/get_workflow.py --id <wfid>
```

## CLI export hangs / is silent

The CLI commands take a while on large instances (1000+ workflows). Output appears only after the operation completes. Run w/ `time` to see actual cost:

```bash
time n8n export:workflow --all --output=workflows.json
```

For real-time progress, prefer the API mode (`export_workflows.py --backend api`) — it processes one workflow at a time.

## Imported workflow doesn't show up

n8n caches workflow lists in some versions. Try:
1. Reload the n8n UI tab
2. Restart the n8n process (`docker restart` or systemctl)

## Decrypted credential export fails

`n8n export:credentials --decrypted` requires the `N8N_ENCRYPTION_KEY` env var to be set to your encryption key. The CLI uses this to decrypt the at-rest credentials.

Find your key:
- Self-hosted Docker: check the env vars passed to the container
- Self-hosted bare: `~/.n8n/config` → `encryptionKey` field
- n8n Cloud: not user-accessible (use API only)

## Comparison `compare_workflows.py` shows tons of changes for an unchanged workflow

Some n8n versions update internal fields (`webhookId`, `versionId`, `updatedAt`) on every save. The diff captures these but they're noise. Filter w/ `jq`:

```bash
jq 'del(.versionId, .updatedAt, .webhookId)' a.json > a.clean.json
jq 'del(.versionId, .updatedAt, .webhookId)' b.json > b.clean.json
python3 compare_workflows.py a.clean.json b.clean.json
```

## `publish_workflow.py` returns 404 on `/publish`

You're on n8n 1.x where the endpoint was `/activate` instead. The script auto-falls-back, but if both fail, n8n is on a much older version (< 1.0). Update n8n.

## Skill refused a non-destructive op

Open a bug — the refusal guard is intentionally aggressive. The forbidden list is in `_common.py:FORBIDDEN_CLI_PREFIXES` and `FORBIDDEN_API_PATHS`. Generic token scan also catches `delete`, `drop`, etc. — see `references/safety-boundaries.md`.

If you ever genuinely need a destructive op, run the underlying `n8n` CLI or a `curl` directly.
