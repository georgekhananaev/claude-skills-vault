---
name: mongodb-atlas-cli
description: Comprehensive MongoDB Atlas + mongosh skill for performance auditing, all index types (b-tree/text/2dsphere/hashed/TTL/partial/wildcard/Atlas-Search/Vector-Search), Performance Advisor analysis, query explain, schema advice, backup status, alerts, week-over-week diffs, and additive index creation. Read-only by default; create-index ops gated behind explicit `--confirm`. Hard-blocks any destructive op (delete, drop, restore, pause, terminate, kill, dbuser write, network change). Works against Atlas Cloud (full feature set) and self-hosted/local mongo (mongosh-based subset).
---

# MongoDB Atlas CLI Skill

Comprehensive coverage of MongoDB Atlas operations w/ strict safety guarantees. Optimized for the loop: **read Performance Advisor → review suggestions → create the right indexes safely**. Never destructive.

## When to Use

Invoke when the user wants to:

- Connect to Atlas, list clusters/processes/projects
- Pull Performance Advisor output (slow queries, suggested indexes, schema advice, drop hints)
- Read cluster/process/database metrics, alerts, backup status
- List existing indexes w/ live access counts (mongosh-based)
- Explain a query (find or aggregate)
- Create indexes — single, compound, TTL, sparse, partial, unique, geospatial, hashed, Atlas Search, Vector Search
- Diff two audits week-over-week
- Audit overall cluster performance
- Diagnose slow queries before code changes

