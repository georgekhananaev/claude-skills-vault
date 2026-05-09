#!/usr/bin/env python3
"""List credentials — names, types, IDs, owner, project. NO secret values.

Read-only. The skill never exposes credential secret data via this script.
For encrypted backups use `export_credentials.py`.

Usage:
  python3 list_credentials.py
  python3 list_credentials.py --type slackOAuth2Api
  python3 list_credentials.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, emit_human  # noqa: E402

# Fields that might leak secrets if the API mistakenly returns them.
# Strip these defensively even if the API includes them.
SENSITIVE_FIELDS = {"data", "encryptedData", "nodesAccess"}


def fetch_credentials(cred_type: str | None) -> list[dict]:
    from _api import list_paginated
    query = {"limit": 250}
    if cred_type:
        query["type"] = cred_type
    items = list_paginated("/api/v1/credentials", query=query)
    # Defensive scrub
    for c in items:
        for f in SENSITIVE_FIELDS:
            c.pop(f, None)
    return items


def summarize(items: list[dict]) -> str:
    if not items:
        return "No credentials match filters."
    from collections import Counter
    by_type = Counter(c.get("type", "?") for c in items)
    lines = [f"Credentials: {len(items)}\n"]
    lines.append("Top types:")
    for t, c in by_type.most_common(10):
        lines.append(f"  {c:>4}  {t}")
    lines.append("")
    for c in items[:30]:
        cid = c.get("id", "?")
        name = c.get("name", "?")
        ctype = c.get("type", "?")
        updated = (c.get("updatedAt") or "")[:19]
        lines.append(f"  {cid:12s}  {name:30s} ({ctype})  updated={updated}")
    if len(items) > 30:
        lines.append(f"\n  ... +{len(items) - 30} more")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List credentials by name/type (read-only, no secrets)")
    parser.add_argument("--type", dest="cred_type", help="Filter by credential type")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        items = fetch_credentials(args.cred_type)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(items, indent=2, default=str))
    else:
        emit_human("Credentials (metadata only)", summarize(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
