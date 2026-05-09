# Local MongoDB vs. Atlas Cloud — What This Skill Can Touch

The `atlas` CLI talks to **Atlas Cloud** (mongodb.com) over the Admin API. It has no concept of a self-hosted mongod. `mongosh` talks to **any** mongod over the wire protocol, so it works against both.

## Feature Matrix

| Feature | Local mongo (Docker / self-host) | Atlas Free (M0) | Atlas Shared (M2/M5) | Atlas Dedicated (M10+) | Skill script |
|---|---|---|---|---|---|
| **Index management (CRUD)** | ✅ via mongosh | ✅ | ✅ | ✅ | `safe_index_create.py` (Atlas API), mongosh for local |
| **`$indexStats` access counts** | ✅ via mongosh | ✅ | ✅ | ✅ | `list_indexes.py` |
| **Query `.explain()`** | ✅ via mongosh | ✅ | ✅ | ✅ | `explain_query.py` |
| **Database profiler** | ✅ | ❌ disabled | ❌ disabled | ✅ | `profiler_status.py` |
| **Performance Advisor (slow queries, suggested indexes)** | ❌ doesn't exist | ❌ | ❌ | ✅ | `slow_queries.py`, `suggest_indexes.py` |
| **Performance Advisor (schema advice)** | ❌ | ❌ | ❌ | ✅ | `schema_advice.py` |
| **Performance Advisor (drop hints)** | ❌ | ❌ | ❌ | ✅ | `drop_index_hints.py` |
| **Cluster process metrics (CPU/mem/conn/op counters)** | use `serverStatus()` | ❌ admin metrics | ❌ admin metrics | ✅ | `cluster_health.py` |
| **Cloud backup snapshots** | use `mongodump`/manual | ❌ | ❌ | ✅ | `backup_status.py` |
| **Atlas Alerts** | ❌ | ✅ | ✅ | ✅ | `alerts.py` |
| **Atlas Search (full-text)** | ❌ unless using `mongodb/mongodb-atlas-local` | ✅ | ✅ | ✅ | `atlas_search_list.py`, `atlas_search_create.py` |
| **Atlas Vector Search** | ❌ unless using `mongodb/mongodb-atlas-local` | ✅ | ✅ | ✅ | `atlas_search_create.py --type vectorSearch` |
| **Atlas Stream Processing** | ❌ | ❌ | ❌ | ✅ via Atlas Streams Workspaces | not in skill |
| **Time-series collections** | ✅ from MongoDB 5.0+ | ✅ | ✅ | ✅ | not in skill (use mongosh) |
| **Change streams** | ✅ replica sets only | ✅ | ✅ | ✅ | not in skill (app-side concern) |
| **Sharding** | manual setup | ❌ no sharding | ❌ | M30+ only | not in skill |
| **Encryption at rest** | manual | ✅ | ✅ | ✅ | not exposed by skill (read via clusters describe) |
| **Field-level encryption (CSFLE / queryable encryption)** | ✅ | ✅ | ✅ | ✅ | app-side; not in skill |
| **TTL indexes** | ✅ | ✅ | ✅ | ✅ | `safe_index_create.py --ttl-seconds` |
| **Geospatial (`2dsphere`)** | ✅ | ✅ | ✅ | ✅ | `safe_index_create.py --key field:2dsphere` |
| **Wildcard indexes** | ✅ | ✅ | ✅ | ✅ | use `--file` w/ `safe_index_create.py` |
| **Hashed indexes (sharding)** | ✅ | ✅ | ✅ | ✅ | `safe_index_create.py --key field:hashed` |
| **Partial indexes** | ✅ | ✅ | ✅ | ✅ | `safe_index_create.py --partial-filter` |
| **Sparse indexes** | ✅ | ✅ | ✅ | ✅ | `safe_index_create.py --sparse` |
| **Unique indexes** | ✅ | ✅ | ✅ | ✅ | `safe_index_create.py --unique` |

## What This Skill Does NOT Touch (by design)

- **Cluster lifecycle** — create, modify, delete, pause, terminate clusters
- **Database users / auth** — create, update, delete dbusers
- **Network access** — peering, IP allowlists, private endpoints
- **Backup restore** — restoring snapshots can overwrite data
- **Index drops** — even when advisor recommends them. Drop manually w/ verification.
- **Federated DBs / data lakes** — Atlas Data Federation is out of scope
- **Sharding admin** — adding/removing shards
- **Org/project management** — create, delete projects/orgs

These are blocked by the skill's destructive-op guard. Run them manually in Atlas UI or `atlas` CLI directly if you genuinely need to.

## "I'm running locally — which scripts work?"

| Script | Works on local mongo? |
|---|---|
| `validate_env.py` | ⚠️  Validates Atlas auth — irrelevant for pure-local |
| `performance_audit.py` | ❌ Atlas-only |
| `suggest_indexes.py` | ❌ Atlas-only |
| `slow_queries.py` | ❌ Atlas-only (read your local profiler instead) |
| `schema_advice.py` | ❌ Atlas-only |
| `drop_index_hints.py` | ❌ Atlas-only |
| `cluster_health.py` | ❌ Atlas-only |
| `backup_status.py` | ❌ Atlas-only |
| `alerts.py` | ❌ Atlas-only |
| `atlas_search_list.py` | ⚠️  Only if using `mongodb/mongodb-atlas-local` |
| `atlas_search_create.py` | ⚠️  Only if using `mongodb/mongodb-atlas-local` |
| `safe_index_create.py` | ❌ Uses Atlas API — for local, use `--print-mongosh` flag for the equivalent shell command |
| `audit_diff.py` | ✅ Pure local file diff |
| `list_indexes.py` | ✅ mongosh — works on local |
| `explain_query.py` | ✅ mongosh — works on local |
| `profiler_status.py` | ✅ mongosh — works on local |

## Local Equivalents for Atlas-Only Features

If you want similar insights against a self-hosted mongod, use mongosh directly:

```javascript
// Slow queries → enable the profiler
use("yourdb");
db.setProfilingLevel(1, { slowms: 100 });   // captures ops > 100ms
db.system.profile.find({}).sort({ts: -1}).limit(10);

// "Suggested indexes" replacement → run explain on your real queries
db.collection.find(<typical query>).explain("executionStats");
// Look for COLLSCAN or high docsExamined/nReturned ratio

// "Drop hints" replacement → check $indexStats over a long window
db.collection.aggregate([{ $indexStats: {} }]).toArray();
// Indexes w/ accessCount=0 and small ratio are drop candidates

// "Schema advice" replacement → manual review w/ Compass / Studio 3T
// Look for: avg doc size > 200KB, unbounded arrays, > 30 indexes per coll

// Server health → serverStatus
db.serverStatus().connections;     // current/available
db.serverStatus().opcounters;      // q/i/u/d totals
db.serverStatus().mem;             // resident MB
```

## When To Use Atlas Local

The Docker image `mongodb/mongodb-atlas-local` gives you Atlas Search + Vector Search **without** a cloud account — useful for dev/CI. Setup:

```bash
docker run -d --name atlas-local -p 27017:27017 mongodb/mongodb-atlas-local

# Then `atlas` CLI's deployments subcommand can manage it:
atlas deployments connect atlas-local
atlas deployments search indexes create ...
```

Note: this is **not** a replacement for Atlas Cloud Performance Advisor. The advisor only exists in real Atlas.
