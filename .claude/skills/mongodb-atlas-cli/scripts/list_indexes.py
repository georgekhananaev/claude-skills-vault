#!/usr/bin/env python3
"""List ALL indexes on a collection (or every collection in a database) w/ access stats.

Read-only. Uses mongosh + `$indexStats` for live access counts and `db.coll.stats()`
for size info. Complements drop_index_hints.py which uses the Atlas Performance
Advisor (sampled).

Usage:
  python3 list_indexes.py --db myapp --collection orders
  python3 list_indexes.py --db myapp  # every collection
  python3 list_indexes.py --db myapp --collection orders --json
  python3 list_indexes.py --connection-string "mongodb+srv://..." --username george --password ...

Env vars (alternative to flags):
  MONGODB_CONNECTION_STRING / ATLAS_CONNECTION_STRING / MONGODB_URI
  MONGODB_USERNAME
  MONGODB_PASSWORD
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _mongo import MongoshError, mongosh_eval, validate_identifier  # noqa: E402


def fetch_collection_indexes(
    db: str, coll: str, conn: str | None, user: str | None, pw: str | None
) -> list[dict]:
    validate_identifier(db, "database")
    validate_identifier(coll, "collection")
    coll_q = json.dumps(coll)
    js = f"""
        const __c = db.getCollection({coll_q});
        const idx = __c.getIndexes();
        const stats = __c.aggregate([{{$indexStats:{{}}}}]).toArray();
        const statByName = {{}};
        for (const s of stats) statByName[s.name] = s.accesses && s.accesses.ops != null ? Number(s.accesses.ops) : 0;
        let collStats = {{}};
        try {{ collStats = __c.stats({{indexDetails: true}}); }} catch(e) {{ collStats = {{}}; }}
        const idxSize = collStats.indexSizes || {{}};
        return idx.map(i => ({{
          name: i.name,
          key: i.key,
          unique: !!i.unique,
          sparse: !!i.sparse,
          partial: !!i.partialFilterExpression,
          ttl: i.expireAfterSeconds,
          accessCount: statByName[i.name] != null ? statByName[i.name] : null,
          sizeBytes: idxSize[i.name] != null ? Number(idxSize[i.name]) : null,
        }}));
    """
    return mongosh_eval(js, connection_string=conn, username=user, password=pw, db=db)


def fetch_collection_names(db: str, conn: str | None, user: str | None, pw: str | None) -> list[str]:
    validate_identifier(db, "database")
    js = "return db.getCollectionNames().sort();"
    return mongosh_eval(js, connection_string=conn, username=user, password=pw, db=db) or []


def render_indexes(db: str, coll: str, idxs: list[dict]) -> str:
    if not idxs:
        return f"  (no indexes — that's strange, _id_ should always exist)"
    lines = []
    for i in idxs:
        attrs = []
        if i.get("unique"): attrs.append("UNIQUE")
        if i.get("sparse"): attrs.append("SPARSE")
        if i.get("partial"): attrs.append("PARTIAL")
        if i.get("ttl") is not None: attrs.append(f"TTL={i.get('ttl')}s")
        attr_str = (" [" + " ".join(attrs) + "]") if attrs else ""
        access = i.get("accessCount")
        access_str = f"{access:,}" if isinstance(access, (int, float)) else "—"
        size = i.get("sizeBytes")
        size_str = f"{size/(1024*1024):.1f}MB" if isinstance(size, (int, float)) else "—"
        # Format key
        key = i.get("key") or {}
        key_str = ", ".join(f"{k}:{v}" for k, v in key.items())
        flag = ""
        if access == 0 and i.get("name") != "_id_":
            flag = "  ⚠️ unused"
        lines.append(f"  {i.get('name','?'):40s}  {{{ key_str }}}{attr_str}")
        lines.append(f"      access: {access_str:>15s}  size: {size_str:>10s}{flag}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List all indexes on a collection or DB w/ access stats")
    parser.add_argument("--db", required=True)
    parser.add_argument("--collection")
    parser.add_argument("--connection-string", dest="connection_string")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        if args.collection:
            idxs = fetch_collection_indexes(args.db, args.collection,
                                            args.connection_string, args.username, args.password)
            if args.json:
                print(json.dumps(idxs, indent=2, default=str))
            else:
                print(f"\n=== Indexes on {args.db}.{args.collection} ({len(idxs)}) ===\n", file=sys.stderr)
                print(render_indexes(args.db, args.collection, idxs), file=sys.stderr)
        else:
            colls = fetch_collection_names(args.db, args.connection_string, args.username, args.password)
            colls = [c for c in colls if not c.startswith("system.")]
            from concurrent.futures import ThreadPoolExecutor, as_completed
            results: dict[str, list[dict]] = {}
            with ThreadPoolExecutor(max_workers=min(6, len(colls) or 1)) as ex:
                futures = {
                    ex.submit(fetch_collection_indexes, args.db, c,
                              args.connection_string, args.username, args.password): c
                    for c in colls
                }
                for fut in as_completed(futures):
                    c = futures[fut]
                    try:
                        results[c] = fut.result()
                    except MongoshError as e:
                        print(f"WARN: failed for {c}: {e}", file=sys.stderr)
            if args.json:
                print(json.dumps(results, indent=2, default=str))
            else:
                total = sum(len(v) for v in results.values())
                print(f"\n=== Indexes across {args.db} — {len(results)} collections, {total} indexes ===\n", file=sys.stderr)
                for c, idxs in sorted(results.items()):
                    print(f"\n--- {c} ({len(idxs)} indexes) ---", file=sys.stderr)
                    print(render_indexes(args.db, c, idxs), file=sys.stderr)
    except MongoshError as e:
        print(str(e), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