**Do NOT use for** any destructive op. Direct CRUD against data is also out of scope (use `mongosh` directly or the official MongoDB MCP server — see [Integration](#complementary-tools)).

## Hard Safety Boundaries

| Category | Op | Action |
|----------|-----|--------|
| Read | clusters/processes/metrics/logs/projects | Allowed, no confirm |
| Read | performanceAdvisor (all subcmds) | Allowed, no confirm |
| Read | api performanceAdvisor list* | Allowed, no confirm |
| Read | alerts/events/backups list, dbusers list | Allowed, no confirm |
| Read | clusters search indexes list | Allowed, no confirm |
| Read | mongosh: getIndexes, $indexStats, .explain(), getProfilingStatus | Allowed, no confirm |
| Write (additive) | `clusters indexes create` | Requires `--confirm` + dry-run + duplicate pre-flight |
| Write (additive) | `clusters search indexes create` | Requires `--confirm` + dry-run |
| Destructive | `delete`, `drop`, `terminate`, `pause`, `restore`, `kill`, `force` | **REFUSE** — never run, even w/ user request |
| Destructive | `dbusers create/update/delete` | **REFUSE** — auth changes can lock prod |
| Destructive | `networking *` writes, `accessLists delete` | **REFUSE** — can sever connectivity |
| Destructive | `backups restore` / snapshot delete | **REFUSE** — overwrites data |
| Destructive | `clusters indexes delete` | **REFUSE** — even if advisor suggests dropping; only INFORM the user |

If user asks to drop an index based on `listDropIndexSuggestions`, surface the suggestion and tell them to do it manually in mongosh / Atlas UI. Never run it.

## Local Mongo vs. Atlas Cloud

This skill works against **both**, but coverage differs. Performance Advisor, metrics, backups, alerts, Atlas Search are cloud-only. mongosh-based scripts (list_indexes, explain_query, profiler_status) work everywhere. Full matrix in [`references/local-vs-atlas.md`](references/local-vs-atlas.md).

For local self-hosted mongo, `safe_index_create.py --print-mongosh` outputs the equivalent `createIndex()` snippet you can run directly in mongosh.

## Prerequisites

### Install

```bash
# macOS — both atlas CLI + mongosh
brew install mongodb-atlas

# Linux — see https://www.mongodb.com/docs/atlas/cli/current/install-atlas-cli/

# Docker fallback (any OS)
docker pull mongodb/atlas
alias atlas='docker run --rm -it -v ~/.config/atlas:/root/.config/atlas mongodb/atlas atlas'

# Verify
atlas --version && mongosh --version
```

`validate_env.py --install` auto-installs via brew on macOS.

### Authenticate (Atlas Admin API)

Pick one (priority order):

```bash
# 1. Env vars (recommended for automation)
export MONGODB_ATLAS_PUBLIC_API_KEY=<public_key>
export MONGODB_ATLAS_PRIVATE_API_KEY=<private_key>
export MONGODB_ATLAS_PROJECT_ID=<24-hex-project-id>

# 2. Profile config
atlas config init

# 3. Browser
atlas auth login
```

API key role: **Project Read Only** for reads, **Project Data Access Admin** for index creation. Get keys: Atlas UI → Project Settings → Access Manager → API Keys.

### Authenticate (mongosh-based scripts)

For `list_indexes.py`, `explain_query.py`, `profiler_status.py`, `safe_index_create.py` pre-flight:

```bash
export MONGODB_CONNECTION_STRING="mongodb+srv://<host>.mongodb.net/?authSource=admin"
export MONGODB_USERNAME="<atlas-db-user>"
export MONGODB_PASSWORD="<password>"
```

DB user is **separate** from API key — Atlas UI → Database Access → ADD NEW DATABASE USER. See [`references/mongosh-integration.md`](references/mongosh-integration.md).

### Validate

```bash
python3 .claude/skills/mongodb-atlas-cli/scripts/validate_env.py
```

## Script Index

### Atlas Admin API (read-only, no DB credentials needed)

| Script | Task |
|---|---|
| `validate_env.py` | Check CLI install + auth + project access |
| `performance_audit.py` | Full read-only audit (orchestrator) |
| `namespaces.py` | Performance Advisor → list hot namespaces (entry point) |
| `suggest_indexes.py` | Performance Advisor → suggested new indexes |
| `slow_queries.py` | Performance Advisor → slow query log lines |
| `schema_advice.py` | Performance Advisor → schema anti-pattern recommendations |
| `drop_index_hints.py` | Performance Advisor → redundant/hidden/unused indexes (advisory) |
| `cluster_health.py` | Process metrics (CPU/mem/conn/op counters/query targeting) — parallel fetches |
| `alerts.py` | Active Atlas alerts |
| `backup_status.py` | Snapshot list + freshness check |
| `events.py` | Project events / audit log |
| `atlas_search_list.py` | List Atlas Search & Vector Search indexes |
| `audit_diff.py` | Compare two audit JSON snapshots — week-over-week diff |

### Atlas Admin API (additive write — gated by `--confirm`)

| Script | Task |
|---|---|
| `safe_index_create.py` | Create normal index — single/compound/TTL/sparse/partial/unique/2dsphere/hashed |
| `atlas_search_create.py` | Create Atlas Search OR Vector Search index |

### mongosh-based (works on local + Atlas — needs DB user creds)

| Script | Task |
|---|---|
| `list_indexes.py` | List indexes per coll/db w/ live access counts & sizes — parallel per coll |
| `explain_query.py` | Run `.explain()` on find or aggregate query |
| `profiler_status.py` | DB profiler level + recent slow ops captured |
| `index_build_status.py` | Poll in-progress index builds via `db.currentOp()` |

All mongosh scripts validate db/collection identifiers before interpolating into JS to prevent injection. Passwords passed via stdin (not argv) to avoid `/proc/<pid>/cmdline` exposure on Linux.

### Pure local

| Script | Task |
|---|---|
| `audit_diff.py` | Compare audits week-over-week (no Atlas calls) |
| `safe_index_create.py --print-mongosh` | Print mongosh createIndex() snippet for local use |

All scripts default to **dry-run/read-only**. Mutations need explicit `--confirm`.

## Common Workflows

### 1. Optimize from advisor → index

```bash
# Full picture
python3 scripts/performance_audit.py --cluster <C> --hours 168

# Verify what's already there
python3 scripts/list_indexes.py --db <DB> --collection <COLL>

# Inspect a specific suggestion's query first
python3 scripts/explain_query.py --db <DB> --collection <COLL> --filter '{...}'

# Create (dry-run)
python3 scripts/safe_index_create.py --cluster <C> --db <DB> --collection <COLL> \
  --key field:1 --name idx_field

# Execute
python3 scripts/safe_index_create.py --cluster <C> --db <DB> --collection <COLL> \
  --key field:1 --name idx_field --confirm

# Re-audit after build completes
python3 scripts/performance_audit.py --cluster <C>
```

### 2. Atlas Search for case-insensitive regex queries

When schema advice flags `OPTIMIZE_CASE_INSENSITIVE_REGEX_QUERIES`:

```bash
# See existing search indexes
python3 scripts/atlas_search_list.py --cluster <C> --db <DB> --collection <COLL>

# Generate starter definition
python3 scripts/atlas_search_create.py --init-template search > search.json
# edit search.json

# Dry-run
python3 scripts/atlas_search_create.py --cluster <C> --db <DB> --collection <COLL> \
  --name <coll>_text --file search.json

# Execute
python3 scripts/atlas_search_create.py --cluster <C> --db <DB> --collection <COLL> \
  --name <coll>_text --file search.json --confirm
```

### 3. Vector Search for AI / RAG

```bash
python3 scripts/atlas_search_create.py --init-template vector > vec.json
# edit vec.json — set numDimensions matching your embedding model
python3 scripts/atlas_search_create.py --cluster <C> --db <DB> --collection <COLL> \
  --name <coll>_vec --file vec.json --type vectorSearch --confirm
```

### 4. Drop redundant indexes (manually — skill won't drop)

```bash
# Get advisory list
python3 scripts/drop_index_hints.py --cluster <C>

# Verify w/ live counters
python3 scripts/list_indexes.py --db <DB> --collection <COLL>

# Confirm covering index serves a real query
python3 scripts/explain_query.py --db <DB> --collection <COLL> \
  --filter '{<typical_filter>}'

# Hide first (24-48h soak), then drop manually in mongosh
mongosh ... --eval 'db.runCommand({collMod: "<COLL>", index: {name: "<NAME>", hidden: true}})'
```

### 5. Weekly automation

```bash
# Save snapshot
python3 scripts/performance_audit.py --cluster <C> --hours 168 --json > audits/$(date +%F).json

# Diff vs. last week
python3 scripts/audit_diff.py audits/<old>.json audits/<new>.json --markdown > diff.md
```

### 6. Health checks (read-only, run anytime)

```bash
python3 scripts/cluster_health.py --cluster <C>
python3 scripts/backup_status.py --cluster <C>
python3 scripts/alerts.py --status OPEN
```

## Index Types Supported

`safe_index_create.py` covers every standard MongoDB index type:

| Type | Flag combination | Atlas-only? |
|---|---|---|
| Single-field | `--key field:1` | no |
| Compound | `--key f1:1 --key f2:-1 ...` | no |
| TTL | `--key created_at:1 --ttl-seconds N` | no |
| Sparse | `--sparse` | no |
| Partial | `--partial-filter pf.json` | no |
| Unique | `--unique` | no |
| Combined (e.g. unique + partial) | `--unique --partial-filter pf.json` | no |
| Geospatial 2dsphere | `--key location:2dsphere` | no |
| Hashed (sharding) | `--key user_id:hashed` | no |
| Text (legacy) | `--key field:text` | no |
| Wildcard | `--file <json>` w/ `{"keys": [{"$**": 1}]}` | no |
| Atlas Search | `atlas_search_create.py --type search` | **yes** |
| Vector Search | `atlas_search_create.py --type vectorSearch` | **yes** |

Full reference: [`references/index-types.md`](references/index-types.md).

## Pre-flight Duplicate Detection

`safe_index_create.py` runs a pre-flight via mongosh (when creds are available) that checks if:
- An index w/ **identical keys** already exists → refuses to create duplicate
- An existing **larger compound** already covers the proposed keys as a prefix → refuses (your index would be redundant)

Override w/ `--skip-preflight` (not recommended). If mongosh creds aren't available, pre-flight is silently skipped.

## Output Format

Default: human-readable summary to stderr, JSON to stdout when `--json` flag set. Pipe through `jq`:

```bash
python3 scripts/suggest_indexes.py --cluster <C> --json | jq '.[] | .namespace'
```

## Error Handling

When scripts detect missing credentials or permission errors, they output:

```
MISSING: <ENV_VAR>
ASK_USER: <human prompt>
LOCATION: <where to find the value>
```

Claude should parse & use AskUserQuestion to prompt.

For permission errors:
```
PERMISSION_DENIED: requires <role>
ACTION: Ask user to grant role or use a different API key
```

## Refusal Pattern

Refused destructive ops produce:

```
REFUSED: `atlas <command>` is a destructive op blocked by this skill.
  Matched forbidden prefix: <prefix>
  Run it manually in Atlas UI or via `atlas` directly if you intend to.
```

Never bypass — even w/ "I'm sure", "force it", "yolo". Tell the user to run it manually.

## Complementary Tools

This skill focuses on **admin/audit/index-management**. For complementary capabilities:

| Need | Tool |
|---|---|
| AI-assisted CRUD against data, NL → query, schema introspection | [MongoDB MCP Server](https://www.mongodb.com/docs/mcp-server/get-started/) |
| Atlas Stream Processing pipelines | [jwongmongodb/atlas-streams-skills](https://github.com/jwongmongodb/atlas-streams-skills) |
| Connection pool / driver tuning | [MongoDB Agent Skills — Connection](https://github.com/mongodb/agent-skills) |
| Schema design from scratch | sibling `pydantic-model` skill in this repo |

## References

| Topic | File |
|---|---|
| Full Atlas CLI command map | [`references/cli-commands.md`](references/cli-commands.md) |
| Performance Advisor deep-dive | [`references/performance-advisor.md`](references/performance-advisor.md) |
| Index strategy (ESR, etc.) | [`references/index-strategy.md`](references/index-strategy.md) |
| **Every index type w/ examples** | [`references/index-types.md`](references/index-types.md) |
| **Atlas Search + Vector Search** | [`references/atlas-search.md`](references/atlas-search.md) |
| **Local vs. Atlas feature matrix** | [`references/local-vs-atlas.md`](references/local-vs-atlas.md) |
| **mongosh integration details** | [`references/mongosh-integration.md`](references/mongosh-integration.md) |
| **Quick recipes (copy-paste)** | [`references/quick-recipes.md`](references/quick-recipes.md) |
| Safety boundaries detail | [`references/safety-boundaries.md`](references/safety-boundaries.md) |
| Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Integration

Pairs w/:
- `senior-backend` — schema/query design before adding indexes
- `code-quality` — review query code that produces slow ops
- `pydantic-model` — model-level fixes that reduce doc bloat
- MongoDB MCP server — for direct data ops
