# Quick Recipes

Copy-paste snippets for the most common ops in this skill.

## Setup once

```bash
# Install
brew install mongodb-atlas
brew install mongosh   # bundled w/ mongodb-atlas already

# Authenticate
atlas auth login   # OR set MONGODB_ATLAS_PUBLIC_API_KEY/PRIVATE_API_KEY env vars

# Verify everything
python3 .claude/skills/mongodb-atlas-cli/scripts/validate_env.py
```

For mongosh-based scripts (list_indexes, explain_query, profiler_status), set:

```bash
export MONGODB_CONNECTION_STRING="mongodb+srv://<your-cluster>.mongodb.net/?authSource=admin"
export MONGODB_USERNAME="<user>"
export MONGODB_PASSWORD="<password>"   # consider using a password manager + a shell alias
```

## Find your project ID & cluster names

```bash
# All projects
atlas projects list -o json | jq -r '.results[] | "\(.id)  \(.name)"'

# Clusters in a project
atlas clusters list --projectId <pid> -o json | jq -r '.results[].name'

# Connection string for a cluster
atlas clusters describe <CLUSTER> --projectId <pid> -o json | jq -r '.connectionStrings.standardSrv'
```

## Run a full audit

```bash
# Full read-only audit (safe to run anytime, on production)
python3 .claude/skills/mongodb-atlas-cli/scripts/performance_audit.py \
  --cluster <CLUSTER> --projectId <pid> --hours 168

# Save JSON for later diffs
python3 .claude/skills/mongodb-atlas-cli/scripts/performance_audit.py \
  --cluster <CLUSTER> --projectId <pid> --json > audit-$(date +%Y-%m-%d).json
```

## Compare two audits week-over-week

```bash
python3 .claude/skills/mongodb-atlas-cli/scripts/audit_diff.py \
  audit-2026-05-09.json audit-2026-05-16.json --markdown > diff.md
```

## See what indexes exist (live, w/ access counts)

```bash
# One collection
python3 .claude/skills/mongodb-atlas-cli/scripts/list_indexes.py \
  --db myapp --collection orders

# Whole database (one block per collection)
python3 .claude/skills/mongodb-atlas-cli/scripts/list_indexes.py --db myapp
```

## Explain a slow query

```bash
# find()
python3 .claude/skills/mongodb-atlas-cli/scripts/explain_query.py \
  --db myapp --collection orders \
  --filter '{"customer_id": "abc"}' --limit 20

# aggregate()
python3 .claude/skills/mongodb-atlas-cli/scripts/explain_query.py \
  --db myapp --collection orders \
  --pipeline '[{"$match": {"customer_id": "abc"}}, {"$group": {"_id": "$status", "n": {"$sum": 1}}}]'
```

## Create an index safely

```bash
# 1. See what's there
python3 .claude/skills/mongodb-atlas-cli/scripts/list_indexes.py \
  --db app --collection users

# 2. Dry-run the create
python3 .claude/skills/mongodb-atlas-cli/scripts/safe_index_create.py \
  --cluster Cluster0 --db app --collection users \
  --key email:1 --unique --name email_unique
# (will warn if duplicate or covered by existing compound)

# 3. Execute
python3 .claude/skills/mongodb-atlas-cli/scripts/safe_index_create.py \
  --cluster Cluster0 --db app --collection users \
  --key email:1 --unique --name email_unique --confirm

# 4. Verify
python3 .claude/skills/mongodb-atlas-cli/scripts/list_indexes.py \
  --db app --collection users | grep email_unique
```

### Compound index (ESR ordering)

```bash
# Equality fields → Sort fields → Range fields
python3 .claude/skills/mongodb-atlas-cli/scripts/safe_index_create.py \
  --cluster Cluster0 --db app --collection orders \
  --key user_id:1 --key status:1 --key created_at:-1 \
  --name user_status_recent --confirm
```

### TTL index (auto-delete old docs)

