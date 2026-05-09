#!/usr/bin/env python3
"""List n8n projects (workspaces). Read-only.

Useful for finding projectId values to pass to list_workflows.py --projectId.

Usage:
  python3 list_projects.py
  python3 list_projects.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, emit_human  # noqa: E402


def fetch_projects() -> list[dict]:
    from _api import list_paginated
    return list_paginated("/api/v1/projects", query={"limit": 250})


def summarize(items: list[dict]) -> str:
    if not items:
        return "No projects (this n8n version may not support multi-project)."
    lines = [f"Projects: {len(items)}\n"]
    for p in items[:50]:
        pid = p.get("id", "?")
        name = p.get("name", "?")
        ptype = p.get("type", "")
        lines.append(f"  {pid:14s}  {name}" + (f"  ({ptype})" if ptype else ""))
    if len(items) > 50:
        lines.append(f"\n  ... +{len(items) - 50} more")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List n8n projects (read-only)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        items = fetch_projects()
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(items, indent=2, default=str))
    else:
        emit_human("Projects", summarize(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
