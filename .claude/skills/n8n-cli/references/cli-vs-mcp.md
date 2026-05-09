# CLI vs MCP — When to Use Which

Both this skill and the n8n MCP server (`mcp__n8n__*` tools) talk to n8n. They are complementary, not redundant.

## Quick decision tree

| Goal | Use |
|---|---|
| Build a workflow from scratch | **MCP** (`mcp__n8n__create_workflow_from_code`, validation, node search) |
| Edit a single workflow's nodes/connections | **MCP** (rich validation surface) |
| Search the node catalog | **MCP** (`search_nodes`) |
| Get node parameter docs | **MCP** (`get_node_types`) |
| List/inspect workflows in bulk | **CLI skill** (this one) |
| Trigger executions | **CLI skill** (or MCP `execute_workflow`) |
| Daily backup of all workflows | **CLI skill** (`export_workflows.py`) |
| Backup credentials (encrypted) | **CLI skill** (CLI-only feature) |
| Migrate between n8n instances | **CLI skill** (export/import) |
| Read execution history & stats | **CLI skill** (faster — direct paginated API) |
| Audit security posture | **CLI skill** (`audit_log.py`) |
| Diff workflows between environments | **CLI skill** (`compare_workflows.py`) |
| Schedule cron-based health checks | **CLI skill** (no MCP server needed at runtime) |

## Why CLI skill is "more efficient" for some workloads

1. **No MCP server overhead** — direct REST API or subprocess. Ms vs hundreds-of-ms per call.
2. **Bulk operations** — list all workflows, export all, paginate efficiently. MCP `search_workflows` returns one page at a time.
3. **Scriptable / CI-friendly** — runs in cron, GitHub Actions, etc. Doesn't need an MCP-aware client.
4. **Local-only ops** — `compare_workflows.py` runs over local JSON files; no network round trip.
5. **CLI-exclusive features** — `n8n audit`, decrypted credential export, separate-file modes.

## Why MCP wins for authoring

1. **Rich node schema** — knows every parameter for every node, validates configurations.
2. **Iterative refinement** — Claude can validate → fix → re-validate in tight loops.
3. **Natural language queries** — "find a node that does X".
4. **Templates** — pre-built workflow patterns.
5. **No file I/O** — reads/writes workflows directly.

## Combined workflow example

```
# 1. Create / refine workflow w/ MCP
mcp__n8n__search_nodes("slack")
mcp__n8n__create_workflow_from_code(...)
mcp__n8n__validate_workflow(...)

# 2. Daily backup w/ this skill
python3 .claude/skills/n8n-cli/scripts/export_workflows.py --output ./backup --separate

# 3. Diff vs. previous backup
python3 .claude/skills/n8n-cli/scripts/compare_workflows.py \
  ./backup-yesterday/<wfid>.json \
  ./backup/<wfid>.json --markdown

# 4. Production health check (this skill)
python3 .claude/skills/n8n-cli/scripts/health_check.py
python3 .claude/skills/n8n-cli/scripts/execution_stats.py --limit 1000
```

## Performance comparison (rough)

| Operation | MCP | This skill |
|---|---|---|
| List 250 workflows | ~1.5s (paginated MCP calls) | ~0.3s (direct API) |
| Export all workflows | not directly supported | ~2s for 50 workflows |
| Get one workflow | ~0.4s | ~0.15s |
| Health check | tool round trip | direct ping |
| `audit` report | not in MCP | CLI / API direct |

(Numbers are illustrative — depends on instance latency.)

## Both have hard refusal guards

- MCP: server-side enforcement of read-only mode (configurable).
- This skill: client-side `_common.py` refusal guard, 13+ forbidden CLI prefixes, 11+ forbidden API endpoints.

## When neither is right

- Browsing workflows in a UI: use the n8n web app.
- Building workflows w/o coding: use the n8n web app.
- Debugging a single failed execution interactively: n8n UI's execution viewer.
