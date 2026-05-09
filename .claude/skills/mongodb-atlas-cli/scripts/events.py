#!/usr/bin/env python3
"""List Atlas project events — audit log of admin actions.

Read-only. Wraps `atlas events list`.

Useful for forensics: who created/modified what, when. Default returns last 100
events; filter w/ --type to narrow (e.g. --type CLUSTER_DELETED).

Usage:
  python3 events.py
  python3 events.py --projectId <id>
  python3 events.py --type CLUSTER_DELETED
  python3 events.py --json --limit 500
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, emit_human, resolve_project_id, run_atlas  # noqa: E402


def fetch_events(
    project_id: str | None, event_type: str | None, limit: int,
) -> list[dict]:
    args = ["events", "list", "--limit", str(limit)]
    pid = resolve_project_id(project_id)
    if pid:
        args += ["--projectId", pid]
    if event_type:
        args += ["--type", event_type]
    data = run_atlas(args)
    if isinstance(data, dict):
        return data.get("results", []) or []
    return data if isinstance(data, list) else []


def summarize(events: list[dict]) -> str:
    if not events:
        return "No events. Either filtered out or quiet project."
    from collections import Counter
    by_type = Counter(e.get("eventTypeName", "?") for e in events)
    by_user = Counter(e.get("username") or e.get("userId") or "?" for e in events)

    lines = [f"Events: {len(events)}\n"]
    lines.append("Top event types:")
    for t, c in by_type.most_common(10):
        lines.append(f"  {c:>4}  {t}")
    lines.append("\nTop actors:")
    for u, c in by_user.most_common(8):
        lines.append(f"  {c:>4}  {u}")
    lines.append("\nLatest 10 events:")
    for e in events[:10]:
        when = (e.get("created") or "")[:19]
        actor = e.get("username") or e.get("userId") or "?"
        ev = e.get("eventTypeName", "?")
        target = e.get("targetUsername") or e.get("publicKey") or e.get("collectionName") or ""
        lines.append(f"  [{when}] {actor:30s} {ev}" + (f" → {target}" if target else ""))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List Atlas project events / audit log (read-only)")
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--type", dest="event_type",
                        help="Filter by event type (e.g. CLUSTER_DELETED, INDEX_CREATED, USER_LOGIN_SUCCESS)")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        events = fetch_events(args.project_id, args.event_type, args.limit)
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(events, indent=2, default=str))
    else:
        emit_human("Atlas Events", summarize(events))
    return 0


if __name__ == "__main__":
    sys.exit(main())
