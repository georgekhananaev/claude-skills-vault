#!/usr/bin/env python3
"""List Atlas Search & Vector Search indexes for a collection.

Read-only. Wraps `atlas clusters search indexes list`.

Useful when Performance Advisor recommends Atlas Search (e.g., for case-insensitive
regex queries).

Usage:
  python3 atlas_search_list.py --cluster Cluster0 --db myapp --collection products
  python3 atlas_search_list.py --cluster Cluster0 --db myapp --collection products --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, emit_human, resolve_project_id, run_atlas  # noqa: E402


def fetch_search_indexes(cluster: str, db: str, collection: str, project_id: str | None) -> list[dict]:
    args = [
        "clusters", "search", "indexes", "list",
        "--clusterName", cluster,
        "--db", db,
        "--collection", collection,
    ]
    pid = resolve_project_id(project_id)
    if pid:
        args += ["--projectId", pid]
    data = run_atlas(args)
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    # Atlas API may return either {"results": [...]} (paginated) or a bare
    # single-index document {"name": "...", ...} (older shape).
    results = data.get("results")
    if isinstance(results, list):
        return results
    if data.get("name"):
        return [data]
    return []


def summarize(indexes: list[dict], db: str, collection: str) -> str:
    if not indexes:
        return (
            f"No Atlas Search or Vector Search indexes on `{db}.{collection}`.\n"
            f"\nTo create one (gated, additive):\n"
            f"  python3 atlas_search_create.py --cluster <name> --db {db} --collection {collection} --type search ...\n"
        )
    lines = [f"Search indexes on `{db}.{collection}`: {len(indexes)}\n"]
    for idx in indexes:
        name = idx.get("name", "?")
        idx_type = idx.get("type", "search")
        status = idx.get("status", "?")
        idx_id = idx.get("indexID", idx.get("id", "?"))
        lines.append(f"  • {name} ({idx_type}, status={status})  id={idx_id}")
        defn = idx.get("definition") or idx.get("latestDefinition") or {}
        if defn:
            mappings = defn.get("mappings") or {}
            fields = mappings.get("fields") or {}
            if isinstance(fields, dict) and fields:
                lines.append(f"      indexed fields: {', '.join(list(fields.keys())[:8])}")
            elif idx_type == "vectorSearch":
                fields_list = defn.get("fields") or []
                vec_fields = [f.get("path") for f in fields_list if isinstance(f, dict) and f.get("type") == "vector"]
                if vec_fields:
                    lines.append(f"      vector fields: {', '.join(vec_fields)}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List Atlas Search & Vector Search indexes (read-only)")
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        idxs = fetch_search_indexes(args.cluster, args.db, args.collection, args.project_id)
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(idxs, indent=2, default=str))
    else:
        emit_human(f"Atlas Search Indexes — {args.db}.{args.collection}", summarize(idxs, args.db, args.collection))
    return 0


if __name__ == "__main__":
    sys.exit(main())
