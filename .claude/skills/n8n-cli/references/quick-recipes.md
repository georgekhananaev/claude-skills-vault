# Quick Recipes

Copy-paste snippets for common n8n ops via this skill.

## Setup (once)

### REST API mode (works on cloud + remote self-hosted)

```bash
# Get an API key from the n8n UI: Settings → n8n API → Create
export N8N_API_URL="https://n8n.example.com"
export N8N_API_KEY="n8n_api_..."

# Verify
python3 .claude/skills/n8n-cli/scripts/validate_env.py
```

### CLI mode (self-hosted only)

```bash
# n8n CLI ships w/ the n8n npm package
npm install -g n8n
n8n --version

# Or w/o install
alias n8n='npx n8n'

# Verify
python3 .claude/skills/n8n-cli/scripts/validate_env.py --backend cli
```

## See what's there

```bash
# All workflows
python3 .claude/skills/n8n-cli/scripts/list_workflows.py

# Active only
python3 .claude/skills/n8n-cli/scripts/list_workflows.py --active true

# Filtered by tag
python3 .claude/skills/n8n-cli/scripts/list_workflows.py --tag prod

# One workflow's full details
python3 .claude/skills/n8n-cli/scripts/get_workflow.py --id <wfid>

# All credentials (no secrets)
python3 .claude/skills/n8n-cli/scripts/list_credentials.py
```

## Recent execution health

```bash
# Last 50 runs across all workflows
python3 .claude/skills/n8n-cli/scripts/list_executions.py

# Failed runs in the last week
python3 .claude/skills/n8n-cli/scripts/list_executions.py --status error --limit 200

# One workflow's runs
python3 .claude/skills/n8n-cli/scripts/list_executions.py --workflow <wfid>

# A single failed execution's details
python3 .claude/skills/n8n-cli/scripts/get_execution.py --id <execId> --include-data

# Aggregate stats (success rate, top errors, p95 duration)
python3 .claude/skills/n8n-cli/scripts/execution_stats.py --limit 1000
```

## Triggering a workflow

```bash
# Dry-run (just shows the command)
python3 .claude/skills/n8n-cli/scripts/trigger_workflow.py --id <wfid>

# Execute via API
python3 .claude/skills/n8n-cli/scripts/trigger_workflow.py --id <wfid> --confirm

# Execute via CLI w/ input data
echo '{"foo": "bar"}' > /tmp/input.json
python3 .claude/skills/n8n-cli/scripts/trigger_workflow.py \
  --id <wfid> --backend cli --input /tmp/input.json --confirm
```

## Publish / unpublish

```bash
# Show current state (read-only)
python3 .claude/skills/n8n-cli/scripts/publish_workflow.py --id <wfid>

# Publish
python3 .claude/skills/n8n-cli/scripts/publish_workflow.py --id <wfid> --action publish --confirm

# Unpublish
python3 .claude/skills/n8n-cli/scripts/publish_workflow.py --id <wfid> --action unpublish --confirm
```

## Backups

```bash
# All workflows, separate files (best for git)
python3 .claude/skills/n8n-cli/scripts/export_workflows.py \
  --output ./backups/$(date +%F)/workflows --separate

# All workflows in one file
python3 .claude/skills/n8n-cli/scripts/export_workflows.py \
  --output ./backups/$(date +%F)/workflows.json --all-in-one workflows.json

# Encrypted credentials backup (safe to commit)
python3 .claude/skills/n8n-cli/scripts/export_credentials.py \
  --output ./backups/$(date +%F)/creds.enc.json
```

## Migrating between n8n instances

```bash
# 1. On OLD instance — export workflows + decrypted credentials
SRC=.claude/skills/n8n-cli/scripts
mkdir -p /secure/migration

python3 $SRC/export_workflows.py --output /secure/migration/workflows --separate

python3 $SRC/export_credentials.py \
  --output /secure/migration/creds.json \
  --decrypted --confirm-secrets

# 2. Set creds for NEW instance (different N8N_API_URL & N8N_API_KEY)
export N8N_API_URL="https://n8n-new.example.com"
export N8N_API_KEY="<new-key>"

# 3. Import workflows (one at a time for clear errors)
for f in /secure/migration/workflows/*.json; do
  python3 $SRC/import_workflow.py --file "$f" --confirm
done

# 4. Import credentials (CLI direct — encrypts w/ new key)
n8n import:credentials --input=/secure/migration/creds.json

# 5. SHRED the plain-text file
shred -u /secure/migration/creds.json
```

## Diff workflows between environments

```bash
# Export from prod
N8N_API_URL=https://prod.example.com N8N_API_KEY=prod_key \
python3 .claude/skills/n8n-cli/scripts/export_workflows.py \
  --output ./prod-backup --separate

# Export from staging
N8N_API_URL=https://staging.example.com N8N_API_KEY=staging_key \
python3 .claude/skills/n8n-cli/scripts/export_workflows.py \
  --output ./staging-backup --separate

# Diff a specific workflow
python3 .claude/skills/n8n-cli/scripts/compare_workflows.py \
  ./prod-backup/<wfid>_*.json \
  ./staging-backup/<wfid>_*.json --markdown
```

## Security audit

```bash
# Markdown audit report (CLI only — richer)
python3 .claude/skills/n8n-cli/scripts/audit_log.py --backend cli > audit-$(date +%F).md

# Specific categories
python3 .claude/skills/n8n-cli/scripts/audit_log.py --categories credentials,nodes
```

## Health check

```bash
# Quick pulse
python3 .claude/skills/n8n-cli/scripts/health_check.py

# JSON for monitoring
python3 .claude/skills/n8n-cli/scripts/health_check.py --json | \
  jq '{api_reachable, success_rate: .recent_executions.success_rate}'
```

## Drop a workflow — manually (skill won't do this)

```javascript
// In the n8n UI: Workflows → ⋯ → Delete
// Or via DB if you really must (NEVER recommended):
//   - SQLite: rm $HOME/.n8n/database.sqlite (NUKES EVERYTHING)
//   - Postgres: connect & DELETE FROM workflow_entity WHERE id = ...
```

## Cron template (daily backup + diff)

```bash
#!/usr/bin/env bash
# nightly-n8n.sh
set -e
SKILL=.claude/skills/n8n-cli/scripts
DATE=$(date +%F)
ROOT=backups/n8n
mkdir -p "$ROOT/$DATE/workflows"

python3 "$SKILL/export_workflows.py" --output "$ROOT/$DATE/workflows" --separate
python3 "$SKILL/export_credentials.py" --output "$ROOT/$DATE/creds.enc.json"
python3 "$SKILL/health_check.py" --json > "$ROOT/$DATE/health.json"
python3 "$SKILL/execution_stats.py" --limit 1000 --json > "$ROOT/$DATE/stats.json"

# Diff against previous day
PREV=$(ls -d $ROOT/2*/ | sort | tail -2 | head -1)
if [ -n "$PREV" ]; then
  for new_file in "$ROOT/$DATE/workflows"/*.json; do
    base=$(basename "$new_file")
    old_file="$PREV/workflows/$base"
    if [ -f "$old_file" ]; then
      python3 "$SKILL/compare_workflows.py" "$old_file" "$new_file" --markdown >> "$ROOT/$DATE/diff.md"
    fi
  done
fi
```

Cron: `0 3 * * * cd /path/to/repo && bash nightly-n8n.sh`
