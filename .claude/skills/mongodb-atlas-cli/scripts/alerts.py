#!/usr/bin/env python3
"""List active Atlas alerts for a project.

Read-only. Wraps `atlas alerts list`.

Usage:
  python3 alerts.py
  python3 alerts.py --projectId <id> --status OPEN
  python3 alerts.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, emit_human, resolve_project_id, run_atlas  # noqa: E402


def fetch_alerts(project_id: str | None, status: str | None) -> list[dict]:
    args = ["alerts", "list"]
    pid = resolve_project_id(project_id)
    if pid:
        args += ["--projectId", pid]
    if status:
        args += ["--status", status]
    data = run_atlas(args)
    if isinstance(data, dict):
        return data.get("results", []) or []
    return data if isinstance(data, list) else []


def summarize(alerts: list[dict]) -> str:
    if not alerts:
        return "No alerts. Either filtered out or the cluster is happy."
    lines = [f"Alerts: {len(alerts)}\n"]
    by_status: dict[str, int] = {}
    for a in alerts:
        s = a.get("status", "?")
        by_status[s] = by_status.get(s, 0) + 1
    lines.append("By status: " + ", ".join(f"{k}={v}" for k, v in by_status.items()))
    lines.append("")
    for a in alerts[:20]:
        status = a.get("status", "?")
        ev_type = a.get("eventTypeName") or a.get("alertConfigId", "?")
        created = a.get("created", "?")[:19]
        updated = a.get("updated", "?")[:19]
        meta = a.get("metricName") or a.get("currentValue") or ""
        flag = "🔴" if status == "OPEN" else ("✅" if status == "CLOSED" else "⏳")
        lines.append(f"  {flag} [{status}] {ev_type}  created={created}  updated={updated}")
        if meta:
            lines.append(f"      detail: {meta}")
    if len(alerts) > 20:
        lines.append(f"\n  ... +{len(alerts) - 20} more (use --json for full list)")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="List Atlas project alerts (read-only)")
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--status", choices=["OPEN", "CLOSED", "TRACKING", "CANCELLED"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        alerts = fetch_alerts(args.project_id, args.status)
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(alerts, indent=2, default=str))
    else:
        emit_human("Atlas Alerts", summarize(alerts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
