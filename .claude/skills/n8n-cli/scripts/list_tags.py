#!/usr/bin/env python3
"""List n8n tags. Read-only.

Usage:
  python3 list_tags.py
  python3 list_tags.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, emit_human  # noqa: E402


def fetch_tags() -> list[dict]:
    from _api import list_paginated
    return list_paginated("/api/v1/tags", query={"limit": 250})


def summarize(items: list[dict]) -> str:
    if not items:
        return "No tags."
    lines = [f"Tags: {len(items)}\n"]
    for t in items[:50]:
        tid = t.get("id", "?")
        name = t.get("name", "?")
        lines.append(f"  {tid:14s}  {name}")
    if len(items) > 50:
        lines.append(f"\n  ... +{len(items) - 50} more")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List n8n tags (read-only)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        items = fetch_tags()
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(items, indent=2, default=str))
    else:
        emit_human("Tags", summarize(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
