#!/usr/bin/env python3
"""Explain a query — wraps `db.coll.find(...).explain()` via mongosh.

Read-only. Useful before adding/dropping indexes — confirm what plan the query
actually uses today.

Usage:
  # find query
  python3 explain_query.py --db myapp --collection orders \\
      --filter '{"hotel_id": "123"}'

  # find w/ projection & sort
  python3 explain_query.py --db myapp --collection orders \\
      --filter '{"status": "paid"}' \\
      --sort '{"created_at": -1}' --limit 20

  # aggregate pipeline
  python3 explain_query.py --db myapp --collection orders \\
      --pipeline '[{"$match": {"customer_id": "123"}}, {"$group": {"_id": "$status"}}]'

  # explain mode
  python3 explain_query.py --... --mode allPlansExecution
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _mongo import MongoshError, mongosh_eval, validate_identifier  # noqa: E402


VALID_MODES = {"queryPlanner", "executionStats", "allPlansExecution"}


def explain_find(
    db: str, coll: str, filt: str, sort: str | None, projection: str | None,
    limit: int | None, mode: str, conn: str | None, user: str | None, pw: str | None,
) -> dict:
    validate_identifier(db, "database")
    validate_identifier(coll, "collection")
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {VALID_MODES}")
    coll_q = json.dumps(coll)
    parts = [f"db.getCollection({coll_q}).find({filt}"]
    if projection:
        parts.append(f", {projection}")
    parts.append(")")
    chain = "".join(parts)
    if sort:
        chain += f".sort({sort})"
    if limit:
        chain += f".limit({int(limit)})"
    js = f"return {chain}.explain({json.dumps(mode)});"
    return mongosh_eval(js, connection_string=conn, username=user, password=pw, db=db)


def explain_aggregate(
    db: str, coll: str, pipeline: str, mode: str,
    conn: str | None, user: str | None, pw: str | None,
) -> dict:
    validate_identifier(db, "database")
    validate_identifier(coll, "collection")
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {VALID_MODES}")
    coll_q = json.dumps(coll)
    js = f"return db.getCollection({coll_q}).explain({json.dumps(mode)}).aggregate({pipeline});"
    return mongosh_eval(js, connection_string=conn, username=user, password=pw, db=db)


def summarize(explain_out: dict) -> str:
    lines = []
    qp = explain_out.get("queryPlanner", {})
    es = explain_out.get("executionStats", {})

    # The aggregate explain has a different shape (stages array)
    stages = explain_out.get("stages")
    if isinstance(stages, list) and stages:
        lines.append("=== Aggregate pipeline plan ===")
        for i, st in enumerate(stages):
            stage_keys = list(st.keys())
            lines.append(f"  Stage {i+1}: {', '.join(stage_keys)}")
        return "\n".join(lines)

    # find() explain
    winning = qp.get("winningPlan", {})
    rejected = qp.get("rejectedPlans", [])
    lines.append(f"=== Winning plan ===")
    lines.append(f"  stage: {winning.get('stage', '?')}")
    inner = winning.get("inputStage") or winning
    while isinstance(inner, dict) and inner.get("inputStage"):
        inner = inner["inputStage"]
    if isinstance(inner, dict):
        if inner.get("indexName"):
            lines.append(f"  index: {inner.get('indexName')}")
            lines.append(f"  keyPattern: {json.dumps(inner.get('keyPattern', {}))}")
        elif inner.get("stage") == "COLLSCAN":
            lines.append("  ⚠️  COLLSCAN — no index used")
    lines.append(f"  rejected plans: {len(rejected)}")

    # Execution stats
    if es:
        lines.append(f"\n=== Execution stats ===")
        lines.append(f"  executionSuccess:    {es.get('executionSuccess')}")
        lines.append(f"  executionTimeMillis: {es.get('executionTimeMillis')}")
        lines.append(f"  totalKeysExamined:   {es.get('totalKeysExamined')}")
        lines.append(f"  totalDocsExamined:   {es.get('totalDocsExamined')}")
        lines.append(f"  nReturned:           {es.get('nReturned')}")
        nreturned = es.get('nReturned') or 0
        examined = es.get('totalDocsExamined') or 0
        if nreturned and examined:
            ratio = examined / nreturned
            flag = " ⚠️" if ratio > 100 else ""
            lines.append(f"  examined/returned:   {ratio:.1f}×{flag}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain a query — find or aggregate")
    parser.add_argument("--db", required=True)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--filter", help="Find filter as JSON, e.g. '{\"name\": \"alice\"}'")
    parser.add_argument("--projection", help="Projection as JSON")
    parser.add_argument("--sort", help="Sort as JSON")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--pipeline", help="Aggregate pipeline as JSON array")
    parser.add_argument("--mode", default="executionStats",
                        choices=["queryPlanner", "executionStats", "allPlansExecution"])
    parser.add_argument("--connection-string", dest="connection_string")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.filter and not args.pipeline:
        print("ERROR: pass --filter (for find) or --pipeline (for aggregate)", file=sys.stderr)
        return 1
    if args.filter and args.pipeline:
        print("ERROR: pass either --filter or --pipeline, not both", file=sys.stderr)
        return 1

    try:
        # Validate JSON args parse cleanly first
        if args.filter:
            json.loads(args.filter)
        if args.pipeline:
            pl = json.loads(args.pipeline)
            if not isinstance(pl, list):
                raise ValueError("--pipeline must be a JSON array")
        if args.sort:
            json.loads(args.sort)
        if args.projection:
            json.loads(args.projection)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: invalid JSON arg: {e}", file=sys.stderr)
        return 1

    try:
        if args.pipeline:
            result = explain_aggregate(args.db, args.collection, args.pipeline, args.mode,
                                       args.connection_string, args.username, args.password)
        else:
            result = explain_find(args.db, args.collection, args.filter, args.sort,
                                  args.projection, args.limit, args.mode,
                                  args.connection_string, args.username, args.password)
    except MongoshError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(summarize(result), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
