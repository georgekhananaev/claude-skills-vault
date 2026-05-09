#!/usr/bin/env python3
"""Fetch Performance Advisor's suggested indexes for a cluster.

Read-only. Wraps `atlas performanceAdvisor suggestedIndexes list`.

Usage:
  python3 suggest_indexes.py --cluster Cluster0
  python3 suggest_indexes.py --cluster Cluster0 --namespace app.users
  python3 suggest_indexes.py --cluster Cluster0 --json    # pure JSON to stdout
  python3 suggest_indexes.py --cluster Cluster0 --since 1700000000 --duration 86400000

Output:
  - Pretty summary to stderr (ranked by impact)
  - JSON to stdout when --json flag set
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, emit_human, primary_process, run_atlas  # noqa: E402


def fetch_suggestions(
    cluster: str,
    project_id: str | None,
    namespaces: list[str] | None,
    n_indexes: int | None,
    n_examples: int | None,
    since: int | None,
    duration: int | None,
) -> list[dict]:
    process_name = primary_process(cluster, project_id)
    args = [
        "performanceAdvisor", "suggestedIndexes", "list",
        "--processName", process_name,
    ]
    if project_id:
        args += ["--projectId", project_id]
    if namespaces:
        args += ["--namespaces", ",".join(namespaces)]
    if n_indexes:
        args += ["--nIndexes", str(n_indexes)]
    if n_examples:
        args += ["--nExamples", str(n_examples)]
    if since:
        args += ["--since", str(since)]
    if duration:
        args += ["--duration", str(duration)]

    data = run_atlas(args)
    if isinstance(data, dict):
        return data.get("suggestedIndexes", []) or data.get("results", []) or []
    return data if isinstance(data, list) else []


def format_summary(suggestions: list[dict]) -> str:
    if not suggestions:
        return "No index suggestions returned. Cluster may be performing well, or there's not enough query history yet."
    lines = [f"Found {len(suggestions)} index suggestion(s):\n"]
    for i, s in enumerate(suggestions, 1):
        ns = s.get("namespace") or s.get("ns") or "?"
        weight = s.get("weight") or s.get("impact") or "?"
        keys = s.get("index") or s.get("keys") or []
        if isinstance(keys, list):
            key_str = ", ".join(
                f"{k.get('field', k)}: {k.get('direction', 1) if isinstance(k, dict) else 1}"
                for k in keys
            )
        elif isinstance(keys, dict):
            key_str = ", ".join(f"{k}: {v}" for k, v in keys.items())
        else:
            key_str = str(keys)
        examples = s.get("impact") or s.get("examples") or []
        ex_count = len(examples) if isinstance(examples, list) else 0
        lines.append(
            f"  [{i}] {ns}\n"
            f"      key:    {{ {key_str} }}\n"
            f"      weight: {weight}\n"
            f"      example queries: {ex_count}"
        )
    lines.append("\nTo create one of these, use:")
    lines.append("  python3 safe_index_create.py --cluster <name> --db <db> --collection <coll> --key field:1 [--key f2:1] --confirm")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Get Performance Advisor's suggested indexes")
    parser.add_argument("--cluster", required=True, help="Cluster name (from `atlas clusters list`)")
    parser.add_argument("--projectId", dest="project_id", help="24-hex project ID (overrides env)")
    parser.add_argument("--namespace", action="append", help="Filter by namespace (db.coll). Repeatable.")
    parser.add_argument("--nIndexes", type=int, dest="n_indexes", help="Max suggestions to return")
    parser.add_argument("--nExamples", type=int, dest="n_examples", help="Max example queries per suggestion")
    parser.add_argument("--since", type=int, help="Unix epoch seconds — start time")
    parser.add_argument("--duration", type=int, help="Window length in milliseconds")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout (default: human summary to stderr)")
    args = parser.parse_args()

    try:
        suggestions = fetch_suggestions(
            cluster=args.cluster,
            project_id=args.project_id,
            namespaces=args.namespace,
            n_indexes=args.n_indexes,
            n_examples=args.n_examples,
            since=args.since,
            duration=args.duration,
        )
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(suggestions, indent=2))
    else:
        emit_human("Suggested Indexes (Performance Advisor)", format_summary(suggestions))
    return 0


if __name__ == "__main__":
    sys.exit(main())
