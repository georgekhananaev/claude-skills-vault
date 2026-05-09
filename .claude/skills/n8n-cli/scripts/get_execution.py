#!/usr/bin/env python3
"""Fetch a single execution's full data — input/output per node, errors.

Read-only.

Usage:
  python3 get_execution.py --id <execution_id>
  python3 get_execution.py --id <execution_id> --include-data    # full input/output
  python3 get_execution.py --id <execution_id> --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, emit_human, validate_resource_id  # noqa: E402


def fetch_execution(eid: str, include_data: bool) -> dict:
    from _api import request
    validate_resource_id(eid, "execution_id")
    query = {"includeData": "true"} if include_data else None
    return request("GET", f"/api/v1/executions/{eid}", query=query)


def summarize(ex: dict) -> str:
    eid = ex.get("id", "?")
    wfid = ex.get("workflowId", "?")
    status = ex.get("status") or ("success" if ex.get("finished") else "?")
    started = (ex.get("startedAt") or "")[:19]
    stopped = (ex.get("stoppedAt") or "")[:19]
    mode = ex.get("mode", "?")

    lines = [
        f"Execution: {eid}",
        f"  workflow:  {wfid}",
        f"  status:    {status}",
        f"  mode:      {mode}",
        f"  started:   {started}",
        f"  stopped:   {stopped}",
    ]

    # Error info if present
    data = ex.get("data") or {}
    result_data = data.get("resultData") or {}
    error = result_data.get("error")
    if error:
        lines.append(f"\n  ERROR:")
        lines.append(f"    name:    {error.get('name', '?')}")
        lines.append(f"    message: {error.get('message', '?')}")
        node = error.get("node")
        if isinstance(node, dict):
            lines.append(f"    node:    {node.get('name', '?')} ({node.get('type', '?')})")
        stack = error.get("stack")
        if stack:
            lines.append(f"    stack (first 5 lines):")
            for sl in str(stack).splitlines()[:5]:
                lines.append(f"      {sl}")

    # Per-node summary
    run_data = result_data.get("runData") or {}
    if isinstance(run_data, dict) and run_data:
        lines.append(f"\n  Nodes executed: {len(run_data)}")
        for node_name, runs in list(run_data.items())[:20]:
            if isinstance(runs, list) and runs:
                first = runs[0]
                ms = first.get("executionTime", "?")
                err_in_node = "ERROR" if first.get("error") else "ok"
                lines.append(f"    - {node_name:30s}  {ms}ms  [{err_in_node}]")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Get a single execution's details (read-only)")
    parser.add_argument("--id", required=True, dest="execution_id")
    parser.add_argument("--include-data", action="store_true",
                        help="Include full input/output data per node (large)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        ex = fetch_execution(args.execution_id, args.include_data)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(ex, indent=2, default=str))
    else:
        emit_human("Execution Detail", summarize(ex))
    return 0


if __name__ == "__main__":
    sys.exit(main())
