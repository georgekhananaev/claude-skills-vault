#!/usr/bin/env python3
"""Pull slow query log lines from Performance Advisor for a cluster.

Read-only. Wraps `atlas performanceAdvisor slowQueryLogs list`.

Usage:
  python3 slow_queries.py --cluster Cluster0
  python3 slow_queries.py --cluster Cluster0 --hours 6
  python3 slow_queries.py --cluster Cluster0 --namespace app.users --hours 24
  python3 slow_queries.py --cluster Cluster0 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, emit_human, primary_process, run_atlas  # noqa: E402


def fetch_slow_queries(
    cluster: str,
    project_id: str | None,
    namespaces: list[str] | None,
    hours: int,
    n_log: int | None,
) -> list[dict]:
    process_name = primary_process(cluster, project_id)
    args = [
        "performanceAdvisor", "slowQueryLogs", "list",
        "--processName", process_name,
        "--duration", str(hours * 3600 * 1000),
    ]
    if project_id:
        args += ["--projectId", project_id]
    if namespaces:
        args += ["--namespaces", ",".join(namespaces)]
    if n_log:
        args += ["--nLog", str(n_log)]

    data = run_atlas(args)
    if isinstance(data, dict):
        return data.get("slowQueries", []) or data.get("results", []) or []
    return data if isinstance(data, list) else []


def summarize(queries: list[dict]) -> str:
    if not queries:
        return "No slow queries logged in the requested window."

    by_ns = Counter()
    by_op = Counter()
    total_ms = 0
    longest = []

    for q in queries:
        ns = q.get("namespace") or q.get("ns") or "?"
        by_ns[ns] += 1
        line = q.get("line", "") or json.dumps(q)
        # Coarse op detection from log line
        for op in ("find", "aggregate", "update", "count", "distinct", "getMore"):
            if f'"{op}"' in line or f' {op} ' in line:
                by_op[op] += 1
                break
        # Try to grab durationMillis
        dur = q.get("durationMillis") or q.get("durationMs") or 0
        if isinstance(dur, (int, float)):
            total_ms += int(dur)
            longest.append((int(dur), ns, line[:200]))

    longest.sort(reverse=True)

    lines = [
        f"Slow query log lines: {len(queries)}",
        f"Total time spent in slow ops: {total_ms / 1000:.1f}s",
        "",
        "Top namespaces by slow-query count:",
    ]
    for ns, cnt in by_ns.most_common(10):
        lines.append(f"  {cnt:>5}  {ns}")
    if by_op:
        lines.append("\nOp distribution:")
        for op, cnt in by_op.most_common():
            lines.append(f"  {cnt:>5}  {op}")
    if longest:
        lines.append("\nLongest 5 ops:")
        for dur, ns, snippet in longest[:5]:
            lines.append(f"  {dur:>6}ms  {ns}\n    {snippet}")
    lines.append("\nNext step: run `suggest_indexes.py --cluster <name> --namespace <ns>` for any hot namespace.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Get slow query logs from Performance Advisor")
    parser.add_argument("--cluster", required=True, help="Cluster name")
    parser.add_argument("--projectId", dest="project_id", help="24-hex project ID")
    parser.add_argument("--namespace", action="append", help="Filter by namespace (db.coll). Repeatable.")
    parser.add_argument("--hours", type=int, default=24, help="How far back to query (default: 24)")
    parser.add_argument("--nLog", type=int, dest="n_log", help="Max log lines (default 20000)")
    parser.add_argument("--json", action="store_true", help="JSON to stdout instead of summary")
    args = parser.parse_args()

    try:
        queries = fetch_slow_queries(
            cluster=args.cluster,
            project_id=args.project_id,
            namespaces=args.namespace,
            hours=args.hours,
            n_log=args.n_log,
        )
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(queries, indent=2))
    else:
        emit_human(f"Slow Queries (last {args.hours}h)", summarize(queries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
