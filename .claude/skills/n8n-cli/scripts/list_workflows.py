#!/usr/bin/env python3
"""List n8n workflows — name, ID, active state, tags, project, updated time.

Read-only. Uses REST API (preferred) or CLI fallback (`n8n list:workflow`).

Usage:
  python3 list_workflows.py                       # all workflows
  python3 list_workflows.py --active true         # only active/published
  python3 list_workflows.py --tag prod            # filter by tag
  python3 list_workflows.py --name webhook        # name substring
  python3 list_workflows.py --json
  python3 list_workflows.py --backend cli         # force CLI backend

Filters work via API. CLI backend returns all (filter client-side here).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, emit_human, resolve_backend, run_n8n_cli  # noqa: E402


def fetch_via_api(active: str | None, tag: str | None, project_id: str | None) -> list[dict]:
    from _api import list_paginated
    query: dict = {"limit": 250}
    if active is not None:
        query["active"] = "true" if active.lower() in {"true", "1", "yes"} else "false"
    if tag:
        query["tags"] = tag
    if project_id:
        query["projectId"] = project_id
    return list_paginated("/api/v1/workflows", query=query)


def fetch_via_cli() -> list[dict]:
    """Use `n8n list:workflow` (CLI). Output is plain text — table-like."""
    raw = run_n8n_cli(["list:workflow"], json_out=False)
    workflows: list[dict] = []
    if not isinstance(raw, str):
        return workflows
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.lower().startswith(("id|", "id ", "---")):
            continue
        # Heuristic parse: "<id>|<name>" or "<id>\t<name>" or whitespace-split
        parts = [p.strip() for p in line.replace("|", "\t").split("\t") if p.strip()]
        if len(parts) >= 2:
            workflows.append({"id": parts[0], "name": " ".join(parts[1:])})
        else:
            workflows.append({"raw": line})
    return workflows


def filter_client_side(items: list[dict], name: str | None) -> list[dict]:
    if not name:
        return items
    needle = name.lower()
    return [w for w in items if needle in (w.get("name") or "").lower()]


def summarize(items: list[dict]) -> str:
    if not items:
        return "No workflows match filters."
    lines = [f"Workflows: {len(items)}\n"]
    active_count = sum(1 for w in items if w.get("active") is True)
    if active_count:
        lines.append(f"Active/published: {active_count}\n")
    for w in items[:50]:
        wid = w.get("id", "?")
        name = w.get("name", "?")
        active = " [active]" if w.get("active") is True else ""
        tags = w.get("tags") or []
        tag_names = ", ".join(t.get("name", t) if isinstance(t, dict) else str(t) for t in tags)
        updated = (w.get("updatedAt") or "")[:19]
        lines.append(f"  {wid}  {name}{active}")
        if tag_names:
            lines.append(f"      tags: {tag_names}")
        if updated:
            lines.append(f"      updated: {updated}")
    if len(items) > 50:
        lines.append(f"\n  ... +{len(items) - 50} more (use --json for full list)")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List n8n workflows (read-only)")
    parser.add_argument("--active", help="Filter by active state: true/false")
    parser.add_argument("--tag", help="Filter by tag name (API only)")
    parser.add_argument("--name", help="Filter by name substring (client-side)")
    parser.add_argument("--projectId", dest="project_id", help="Filter by project (API only)")
    parser.add_argument("--backend", choices=["cli", "api"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        backend = resolve_backend(args.backend)
        if backend == "api":
            workflows = fetch_via_api(args.active, args.tag, args.project_id)
        else:
            workflows = fetch_via_cli()
        workflows = filter_client_side(workflows, args.name)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(workflows, indent=2, default=str))
    else:
        emit_human(f"Workflows ({backend} backend)", summarize(workflows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
