#!/usr/bin/env python3
"""List n8n environment variables (visible to workflows via $vars). Read-only.

These are NOT process env vars — they're n8n's first-class variable feature
exposed in workflows as $vars.<key>. Useful for migration audits.

Usage:
  python3 list_variables.py
  python3 list_variables.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, emit_human  # noqa: E402


def fetch_variables() -> list[dict]:
    from _api import list_paginated
    return list_paginated("/api/v1/variables", query={"limit": 250})


def summarize(items: list[dict]) -> str:
    if not items:
        return "No variables (or this n8n version doesn't support them)."
    lines = [f"Variables: {len(items)}\n"]
    for v in items[:50]:
        vid = v.get("id", "?")
        key = v.get("key", "?")
        # Variable VALUES may be sensitive — n8n doesn't expose them via API for
        # non-owners but defensively don't echo them in summary.
        has_value = bool(v.get("value"))
        vtype = v.get("type", "string")
        lines.append(f"  {vid:14s}  {key:30s}  ({vtype})" + ("  [has value]" if has_value else ""))
    if len(items) > 50:
        lines.append(f"\n  ... +{len(items) - 50} more")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List n8n variables (read-only, redacts values)")
    parser.add_argument("--json", action="store_true",
                        help="Include values in output (use carefully)")
    args = parser.parse_args()

    try:
        items = fetch_variables()
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(items, indent=2, default=str))
    else:
        emit_human("Variables", summarize(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
