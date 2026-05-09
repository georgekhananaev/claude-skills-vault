#!/usr/bin/env python3
"""Aggregate execution stats — by workflow, by status, error patterns.

Read-only.

Usage:
  python3 execution_stats.py                     # last 500 executions
  python3 execution_stats.py --limit 1000
  python3 execution_stats.py --workflow <id>    # for one workflow
  python3 execution_stats.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError  # noqa: E402


def fetch_executions(workflow_id: str | None, limit: int) -> list[dict]:
    from _api import list_paginated
    query = {"limit": min(limit, 250)}
    if workflow_id:
        query["workflowId"] = workflow_id
    return list_paginated("/api/v1/executions", query=query, max_pages=20)[:limit]


def compute_stats(items: list[dict]) -> dict:
    by_status = Counter()
    by_workflow = Counter()
    by_workflow_errors = Counter()
    durations_ms: list[int] = []
    error_messages = Counter()

    for e in items:
        status = e.get("status") or ("success" if e.get("finished") else "unknown")
        wfid = str(e.get("workflowId") or "?")
        by_status[status] += 1
        by_workflow[wfid] += 1
        if status == "error":
            by_workflow_errors[wfid] += 1
            # n8n exposes top-level error fields in some shapes
            err_msg = (e.get("data") or {}).get("resultData", {}).get("error", {}).get("message")
            if err_msg:
                error_messages[err_msg[:120]] += 1

        # Duration
        started = e.get("startedAt")
        stopped = e.get("stoppedAt")
        if started and stopped:
            try:
                from datetime import datetime
                t1 = datetime.fromisoformat(started.replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(stopped.replace("Z", "+00:00"))
                ms = int((t2 - t1).total_seconds() * 1000)
                if ms >= 0:
                    durations_ms.append(ms)
            except Exception:
                pass

    durations_ms.sort()
    n = len(durations_ms)
    p50 = durations_ms[n // 2] if n else None
    p95 = durations_ms[int(n * 0.95)] if n else None
    p99 = durations_ms[int(n * 0.99)] if n else None

    return {
        "total": len(items),
        "by_status": dict(by_status),
        "by_workflow_total": by_workflow.most_common(20),
        "by_workflow_errors": by_workflow_errors.most_common(10),
        "duration_ms": {"p50": p50, "p95": p95, "p99": p99, "max": durations_ms[-1] if durations_ms else None},
        "top_error_messages": error_messages.most_common(10),
    }


def render(stats: dict) -> str:
    lines = [f"Total executions sampled: {stats['total']}\n"]
    lines.append("By status:")
    for s, c in stats["by_status"].items():
        lines.append(f"  {s:10s}: {c}")
    lines.append("")
    d = stats["duration_ms"]
    if d.get("p50") is not None:
        lines.append(f"Duration: p50={d['p50']}ms  p95={d['p95']}ms  p99={d['p99']}ms  max={d['max']}ms")
        lines.append("")
    lines.append("Top workflows by execution count:")
    for wfid, c in stats["by_workflow_total"][:10]:
        lines.append(f"  wf={wfid:14s}: {c} runs")
    if stats["by_workflow_errors"]:
        lines.append("\nWorkflows w/ most errors:")
        for wfid, c in stats["by_workflow_errors"]:
            lines.append(f"  wf={wfid:14s}: {c} errors")
    if stats["top_error_messages"]:
        lines.append("\nTop error messages:")
        for msg, c in stats["top_error_messages"]:
            lines.append(f"  {c}× {msg}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate execution statistics (read-only)")
    parser.add_argument("--workflow", dest="workflow_id")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        items = fetch_executions(args.workflow_id, args.limit)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    stats = compute_stats(items)
    if args.json:
        print(json.dumps(stats, indent=2, default=str))
    else:
        print("\n=== Execution Stats ===\n", file=sys.stderr)
        print(render(stats), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