```bash
python3 .claude/skills/mongodb-atlas-cli/scripts/safe_index_create.py \
  --cluster Cluster0 --db app --collection sessions \
  --key created_at:1 --ttl-seconds 86400 \
  --name sessions_24h_ttl --confirm
```

### Partial index (only some docs)

```bash
echo '{"deleted": false}' > /tmp/pf.json
python3 .claude/skills/mongodb-atlas-cli/scripts/safe_index_create.py \
  --cluster Cluster0 --db app --collection users \
  --key email:1 --partial-filter /tmp/pf.json \
  --name email_active_only --confirm
```

## Drop an index — manually (skill won't do this)

```javascript
// In mongosh
use("app");
db.users.dropIndex("name_of_index_to_drop");
```

Or hide first to test the impact:

```javascript
use("app");
db.runCommand({ collMod: "users", index: { name: "name_of_index", hidden: true } });
// monitor 24-48h
// If issues, unhide:
db.runCommand({ collMod: "users", index: { name: "name_of_index", hidden: false } });
// If all good, drop:
db.users.dropIndex("name_of_index");
```

## Atlas Search

```bash
# List existing search indexes on a coll
python3 .claude/skills/mongodb-atlas-cli/scripts/atlas_search_list.py \
  --cluster Cluster0 --db myapp --collection products

# Generate a starter definition
python3 .claude/skills/mongodb-atlas-cli/scripts/atlas_search_create.py \
  --init-template search > /tmp/search.json
# edit /tmp/search.json to include your fields

# Dry-run
python3 .claude/skills/mongodb-atlas-cli/scripts/atlas_search_create.py \
  --cluster Cluster0 --db myapp --collection products \
  --name products_text --file /tmp/search.json

# Execute
# ... add --confirm
```

### Vector search

```bash
python3 .claude/skills/mongodb-atlas-cli/scripts/atlas_search_create.py \
  --init-template vector > /tmp/vec.json
# edit numDimensions to match your model (e.g. 1536 for OpenAI text-embedding-3-small)

python3 .claude/skills/mongodb-atlas-cli/scripts/atlas_search_create.py \
  --cluster Cluster0 --db myapp --collection docs \
  --name doc_embeddings --file /tmp/vec.json --type vectorSearch --confirm
```

## Health checks

```bash
# Backup status (warn if last snapshot >26h old)
python3 .claude/skills/mongodb-atlas-cli/scripts/backup_status.py \
  --cluster Cluster0 --projectId <pid>

# Active alerts
python3 .claude/skills/mongodb-atlas-cli/scripts/alerts.py \
  --projectId <pid> --status OPEN

# Live cluster metrics
python3 .claude/skills/mongodb-atlas-cli/scripts/cluster_health.py \
  --cluster Cluster0 --projectId <pid> --period PT1H

# Profiler status (in mongosh, per-database)
python3 .claude/skills/mongodb-atlas-cli/scripts/profiler_status.py --db myapp
```

## Weekly automation pattern

```bash
#!/usr/bin/env bash
# weekly-audit.sh — drop in cron
SKILL=.claude/skills/mongodb-atlas-cli/scripts
DATE=$(date +%Y-%m-%d)
OUT=audits

mkdir -p "$OUT"
python3 "$SKILL/performance_audit.py" --cluster Cluster0 --projectId <pid> --hours 168 --json > "$OUT/audit-$DATE.json"

# Diff against last week's
LAST=$(ls -1 "$OUT"/audit-*.json | sort | tail -2 | head -1)
if [ -n "$LAST" ] && [ "$LAST" != "$OUT/audit-$DATE.json" ]; then
  python3 "$SKILL/audit_diff.py" "$LAST" "$OUT/audit-$DATE.json" --markdown > "$OUT/diff-$DATE.md"
  echo "Diff: $OUT/diff-$DATE.md"
fi
```

Cron: `0 9 * * MON cd /path/to/repo && bash weekly-audit.sh`
