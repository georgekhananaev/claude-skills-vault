#!/usr/bin/env python3
"""Show source-control (git) status for the n8n instance. Read-only.

Source-control PULL and PUSH ops are REFUSED (overwrites). This script only
reads status — local-vs-remote diff, last-pull info, conflicts.

Usage:
  python3 source_control_status.py
  python3 source_control_status.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError  # noqa: E402


def fetch_status() -> dict:
    from _api import request
    # GET /api/v1/source-control returns config + status info on most n8n versions
    return request("GET", "/api/v1/source-control/status")


def render(status: dict) -> str:
    if not isinstance(status, dict):
        return f"(unexpected response shape: {type(status).__name__})"
    lines = []
    if "branch" in status:
        lines.append(f"Branch:           {status.get('branch')}")
    if "behind" in status or "ahead" in status:
        lines.append(f"Local vs remote:  ahead={status.get('ahead', 0)}  behind={status.get('behind', 0)}")
    if status.get("conflicts"):
        lines.append(f"⚠️  Conflicts:    {len(status['conflicts'])}")
    if status.get("pull"):
        lines.append("Pending changes (would be pulled):")
        for c in status.get("pull", [])[:20]:
            lines.append(f"  - {c.get('type', '?')}: {c.get('name', c.get('id', '?'))}")
    if status.get("push"):
        lines.append("\nLocal-only changes (would be pushed):")
        for c in status.get("push", [])[:20]:
            lines.append(f"  - {c.get('type', '?')}: {c.get('name', c.get('id', '?'))}")
    if not lines:
        return "Source-control: clean (no pending changes) or not configured."
    lines.append("\nThis skill REFUSES `pull` and `push`. Run them in the n8n UI if you mean to.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="n8n source-control status (read-only)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        status = fetch_status()
    except N8nError as e:
        msg = str(e)
        if "HTTP 404" in msg or "HTTP 400" in msg:
            print("Source-control not configured on this instance.", file=sys.stderr)
            return 0
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(status, indent=2, default=str))
    else:
        print("\n=== Source-control status ===\n", file=sys.stderr)
        print(render(status), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
