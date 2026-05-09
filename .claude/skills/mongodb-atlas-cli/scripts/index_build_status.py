#!/usr/bin/env python3
"""Check the status of an in-progress index build.

Read-only. Uses mongosh `db.currentOp()` to find rolling index builds.

After `safe_index_create.py --confirm` returns, the build runs async. Use this
to poll progress.

Usage:
  python3 index_build_status.py --db myapp --collection orders
  python3 index_build_status.py --db myapp                          # all builds in db
  python3 index_build_status.py --db admin --all                            # all builds, all dbs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _mongo import MongoshError, mongosh_eval, validate_identifier  # noqa: E402


def fetch_build_status(
    db: str, coll: str | None, all_dbs: bool,
    conn: str | None, user: str | None, pw: str | None,
) -> list[dict]:
    validate_identifier(db, "database")
    if coll:
        validate_identifier(coll, "collection")

    # Filter conditions
    filters = ['"command.createIndexes": { $exists: true }']
    if not all_dbs:
        filters.append(f'"ns": {{ $regex: "^{db}\\\\.[^.]+$" }}')
    if coll:
        filters.append(f'"ns": "{db}.{coll}"')
    filter_js = "{ $or: [ { " + " }, { ".join(filters) + " } ] }"

    js = """
        const ops = db.currentOp({ "$or": [
            { "command.createIndexes": { $exists: true } },
            { "msg": { $regex: "Index Build" } }
        ]});
        return (ops.inprog || []).map(o => ({
            opid: o.opid,
            ns: o.ns,
            command: o.command,
            msg: o.msg,
            secs_running: o.secs_running,
            progress: o.progress
        }));
    """
    return mongosh_eval(js, connection_string=conn, username=user, password=pw, db="admin") or []


def summarize(ops: list[dict], db: str, coll: str | None) -> str:
    # Filter client-side too in case server filter was overly broad
    filtered = []
    for op in ops:
        ns = op.get("ns", "")
        if coll and ns != f"{db}.{coll}":
            continue
        if not coll and not ns.startswith(f"{db}."):
            continue
        filtered.append(op)

    if not filtered:
        return f"No index builds in progress for {db}{f'.{coll}' if coll else ''}."

    lines = [f"In-progress index builds: {len(filtered)}\n"]
    for op in filtered:
        ns = op.get("ns", "?")
        secs = op.get("secs_running", "?")
        progress = op.get("progress") or {}
        cmd = op.get("command") or {}
        idx_names = cmd.get("indexes", [])
        if isinstance(idx_names, list):
            idx_names = [i.get("name") for i in idx_names if isinstance(i, dict)]
        lines.append(f"  • {ns}")
        lines.append(f"      indexes: {', '.join(filter(None, idx_names)) or '?'}")
        lines.append(f"      running: {secs}s")
        if progress:
            done = progress.get("done", "?")
            total = progress.get("total", "?")
            lines.append(f"      progress: {done} / {total}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Show in-progress index builds")
    parser.add_argument("--db", required=True)
    parser.add_argument("--collection")
    parser.add_argument("--all", action="store_true", help="Search all databases (ignores --db filter for matching)")
    parser.add_argument("--connection-string", dest="connection_string")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        ops = fetch_build_status(args.db, args.collection, args.all,
                                 args.connection_string, args.username, args.password)
    except MongoshError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(ops, indent=2, default=str))
    else:
        print(f"\n=== Index Build Status — {args.db}{f'.{args.collection}' if args.collection else ''} ===\n",
              file=sys.stderr)
        print(summarize(ops, args.db, args.collection), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
