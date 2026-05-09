# mongosh Integration

A few scripts in this skill talk directly to your cluster via `mongosh` rather than the Atlas Admin API. This is necessary when:

- You need data the Admin API doesn't expose (e.g. live `$indexStats`, query explain plans, profiler state).
- You want exact, unsampled results — Performance Advisor samples its source data.

## Scripts that use mongosh

| Script | Why mongosh |
|---|---|
| `list_indexes.py` | `db.coll.getIndexes()` + `$indexStats` for live access counts |
| `explain_query.py` | `db.coll.find().explain()` — not in Admin API |
| `profiler_status.py` | `db.getProfilingStatus()` + `db.system.profile` |
| `safe_index_create.py` (pre-flight) | Probes existing indexes to warn on duplicates |

## Setup

### Install

```bash
brew install mongosh
# OR (already bundled w/ Atlas CLI)
brew install mongodb-atlas
```

### Credentials

Three env vars — set them once:

```bash
export MONGODB_CONNECTION_STRING="mongodb+srv://<host>.mongodb.net/?authSource=admin"
export MONGODB_USERNAME="<atlas-db-user>"
export MONGODB_PASSWORD="<password>"
```

Or pass per-invocation:

```bash
python3 list_indexes.py --db myapp \
  --connection-string "mongodb+srv://..." \
  --username george --password '...'
```

The `_mongo.py` helper reads these and passes user/password as **flags** (not in URL) — avoids URL-encoding issues w/ special characters and prevents the password from leaking into process listings.

### Get the connection string

```bash
atlas clusters describe <CLUSTER> --projectId <pid> -o json | jq -r '.connectionStrings.standardSrv'
```

### Get / create the user

The Atlas DB user is **separate** from the Atlas API key. Different surface entirely.

- **API key**: Atlas UI → Project Settings → Access Manager → API Keys. Used by `atlas` CLI commands (most of this skill).
- **DB user**: Atlas UI → Database Access → ADD NEW DATABASE USER. Used by mongosh / your app to connect to the actual database.

> ⚠️  Creating / updating DB users is **REFUSED** by this skill (`atlas dbusers create` is in the destructive list). Do it in the Atlas UI.

## Output Discipline

mongosh's output isn't pure JSON by default — it can include warnings, ANSI codes, and EJSON-formatted dates / ObjectIds. The `_mongo.py` helper:

1. Calls `mongosh --quiet` to suppress banners.
2. Wraps the user JS in `EJSON.stringify(__r, null, 0, { relaxed: true })` to produce a single JSON line.
3. Picks the **last JSON-shaped line** from stdout (in case warnings printed first).
4. Falls back to raw text if JSON parsing fails.

`relaxed: true` mode renders dates as `{"$date": "2026-05-09T..."}` and ObjectIds as `{"$oid": "..."}` — Python parses these as plain dicts, which is fine for our display purposes.

## Read-Only Discipline

The mongosh-based scripts in this skill are **read-only** by intent:

- `list_indexes.py` — only calls `getIndexes()`, `$indexStats`, `stats()`.
- `explain_query.py` — only calls `.explain()` (does not execute the query).
- `profiler_status.py` — only calls `getProfilingStatus()`, `find()` on `system.profile`.
- `safe_index_create.py` pre-flight — only calls `getIndexes()`.

There is no script in this skill that issues `db.coll.dropIndex(...)`, `db.coll.deleteMany(...)`, or any mutating mongosh op. **You** run those manually if needed (the playbook reports show you the exact commands).

## Troubleshooting

**`MongoServerError: Authentication failed`**
- Check user/password against Atlas UI → Database Access. Atlas DB users are case-sensitive.
- The user must have at least read on the target database. `clusterAdmin` works for `$indexStats`.

**`mongosh: command not found`**
- `brew install mongosh` (macOS) or download from https://www.mongodb.com/try/download/shell

**`MongoNetworkError: connection ... timed out`**
- Check Atlas IP allowlist (Atlas UI → Network Access). Add your current IP.
- Connection string must be the SRV form for replica-set discovery.

**`ECONNREFUSED ::1:27017`**
- You passed `localhost`, but mongosh isn't reaching Atlas. Use the SRV connection string from Atlas UI.

## Why Not Just Use the Admin API?

Two reasons:
1. **Performance Advisor is sampled** — it sees a subset of slow queries. `$indexStats` shows you actual access counts since stats reset (typically server restart).
2. **`.explain()` doesn't exist in the Admin API** — there's no way to ask "what would the planner do for this query?" without running it through the driver.

So mongosh complements, doesn't replace, the Admin-API scripts.
