#!/usr/bin/env python3
"""Create an Atlas Search or Vector Search index — gated, dry-run by default.

Wraps `atlas clusters search indexes create`. Same safety pattern as
safe_index_create.py: dry-run by default, requires --confirm to execute,
hard-blocks destructive ops via shared guard.

Atlas Search index definition lives in a JSON file. Sample definitions for the
two common shapes are included as templates and printed in --init-template.

Usage (text search):
  python3 atlas_search_create.py --init-template search > search.json
  # edit search.json
  python3 atlas_search_create.py \\
    --cluster Cluster0 --db myapp --collection products \\
    --name products_text --file search.json
  # add --confirm to execute

Usage (vector search):
  python3 atlas_search_create.py --init-template vector > vec.json
  # edit vec.json (set field path & numDimensions)
  python3 atlas_search_create.py \\
    --cluster Cluster0 --db myapp --collection products \\
    --name products_vector --file vec.json --type vectorSearch --confirm
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, refuse_if_destructive, resolve_project_id, run_atlas  # noqa: E402


SEARCH_TEMPLATE = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "name": {"type": "string", "analyzer": "lucene.standard"},
            "description": {"type": "string", "analyzer": "lucene.standard"}
        }
    }
}

VECTOR_TEMPLATE = {
    "fields": [
        {
            "type": "vector",
            "path": "embedding",
            "numDimensions": 1536,
            "similarity": "cosine"
        }
    ]
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely create an Atlas Search or Vector Search index (dry-run by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--cluster", help="Cluster name")
    parser.add_argument("--db", help="Database name")
    parser.add_argument("--collection", help="Collection name")
    parser.add_argument("--name", help="Search index name")
    parser.add_argument("--file", help="Path to JSON definition")
    parser.add_argument("--type", choices=["search", "vectorSearch"], default="search",
                        help="Index type (default: search)")
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--confirm", action="store_true", help="EXECUTE (without this, dry-run only)")
    parser.add_argument("--init-template", choices=["search", "vector"],
                        help="Print a starter JSON definition to stdout and exit")
    args = parser.parse_args()

    if args.init_template:
        tmpl = SEARCH_TEMPLATE if args.init_template == "search" else VECTOR_TEMPLATE
        print(json.dumps(tmpl, indent=2))
        return 0

    # Validate required args (only when not in template mode)
    missing = [a for a in ("cluster", "db", "collection", "name", "file") if not getattr(args, a)]
    if missing:
        print(f"ERROR: missing required args: {', '.join('--' + m for m in missing)}", file=sys.stderr)
        return 1

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: definition file not found: {file_path}", file=sys.stderr)
        return 1

    try:
        defn = json.loads(file_path.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in {file_path}: {e}", file=sys.stderr)
        return 1

    cmd_args = [
        "clusters", "search", "indexes", "create",
        "--clusterName", args.cluster,
        "--db", args.db,
        "--collection", args.collection,
        "--file", str(file_path),
    ]
    if args.type == "vectorSearch":
        cmd_args += ["--type", "vectorSearch"]
    pid = resolve_project_id(args.project_id)
    if pid:
        cmd_args += ["--projectId", pid]
    if args.name:
        cmd_args += [args.name]

    try:
        refuse_if_destructive(cmd_args)
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    rendered = "atlas " + " ".join(shlex.quote(a) for a in cmd_args)
    print("Planned command:", file=sys.stderr)
    print(f"  {rendered}", file=sys.stderr)
    print(file=sys.stderr)
    print("Definition preview:", file=sys.stderr)
    print(json.dumps(defn, indent=2)[:1000], file=sys.stderr)
    print(file=sys.stderr)
    print("Pre-flight notes:", file=sys.stderr)
    print("  • Atlas builds search indexes asynchronously; status reaches READY in minutes.", file=sys.stderr)
    print("  • Vector search requires `numDimensions` matching your embedding model.", file=sys.stderr)
    print("  • This is ADDITIVE — won't drop or modify existing indexes.", file=sys.stderr)
    print("  • To roll back: drop manually in Atlas UI (this skill won't drop).", file=sys.stderr)

    if not args.confirm:
        print("\n[DRY RUN] Add --confirm to execute.", file=sys.stderr)
        return 0

    print("\nExecuting…", file=sys.stderr)
    try:
        result = run_atlas(cmd_args, json_out=False)
        print(result)
        print("\n✓ Search index creation submitted. Build runs asynchronously.", file=sys.stderr)
        print(f"  Check status: python3 atlas_search_list.py --cluster {args.cluster} --db {args.db} --collection {args.collection}",
              file=sys.stderr)
    except AtlasError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
