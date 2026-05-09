# Atlas Search & Vector Search

When to add a search index, what shape it should take, and how this skill helps.

## When You Need Atlas Search (vs. a regular index)

Use Atlas Search when:
- **Case-insensitive text matching** — `$regex /name/i` doesn't use indexes; Atlas Search does.
- **Fuzzy / partial / autocomplete** — typo tolerance, partial-word match, prefix search.
- **Multi-field full-text** — query spans many fields w/ relevance ranking.
- **Faceted search** — group results by tags/categories w/ counts.

Use a regular b-tree index when:
- Exact equality, range, or sort.
- Compound query w/ predictable shape & cardinality.

The Performance Advisor will say `OPTIMIZE_CASE_INSENSITIVE_REGEX_QUERIES` when it detects regex traffic — that's its hint that Atlas Search is the better tool.

## When to Use Vector Search

For semantic similarity (AI / RAG / "find docs like this one"). Each doc has an embedding (a list of floats); Vector Search finds nearest neighbors by cosine / euclidean / dot product.

Common embedding models & dimensions:
| Model | Dimensions |
|---|---:|
| OpenAI `text-embedding-3-small` | 1536 |
| OpenAI `text-embedding-3-large` | 3072 |
| Cohere `embed-english-v3.0` | 1024 |
| Voyage `voyage-3` | 1024 |
| Sentence-Transformers `all-MiniLM-L6-v2` | 384 |

The `--init-template vector` output uses `numDimensions: 1536` as the default; adjust to your model.

## Search Index Definition Anatomy

A minimal text-search index:

```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "name": { "type": "string", "analyzer": "lucene.standard" },
      "description": { "type": "string", "analyzer": "lucene.standard" }
    }
  }
}
```

Tradeoffs:

| Field | What it does | When to use |
|---|---|---|
| `dynamic: true` | Index every field automatically | Fast prototyping; wastes storage |
| `dynamic: false` | Only fields you list | Production; smaller, faster |
| `analyzer: lucene.standard` | Default tokenizer + lowercase | Most general-purpose text |
| `analyzer: lucene.keyword` | Treat field as one token | Exact-match w/ case-insensitive |
| `analyzer: lucene.english` | English stemming, stopwords removed | English content w/ semantic match |
| `type: autocomplete` | Builds an autocomplete index | Typeahead UIs |
| `type: token` | Faceting | Filters / categories |

Vector index definition:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "category"
    }
  ]
}
```

`similarity` ∈ {`cosine`, `euclidean`, `dotProduct`}. Use `cosine` for normalized embeddings (most LLM models).

## Querying

Atlas Search:

```javascript
// Text search w/ scoring
db.hotels.aggregate([
  { $search: {
      index: "hotels_text",
      text: { query: "boutique resort", path: ["name", "description"] }
  }},
  { $project: { name: 1, score: { $meta: "searchScore" } } },
  { $limit: 10 }
]);
```

Vector search:

```javascript
db.docs.aggregate([
  { $vectorSearch: {
      index: "doc_embeddings",
      path: "embedding",
      queryVector: <embedding from your model — 1536 floats>,
      numCandidates: 100,
      limit: 5
  }}
]);
```

## This Skill's Coverage

| Op | Script | Notes |
|---|---|---|
| List search indexes | `atlas_search_list.py` | Read-only |
| Create search/vector index | `atlas_search_create.py` | Gated, dry-run by default |
| Delete search index | — | **REFUSED** — not in skill scope |
| Update search index | — | Use Atlas UI; updates are essentially drop+recreate |

## Common Gotchas

1. **Build is async** — index status starts at `BUILDING` and reaches `READY` in minutes. Don't query before READY.
2. **Source field changes don't auto-rebuild** — if you change a doc's analyzer-relevant field, the search index updates incrementally.
3. **Search is on M10+** only (not free or shared tiers).
4. **Vector dimensions must match** — mismatching `numDimensions` between index and query vector returns errors.
5. **`$search` must be FIRST stage** — can't be combined w/ `$match` before it (use `compound.filter` w/ Search instead).

## Sources

- https://www.mongodb.com/docs/atlas/atlas-search/
- https://www.mongodb.com/docs/atlas/atlas-vector-search/
- https://www.mongodb.com/docs/atlas/cli/current/command/atlas-clusters-search-indexes-list/
