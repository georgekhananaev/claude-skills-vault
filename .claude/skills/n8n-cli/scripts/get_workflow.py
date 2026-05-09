#!/usr/bin/env python3
"""Describe a single n8n workflow — nodes, connections, settings, full JSON.

Read-only. API-only (CLI doesn't have a get-by-id command short of export).

Usage:
  python3 get_workflow.py --id <workflow_id>
  python3 get_workflow.py --id <workflow_id> --summary    # node list only
  python3 get_workflow.py --id <workflow_id> --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, emit_human, validate_resource_id  # noqa: E402


def fetch_workflow(workflow_id: str) -> dict:
    from _api import request
    validate_resource_id(workflow_id, "workflow_id")
    return request("GET", f"/api/v1/workflows/{workflow_id}")


def summarize(wf: dict, summary_only: bool) -> str:
    name = wf.get("name", "?")
    wid = wf.get("id", "?")
    active = wf.get("active", "?")
    nodes = wf.get("nodes") or []
    connections = wf.get("connections") or {}
    tags = wf.get("tags") or []
    settings = wf.get("settings") or {}
    created = (wf.get("createdAt") or "")[:19]
    updated = (wf.get("updatedAt") or "")[:19]

    lines = [
        f"Workflow: {name} (id={wid})",
        f"  active:    {active}",
        f"  nodes:     {len(nodes)}",
        f"  connects:  {sum(len(v) for v in connections.values()) if isinstance(connections, dict) else 0}",
        f"  tags:      {', '.join(t.get('name', t) if isinstance(t, dict) else str(t) for t in tags) or '(none)'}",
        f"  created:   {created}",
        f"  updated:   {updated}",
    ]

    # Node summary table
    lines.append("\n  Nodes:")
    for n in nodes[:50]:
        nname = n.get("name", "?")
        ntype = n.get("type", "?").split(".")[-1]  # short form
        disabled = " [disabled]" if n.get("disabled") else ""
        lines.append(f"    - {nname:30s}  ({ntype}){disabled}")
    if len(nodes) > 50:
        lines.append(f"    ... +{len(nodes) - 50} more nodes")

    if not summary_only and settings:
        lines.append("\n  Settings:")
        for k, v in settings.items():
            lines.append(f"    {k}: {v}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Get a single workflow's details (read-only)")
    parser.add_argument("--id", required=True, dest="workflow_id")
    parser.add_argument("--summary", action="store_true",
                        help="Show only node list (skip settings)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        wf = fetch_workflow(args.workflow_id)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(wf, indent=2, default=str))
    else:
        emit_human("Workflow Detail", summarize(wf, args.summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
