# Index Types — Complete Reference

Every index type MongoDB supports, when to use it, and how this skill creates it.

## 1. Single-field index (b-tree)

The simplest index. One field, ascending or descending.

```bash
python3 safe_index_create.py --cluster X --db app --collection users \
  --key email:1 --confirm
```

mongosh equivalent:
```javascript
db.users.createIndex({ email: 1 });
```

**Use when:** filtering or sorting on a single field. Direction (`1` vs `-1`) doesn't matter for equality, but matters for sort.

## 2. Compound index

Multiple fields. Order matters — follow the **ESR rule**: Equality fields → Sort fields → Range fields.

```bash
python3 safe_index_create.py --cluster X --db app --collection orders \
  --key user_id:1 --key status:1 --key created_at:-1 --confirm
```

**ESR example:**

```javascript
// Query: find({ user_id: X, status: "open" }).sort({ created_at: -1 })
//
// E (equality): user_id, status   → asc (direction irrelevant for equality)
// S (sort):     created_at         → -1 to match query sort
// R (range):    none here
//
// Index: { user_id: 1, status: 1, created_at: -1 }
```

A compound index can serve any **prefix** of its fields. `{a:1, b:1, c:1}` covers `find({a})`, `find({a, b})`, `find({a, b, c})` but **not** `find({b})` or `find({c})`.

## 3. Multikey index

Auto-created when an index field is an **array**. No special syntax — just create a normal index on an array field.

```javascript
db.users.insertOne({ name: "alice", tags: ["admin", "active"] });
db.users.createIndex({ tags: 1 });  // becomes multikey
db.users.find({ tags: "admin" });   // matches doc above
```

**Limitation:** can't have a compound multikey index where **two** fields are arrays. MongoDB will reject it.

## 4. Text index

Built-in full-text search. Supports `$text` queries with stemming, stopwords, and language-specific tokenization.

```bash
python3 safe_index_create.py --cluster X --db app --collection products \
  --key name:text --confirm
```

```javascript
// Query
db.products.find({ $text: { $search: "wireless headphones" } });
```

**One per collection.** Compound text+other-field is allowed: `{name:"text", category:1}`.

**For modern apps, prefer Atlas Search** — better tokenization, fuzzy match, scoring, faceting. See `atlas-search.md`.

## 5. 2dsphere (geospatial)

Spherical geometry — for lat/long pairs, polygons, etc.

```bash
python3 safe_index_create.py --cluster X --db delivery --collection drivers \
  --key location:2dsphere --confirm
```

Document shape:
```javascript
{ name: "Driver A", location: { type: "Point", coordinates: [-73.97, 40.77] } }
```

Query:
```javascript
db.drivers.find({
  location: {
    $near: {
      $geometry: { type: "Point", coordinates: [-73.97, 40.77] },
      $maxDistance: 5000  // meters
    }
  }
});
```

## 6. 2d (legacy planar)

Flat geometry — only use for legacy data. Prefer `2dsphere` for new code.

## 7. Hashed index

For **sharding** by a key. Hashed indexes give uniform distribution but only support equality (no range / sort).

```bash
python3 safe_index_create.py --cluster X --db app --collection events \
  --key user_id:hashed --confirm
```

```javascript
// Sharded collection w/ hashed shard key
sh.shardCollection("app.events", { user_id: "hashed" });
```

## 8. TTL index (time-to-live)

Auto-delete docs after N seconds past the indexed date field. Common for sessions, logs, caches.

```bash
python3 safe_index_create.py --cluster X --db app --collection sessions \
  --key created_at:1 --ttl-seconds 86400 --name sessions_24h --confirm
```

mongosh equivalent:
```javascript
db.sessions.createIndex({ created_at: 1 }, { expireAfterSeconds: 86400 });
```

**Caveats:**
- Only works on top-level `Date` fields (not strings).
- Deletion runs every 60 seconds — not real-time.
- Use `expireAfterSeconds: 0` w/ a future-dated field for "expire at this exact time" patterns.

## 9. Sparse index

Only includes docs where the indexed field **exists**. Saves space when most docs don't have the field.

```bash
python3 safe_index_create.py --cluster X --db app --collection users \
  --key referral_code:1 --sparse --confirm
```

**Limitation:** queries on the sparse field can use the index, but `{$ne: null}` queries may not. For more precision, use **partial** instead.

## 10. Partial index

Like sparse but more precise — index only docs matching a filter expression. **Strongly preferred over sparse** for most cases.

