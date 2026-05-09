# Backup Strategy

How to use this skill for reliable n8n disaster recovery.

## What needs backing up

| Asset | What it is | Backup script | Sensitivity |
|---|---|---|---|
| Workflows | Node graphs + settings + connections | `export_workflows.py` | Public-ish |
| Encrypted credentials | OAuth tokens, API keys (encrypted at rest) | `export_credentials.py` | Useless w/o key |
| Decrypted credentials | Plain-text secret values | `export_credentials.py --decrypted --confirm-secrets` | **CRITICAL** |
| n8n encryption key | The key that encrypts the above | NOT THIS SKILL — see n8n config | **CRITICAL** |
| Database | SQLite file or Postgres dump | n8n CLI `db:*` (REFUSED here) — use `pg_dump` etc. | Critical |

## Recommended cadence

| Frequency | What | Where |
|---|---|---|
| Daily | Workflows + encrypted credentials | Git repo (private) or S3-style storage |
| Weekly | Full DB dump | Off-site encrypted storage |
| Before any major change | Full backup of everything | Local + remote |
| Before `import_workflow.py --confirm` | Snapshot the workflow being overwritten | `export_workflows.py --id <wfid>` |

## Daily script template

```bash
#!/usr/bin/env bash
# nightly-n8n-backup.sh
SKILL=.claude/skills/n8n-cli/scripts
DATE=$(date +%Y-%m-%d)
OUT=backups/n8n/$DATE
mkdir -p "$OUT"

# Workflows — all, separate files (clean diffs in git)
python3 "$SKILL/export_workflows.py" --output "$OUT/workflows" --separate

# Encrypted credentials (safe to commit; useless w/o n8n encryption key)
python3 "$SKILL/export_credentials.py" --output "$OUT/credentials.enc.json"

# Health snapshot
python3 "$SKILL/health_check.py" --json > "$OUT/health.json"

# Execution stats
python3 "$SKILL/execution_stats.py" --limit 1000 --json > "$OUT/exec-stats.json"

# Optional: commit to a private repo
( cd backups && git add . && git commit -m "n8n backup $DATE" )
```

Cron: `0 3 * * * cd /path/to/repo && bash nightly-n8n-backup.sh`

## Restore flow

### Workflows only

```bash
# 1. Inspect what's in the backup
python3 .claude/skills/n8n-cli/scripts/list_workflows.py    # current state
ls backups/n8n/2026-05-09/workflows/

# 2. Dry-run import
python3 .claude/skills/n8n-cli/scripts/import_workflow.py \
  --file backups/n8n/2026-05-09/workflows/<file>.json

# 3. Execute (creates new workflow w/ new ID via API; preserves ID via CLI)
python3 .claude/skills/n8n-cli/scripts/import_workflow.py \
  --file backups/n8n/2026-05-09/workflows/<file>.json --confirm
```

### Encrypted credentials → same instance (key unchanged)

```bash
n8n import:credentials --input=backups/n8n/2026-05-09/credentials.enc.json
```

(Skill doesn't wrap this — call CLI directly. The decryption uses your existing `N8N_ENCRYPTION_KEY`.)

### Migrating to new instance (different encryption key)

The DECRYPTED export path. Treat output as a vault.

```bash
# On OLD instance — export plain-text
python3 .claude/skills/n8n-cli/scripts/export_credentials.py \
  --output /secure/migration/creds.json \
  --decrypted --confirm-secrets

# On NEW instance — import (encrypts w/ new key)
n8n import:credentials --input=/secure/migration/creds.json

# Then DELETE the plain-text file
shred -u /secure/migration/creds.json
```

## What NOT to commit to public repos

- Decrypted credentials JSON
- The n8n `.n8n/config` file (contains encryption key)
- The DB file (`database.sqlite`)
- Anything with the words "decrypted" in the filename

`.gitignore` template:

```gitignore
# n8n secrets
*.decrypted.json
**/credentials*.json
.n8n/
database.sqlite
N8N_ENCRYPTION_KEY*
```

## Verifying a backup is restorable

Periodically (monthly):
1. Spin up a temp n8n instance: `docker run -p 5679:5678 n8nio/n8n`
2. Set `N8N_ENCRYPTION_KEY` to the same value as production
3. Import a workflow + matching credential
4. Trigger via `trigger_workflow.py --confirm` and verify it runs end-to-end

This is how you catch silent backup corruption.
