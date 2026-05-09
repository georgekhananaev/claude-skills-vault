#!/usr/bin/env python3
"""List recent workflow executions.

Read-only. API-based.

Usage:
  python3 list_executions.py
  python3 list_executions.py --workflow <id> --status error --limit 50
  python3 list_executions.py --status success --json

--status values: success, error, waiting, running, canceled
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, emit_human  # noqa: E402

VALID_STATUS = {"success", "error", "waiting", "running", "canceled", "crashed"}


def fetch_executions(workflow_id: str | None, status: str | None, limit: int) -> list[dict]:
    from _api import list_paginated
    query: dict = {"limit": min(limit, 250)}
    if workflow_id:
        query["workflowId"] = workflow_id
    if status:
        query["status"] = status
    items = list_paginated("/api/v1/executions", query=query, max_pages=10)
    return items[:limit]


def _status_of(e: dict) -> str:
    """Resolve status from the (sometimes-inconsistent) execution record shape."""
    s = e.get("status")
    if s:
        return s
    finished = e.get("finished")
    if finished is True:
        return "success"
    if finished is False:
        return "error"
    return "unknown"


def summarize(items: list[dict]) -> str:
    if not items:
        return "No executions match filters."
    from collections import Counter
    by_status = Counter(_status_of(e) for e in items)
    lines = [f"Executions: {len(items)}\n"]
    lines.append("By status: " + ", ".join(f"{k}={v}" for k, v in by_status.items()))
    lines.append("")
    for e in items[:30]:
        eid = e.get("id", "?")
        wfid = e.get("workflowId", "?")
        status = _status_of(e)
        started = (e.get("startedAt") or "")[:19]
        stopped = (e.get("stoppedAt") or "")[:19]
        mode = e.get("mode", "?")
        flag = "✗" if status == "error" else ("✓" if status == "success" else "•")
        lines.append(f"  {flag} {eid:12s}  wf={wfid:12s} {status:8s} mode={mode}  started={started}")
        if stopped and stopped != started:
            try:
                from datetime import datetime
                t1 = datetime.fromisoformat(started)
                t2 = datetime.fromisoformat(stopped)
                ms = int((t2 - t1).total_seconds() * 1000)
                lines.append(f"      duration: {ms}ms")
            except Exception:
                pass
    if len(items) > 30:
        lines.append(f"\n  ... +{len(items) - 30} more")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List workflow executions (read-only)")
    parser.add_argument("--workflow", dest="workflow_id")
    parser.add_argument("--status", choices=sorted(VALID_STATUS))
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        items = fetch_executions(args.workflow_id, args.status, args.limit)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(items, indent=2, default=str))
    else:
        emit_human("Executions", summarize(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
