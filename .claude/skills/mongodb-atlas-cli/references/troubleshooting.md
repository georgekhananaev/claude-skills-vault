# Troubleshooting

## `atlas: command not found`

**macOS:**
```bash
brew install mongodb-atlas
# Or run our auto-installer
python3 scripts/validate_env.py --install
```

**Linux:** apt/yum guides at https://www.mongodb.com/docs/atlas/cli/current/install-atlas-cli/

**Docker fallback (any OS):**
```bash
docker pull mongodb/atlas
alias atlas='docker run --rm -it -v ~/.config/atlas:/root/.config/atlas mongodb/atlas atlas'
```

## `Error: project ID not set`

You're missing `MONGODB_ATLAS_PROJECT_ID` & no profile default.

```bash
# Find your project ID — Atlas UI URL: /v2/<24-hex>/...
export MONGODB_ATLAS_PROJECT_ID=64a1b2c3d4e5f6a7b8c9d0e1
```

Or save in a profile:
```bash
atlas config set project_id 64a1b2c3d4e5f6a7b8c9d0e1
```

## `Error: status code 401 (request "INVALID_API_KEY")`

API key invalid or expired. Generate a new one:
- Atlas UI → Project Settings → Access Manager → API Keys → Create
- Save the **private** key immediately — it's shown only once.

```bash
export MONGODB_ATLAS_PUBLIC_API_KEY=...
export MONGODB_ATLAS_PRIVATE_API_KEY=...
```

## `Error: status code 403 (request "PROJECT_DATA_ACCESS_ADMIN")`

API key lacks permission for the op. Roles needed:

| Op | Role |
|----|------|
| Read clusters/processes/metrics | Project Read Only |
| Performance Advisor reads | Project Read Only (some need Project Data Access Read/Write) |
| Create indexes | Project Data Access Admin |

Edit the API key in Atlas UI → Project Settings → Access Manager → API Keys → Edit.

## `No processes found for cluster X`

Cluster name typo or different project. Check:

```bash
atlas clusters list --output json | jq -r '.results[].name'
```

## `processName mismatch in performanceAdvisor`

The `processName` arg must be **exactly** `host:port` of a running mongod. The skill's `_common.py:primary_process()` resolves this from `atlas processes list`. If it picks the wrong host:

```bash
# List all processes, find the one you want
atlas processes list --output json | jq '.results[] | {id, replicaSetName, typeName}'
```

Pass the host explicitly to the underlying CLI command if needed.

## Slow queries returns empty array

Possible reasons:
- No slow ops in the time window — increase `--hours`
- Slow op threshold is too high — check Atlas UI → Cluster → Profiler
- Cluster tier (M0/M2/M5) doesn't expose Performance Advisor — only M10+

## Index creation hangs

Atlas builds rolling indexes — one node at a time. Build time scales w/ collection size:

| Collection size | Approx build time |
|-----------------|-------------------|
| < 1 GB | < 5 min |
| 1–10 GB | 5–30 min |
| 10–100 GB | 30 min – 4 hr |
| > 100 GB | hours, plan for off-peak |

Monitor progress in Atlas UI → Collection → Indexes. Submission completes immediately; build runs async.

## `safe_index_create.py` says "REFUSED"

The destructive-token guard in `_common.py` fired. Check that:
- `--collection` and `--db` names don't contain `delete`, `drop`, etc.
- Index name doesn't contain those tokens

If your collection is legitimately named `delete_queue`, you'll need to use `mongosh` or Atlas UI directly — the skill won't whitelist it.

## Output is truncated in human-readable mode

`emit_human()` truncates payloads at 4000 chars. For full output use `--json`:

```bash
python3 scripts/suggest_indexes.py --cluster Cluster0 --json | jq .
```

## Performance Advisor shows nothing useful

Advisor needs traffic to learn from:
- Run for at least a few hours after cluster start
- Cluster must be M10+ (free/shared tiers don't have it)
- Pre-aggregated metrics may take ~1h to populate

For low-traffic dev clusters, advisor output is genuinely sparse — that's fine.