```bash
echo '{"deleted": false}' > /tmp/pf.json
python3 safe_index_create.py --cluster X --db app --collection users \
  --key email:1 --partial-filter /tmp/pf.json --confirm
```

mongosh equivalent:
```javascript
db.users.createIndex(
  { email: 1 },
  { partialFilterExpression: { deleted: false } }
);
```

**The query MUST include the filter clause** to use the partial index.

## 11. Unique index

Enforces uniqueness across docs. The skill validates this is intentional via the explicit `--unique` flag.

```bash
python3 safe_index_create.py --cluster X --db app --collection users \
  --key email:1 --unique --name email_unique --confirm
```

**Caveat:** if existing docs violate uniqueness, the build fails. Pre-clean duplicates first.

You can combine **unique + partial** to enforce uniqueness only over a subset:
```javascript
db.users.createIndex(
  { email: 1 },
  { unique: true, partialFilterExpression: { deleted: false } }
);
// Allows multiple deleted users w/ same email, enforces unique among non-deleted
```

## 12. Wildcard index

Index every field (or every field matching a path pattern). Useful for **unknown query shapes**.

```javascript
// Index every field in every doc
db.products.createIndex({ "$**": 1 });

// Index every field under attributes.*
db.products.createIndex({ "attributes.$**": 1 });
```

Via this skill — build a JSON file then pass via `--file`:

```bash
cat > /tmp/wildcard.json <<'EOF'
{
  "db": "shop",
  "collection": "products",
  "keys": [{"$**": 1}],
  "options": {"name": "wildcard_attrs"}
}
EOF

python3 safe_index_create.py --cluster X --file /tmp/wildcard.json --confirm
```

**Caveat:** larger and slower than targeted indexes. Use only when query shapes are genuinely unknown (e.g. user-defined filter UIs).

## 13. Atlas Search index

Full-text search on Atlas Cloud, way more powerful than the built-in `text` index. See `atlas-search.md`.

```bash
python3 atlas_search_create.py --init-template search > /tmp/s.json
# edit /tmp/s.json
python3 atlas_search_create.py --cluster X --db app --collection hotels \
  --name hotels_text --file /tmp/s.json --confirm
```

## 14. Atlas Vector Search index

For semantic similarity (RAG, AI). Cosine / euclidean / dot-product over float-array fields.

```bash
python3 atlas_search_create.py --init-template vector > /tmp/v.json
# edit numDimensions to match your embedding model
python3 atlas_search_create.py --cluster X --db app --collection docs \
  --name doc_vec --file /tmp/v.json --type vectorSearch --confirm
```

## Comparison Table

| Type | Storage | Write cost | Query types | Atlas-only? |
|---|---|---|---|---|
| Single-field | low | low | eq, range, sort | no |
| Compound (N fields) | medium | medium-high | prefix queries | no |
| Multikey (array) | high | high | array element match | no |
| Text | medium | low | `$text` w/ stemming | no |
| 2dsphere | medium | low | geo near, within, intersect | no |
| Hashed | medium | low | equality (sharding) | no |
| TTL | low | low | eq + auto-expire | no |
| Sparse | low | low | exists | no |
| Partial | low | low | matches filter expression | no |
| Unique | low | high* | uniqueness enforcement | no |
| Wildcard | high | high | unknown shapes | no |
| Atlas Search | medium | low | full-text, fuzzy, faceted | **yes** |
| Vector Search | high | medium | semantic similarity | **yes** |

*write cost on unique = uniqueness check on every insert/update

## Combining Modifiers

Many can be combined:
- unique + partial: enforce uniqueness on a subset
- TTL + partial: auto-delete only some docs
- compound + sparse: compound where leading field exists
- compound + unique: enforce uniqueness across a tuple

`safe_index_create.py` supports any combination via its flags + `--partial-filter` JSON.

## Common Pitfalls

1. **`{a:1, b:1}` doesn't help `find({b: x})`** — only the leading prefix is useful.
2. **Direction matters for sort, not equality** — `{a:1}` and `{a:-1}` perform identically for `find({a: x})`, but only the matching one helps `.sort({a: 1})` (vs sort:-1).
3. **Multikey + sort doesn't always work** — multikey indexes can't always serve sort if the array is being expanded. Test w/ `.explain()`.
4. **Index size matters for memory** — Atlas tracks `indexSize`. If indexes don't fit in RAM, perf degrades. `list_indexes.py` shows per-index size.
5. **Adding indexes always slows writes** — every insert/update/delete writes to all indexes. The drop-hints script flags ones not paying their write cost.
