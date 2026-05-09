#!/usr/bin/env python3
"""Show database profiler settings + recent slow ops captured.

Read-only. Uses mongosh.

The Atlas Performance Advisor pulls from the profiler — useful to confirm the
profiler is enabled & at the threshold you expect.

Usage:
  python3 profiler_status.py --db myapp
  python3 profiler_status.py --db myapp --recent 10   # show 10 most recent slow ops
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _mongo import MongoshError, mongosh_eval, validate_identifier  # noqa: E402


def fetch_profiler_status(db: str, recent: int, conn: str | None, user: str | None, pw: str | None) -> dict:
    validate_identifier(db, "database")
    recent = max(0, min(int(recent), 1000))   # clamp to safe int range
    js = f"""
        const lvl = db.getProfilingStatus();
        let recent_ops = [];
        try {{
            recent_ops = db.system.profile.find({{}}).sort({{ts: -1}}).limit({recent}).toArray();
        }} catch (e) {{ /* profiler collection not present at level 0 */ }}
        return {{ profilingStatus: lvl, recentSlowOps: recent_ops }};
    """
    return mongosh_eval(js, connection_string=conn, username=user, password=pw, db=db)


def summarize(payload: dict) -> str:
    status = payload.get("profilingStatus") or {}
    level = status.get("was") if "was" in status else status.get("level")
    threshold = status.get("slowms")
    sample_rate = status.get("sampleRate")
    recent = payload.get("recentSlowOps") or []

    LEVEL_DESC = {0: "off", 1: "slow ops only", 2: "all ops (caution!)"}
    lines = []
    lines.append(f"Profiler level:    {level} ({LEVEL_DESC.get(level, '?')})")
    lines.append(f"Slow op threshold: {threshold} ms")
    if sample_rate is not None:
        lines.append(f"Sample rate:       {sample_rate}")
    lines.append("")

    if not recent:
        lines.append("No recent profile entries (profiler may be off, or no slow ops recently).")
    else:
        lines.append(f"Recent {len(recent)} slow ops:")
        for op in recent:
            ns = op.get("ns", "?")
            opname = op.get("op", "?")
            ms = op.get("millis", 0)
            ts = op.get("ts", "?")
            ts_str = str(ts).split(".")[0] if ts else "?"
            lines.append(f"  [{ts_str}] {ns} {opname} {ms}ms")
            plan = op.get("planSummary")
            if plan:
                lines.append(f"      plan: {plan}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Database profiler status & recent slow ops")
    parser.add_argument("--db", required=True)
    parser.add_argument("--recent", type=int, default=5, help="Show this many recent slow ops (default 5)")
    parser.add_argument("--connection-string", dest="connection_string")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        payload = fetch_profiler_status(args.db, args.recent, args.connection_string,
                                        args.username, args.password)
    except MongoshError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(f"\n=== Profiler — {args.db} ===\n", file=sys.stderr)
        print(summarize(payload), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
