# Performance Advisor — Deep Dive

How to read & act on output from each Performance Advisor source.

## What It Does

Atlas Performance Advisor analyzes the cluster's slow-query log (queries that exceed the slow op threshold — default 100ms, auto-tuned per workload) and produces 4 kinds of output:

1. **Slow query log lines** — raw lines of slow ops grouped by query shape
2. **Suggested indexes** — indexes that, if created, would speed up observed slow queries
3. **Drop index suggestions** — hidden, redundant, or unused indexes that could be removed (this skill **never** drops them)
4. **Schema advice** — anti-pattern findings like unbounded arrays or bloated documents

## Slow Queries (`slowQueryLogs list`)

### Reading the output

Each entry has:
- `namespace` — `db.collection`
- `line` — full mongod log line (JSON-format since 4.4)
- `opType` — `query`, `aggregate`, `update`, `getMore`, `count`
- `durationMillis`

### Triage flow

1. Group by namespace → which collections are hot?
2. Group by query shape → which filters/sorts repeat?
3. For top shapes, check `planSummary` in the log line:
   - `COLLSCAN` → missing index
   - `IXSCAN { ... }` followed by `FETCH` w/ `nreturned << docsExamined` → index has wrong shape
   - `SORT` (in-memory) → missing sort key in compound index
4. Map shape → suggested index from `suggestedIndexes list`

### Helpful awk

```bash
# Count slow queries per namespace
python3 scripts/slow_queries.py --cluster Cluster0 --json | \
  jq -r '.[].namespace' | sort | uniq -c | sort -rn
```

## Suggested Indexes (`suggestedIndexes list`)

### Output shape

```json
{
  "namespace": "app.users",
  "weight": 0.95,            // 0–1, advisor's confidence
  "index": [{"field": "email", "direction": 1}],
  "impact": [
    {"namespace": "app.users", "predicates": ["email = ?"], "..."}
  ]
}
```

### Decision criteria

Don't blindly accept all suggestions. Check:

- **Cardinality** — index on a low-cardinality field (e.g., `is_active: bool`) wastes space. Better as compound w/ a high-cardinality field.
- **Write rate** — every index slows writes. If the collection is write-heavy & the suggested index covers an infrequent query, skip it.
- **Existing indexes** — could the workload be solved by extending an existing compound index instead of adding a new one?
- **ESR rule** for compound indexes: **E**quality fields → **S**ort fields → **R**ange fields.

### Example workflow

```bash
# 1. See suggestions
python3 scripts/suggest_indexes.py --cluster Cluster0

# 2. Verify w/ slow query lines
python3 scripts/slow_queries.py --cluster Cluster0 --namespace app.users

# 3. Create the index (dry-run first)
python3 scripts/safe_index_create.py --cluster Cluster0 \
  --db app --collection users --key email:1
# Review output, then add --confirm

# 4. Wait ~minutes-hours for build, then re-audit
python3 scripts/performance_audit.py --cluster Cluster0
```

## Drop Index Hints (`listDropIndexSuggestions`)

Returns three categories:
- `hiddenIndexes` — already invisible to planner; safe candidates for full removal
- `redundantIndexes` — fully covered by another index; deletable w/o query impact
- `unusedIndexes` — no recent reads; deletable but verify w/ app team first

### **This skill does not drop indexes.** Surface the hint, recommend the user drop manually:

```js
// In mongosh, connected to cluster
db.<collection>.dropIndex("<index_name>")
```

Or Atlas UI: Cluster → Collections → Indexes → ⋯ → Drop.

## Schema Advice (`listSchemaAdvice`)

Holistic recommendations from sampled documents. Common findings:

| Finding | Meaning | Fix |
|---------|---------|-----|
| `reduceNumberOfNamespaces` | Too many small collections | Consolidate, embed |
| `reduceDocumentSize` | Avg doc > ~500KB | Move large fields to GridFS or separate collection |
| `removeUnnecessaryIndexes` | Index count > 10 per coll | Cross-ref drop hints |
| `avoidUnboundedArrays` | Array fields growing unbounded | Bucket pattern |
| `useSchemaValidationToEnforceTypes` | Field types inconsistent | Add `$jsonSchema` validator |

These require **app + schema changes**, not Atlas-only ops. Discuss w/ the team before acting.

## Slow Op Threshold

Atlas auto-tunes slow op threshold based on cluster's typical op duration. To inspect or override:

```bash
atlas performanceAdvisor slowOperationThreshold list
# (Read-only — disabling/enabling is a write op; do it in Atlas UI if needed)
```

## Sources

- https://www.mongodb.com/docs/atlas/performance-advisor/
- https://www.mongodb.com/docs/atlas/performance-advisor/index-ranking/
- https://www.mongodb.com/docs/manual/core/index-compound/
