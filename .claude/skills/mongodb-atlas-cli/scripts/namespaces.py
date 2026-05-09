#!/usr/bin/env python3
"""List the hottest namespaces — collections experiencing slow queries.

Read-only. Wraps `atlas performanceAdvisor namespaces`.

Use this BEFORE drilling into slow_queries / suggest_indexes — gives the
"which collections deserve attention" overview.

Usage:
  python3 namespaces.py --cluster Cluster0
  python3 namespaces.py --cluster Cluster0 --since 1700000000 --duration 86400000
  python3 namespaces.py --cluster Cluster0 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, emit_human, primary_process, run_atlas  # noqa: E402


def fetch_namespaces(
    cluster: str, project_id: str | None, since: int | None, duration: int | None,
) -> list[dict]:
    process_name = primary_process(cluster, project_id)
    args = ["performanceAdvisor", "namespaces", "list", "--processName", process_name]
    if project_id:
        args += ["--projectId", project_id]
    if since:
        args += ["--since", str(since)]
    if duration:
        args += ["--duration", str(duration)]
    data = run_atlas(args)
    if isinstance(data, dict):
        return data.get("namespaces") or data.get("results") or []
    return data if isinstance(data, list) else []


def summarize(ns_list: list[dict]) -> str:
    if not ns_list:
        return "No hot namespaces in the requested window. Cluster may be quiet or perf is healthy."
    lines = [f"Hot namespaces (slow query namespaces): {len(ns_list)}\n"]
    for ns in ns_list[:30]:
        if isinstance(ns, dict):
            namespace = ns.get("namespace", ns.get("ns", "?"))
            ns_type = ns.get("type", "")
            lines.append(f"  • {namespace}" + (f"  ({ns_type})" if ns_type else ""))
        else:
            lines.append(f"  • {ns}")
    if len(ns_list) > 30:
        lines.append(f"  ... +{len(ns_list) - 30} more")
    lines.append("\nDrill into one:")
    lines.append("  python3 slow_queries.py --cluster <name> --namespace <db.coll>")
    lines.append("  python3 suggest_indexes.py --cluster <name> --namespace <db.coll>")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List hot namespaces from Performance Advisor")
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--since", type=int, help="Unix epoch seconds")
    parser.add_argument("--duration", type=int, help="Window length in milliseconds")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        ns_list = fetch_namespaces(args.cluster, args.project_id, args.since, args.duration)
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(ns_list, indent=2, default=str))
    else:
        emit_human("Hot Namespaces", summarize(ns_list))
    return 0


if __name__ == "__main__":
    sys.exit(main())
