# Index Design Strategy

Decision rules for picking & designing indexes from advisor output.

## ESR Rule (Compound Indexes)

Order keys: **Equality → Sort → Range**.

```js
// Query: find({status: "active", created_at: {$gte: ...}}).sort({priority: -1})
// Wrong:   { created_at: 1, status: 1, priority: -1 }
// Correct: { status: 1, priority: -1, created_at: 1 }
//           E              S            R
```

## Index Types

| Type | Spec | Use |
|------|------|-----|
| Ascending | `field:1` | Range queries, sorts |
| Descending | `field:-1` | Reverse sorts |
| Multikey | `field:1` (auto on arrays) | Array element matching |
| Text | `field:text` | `$text` search (one per coll) |
| 2dsphere | `field:2dsphere` | Geo queries |
| Hashed | `field:hashed` | Sharding key, equality only |
| Wildcard | `'$**':1` (file-based) | Unknown query patterns |

This skill's `safe_index_create.py` accepts `1`, `-1`, `text`, `2dsphere`, `2d`, `hashed`, `geoHaystack`. For wildcard or partial indexes, use `--file <json>`.

## Don't-Index Rules

Skip an index when:
- Collection has < 10K documents (collscan is fine)
- Field has < 5 distinct values (low selectivity)
- Field is rarely filtered AND not used for sort
- Existing compound index already covers the query (verify w/ `db.coll.find(q).explain()`)
- Write throughput is the bottleneck, not read latency

## Cost of Each Index

- **Storage** — index size grows w/ collection size
- **Write amplification** — every insert/update/delete writes to ALL indexes
- **Build time** — large collections can take hours; impacts cluster
- **Memory** — working set must fit in RAM for fast access

Rule of thumb: 5–10 indexes per high-traffic collection is usually plenty.

## Safe Index Creation Checklist

Before running `safe_index_create.py --confirm`:

- [ ] Confirmed query pattern via `slow_queries.py` (not just trusting advisor)
- [ ] Checked existing indexes: `atlas clusters indexes describe ...`
- [ ] Estimated write-rate impact
- [ ] Ordered fields per ESR
- [ ] Picked an index name that's stable across env (avoid auto-generated where possible)
- [ ] Have rollback plan (drop manually in UI if needed)
- [ ] Off-peak window if collection is large

## Atlas Rolling Builds

`atlas clusters indexes create` triggers a **rolling index build** by default — one node at a time. This:
- Reduces resiliency briefly (one less replica during build)
- Takes longer than foreground builds
- Is non-blocking to writes

Avoid creating multiple indexes simultaneously on the same cluster.

## Examples

### Single-field

```bash
python3 scripts/safe_index_create.py \
  --cluster Cluster0 --db shop --collection products \
  --key sku:1 --name sku_unique \
  --confirm
```

### Compound, w/ ESR ordering

```bash
# Query: orders.find({customer_id: x, status: "open"}).sort({created_at: -1})
python3 scripts/safe_index_create.py \
  --cluster Cluster0 --db shop --collection orders \
  --key customer_id:1 --key status:1 --key created_at:-1 \
  --name customer_status_created \
  --confirm
```

### Sparse (only documents w/ field)

```bash
python3 scripts/safe_index_create.py \
  --cluster Cluster0 --db shop --collection users \
  --key referral_code:1 --sparse \
  --confirm
```

### Geospatial

```bash
python3 scripts/safe_index_create.py \
  --cluster Cluster0 --db delivery --collection drivers \
  --key location:2dsphere \
  --confirm
```

## Verifying After Build

```bash
# List indexes on a collection (read-only)
atlas clusters indexes describe \
  --clusterName Cluster0 \
  --db shop --collection orders

# Re-audit to confirm slow queries dropped
python3 scripts/performance_audit.py --cluster Cluster0
```

## Sources

- https://www.mongodb.com/docs/manual/core/index-compound/
- https://www.mongodb.com/docs/manual/applications/indexes/
- https://www.mongodb.com/blog/post/performance-best-practices-indexing
