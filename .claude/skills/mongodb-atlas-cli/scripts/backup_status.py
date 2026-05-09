#!/usr/bin/env python3
"""Verify backup health — list snapshots & flag stale backups.

Read-only. Wraps `atlas backups snapshots list <cluster>`.

Usage:
  python3 backup_status.py --cluster Cluster0
  python3 backup_status.py --cluster Cluster0 --projectId <id>
  python3 backup_status.py --cluster Cluster0 --json
  python3 backup_status.py --cluster Cluster0 --max-age-hours 30   # warn if last snapshot older

Flags as warnings (non-zero exit):
  - No snapshots in last 24h (default; configurable via --max-age-hours)
  - Latest snapshot status != "completed"
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, emit_human, resolve_project_id, run_atlas  # noqa: E402


def fetch_snapshots(cluster: str, project_id: str | None) -> list[dict]:
    args = ["backups", "snapshots", "list", cluster]
    pid = resolve_project_id(project_id)
    if pid:
        args += ["--projectId", pid]
    data = run_atlas(args)
    if isinstance(data, dict):
        return data.get("results", []) or []
    return data if isinstance(data, list) else []


def parse_dt(s: str | None) -> datetime.datetime | None:
    if not s:
        return None
    try:
        # Atlas API returns ISO-8601 like "2026-05-09T03:14:15Z"
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def summarize(snapshots: list[dict], max_age_hours: float) -> tuple[str, int]:
    """Return (text, exit_code). Exit non-zero if backup is stale."""
    if not snapshots:
        return ("⚠️  No snapshots found. Cloud backup may be disabled.", 2)

    snapshots_sorted = sorted(snapshots, key=lambda s: s.get("createdAt") or "", reverse=True)
    latest = snapshots_sorted[0]
    latest_dt = parse_dt(latest.get("createdAt"))
    now = datetime.datetime.now(datetime.timezone.utc)  # 3.10-compatible
    exit_code = 0

    lines = [f"Snapshots: {len(snapshots)}\n"]
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for s in snapshots:
        st = s.get("status", "?")
        by_status[st] = by_status.get(st, 0) + 1
        tp = s.get("snapshotType", "?")
        by_type[tp] = by_type.get(tp, 0) + 1
    lines.append("By status: " + ", ".join(f"{k}={v}" for k, v in by_status.items()))
    lines.append("By type:   " + ", ".join(f"{k}={v}" for k, v in by_type.items()))
    lines.append("")

    # Health flags
    if latest_dt:
        age = now - latest_dt
        age_hours = age.total_seconds() / 3600
        if age_hours > max_age_hours:
            lines.append(f"⚠️  Latest snapshot is **{age_hours:.1f} hours old** (threshold: {max_age_hours}h)")
            exit_code = 3
        else:
            lines.append(f"✅ Latest snapshot is {age_hours:.1f} hours old (within {max_age_hours}h threshold)")
    if latest.get("status") != "completed":
        lines.append(f"⚠️  Latest snapshot status is **{latest.get('status')}**, not 'completed'")
        exit_code = max(exit_code, 4)

    lines.append("")
    lines.append("Latest 10 snapshots:")
    for s in snapshots_sorted[:10]:
        sid = s.get("id", "?")[:12]
        created = (s.get("createdAt") or "?")[:19]
        expires = (s.get("expires") or "?")[:19]
        status = s.get("status", "?")
        tp = s.get("snapshotType", "?")
        size_mb = (s.get("storageSizeBytes") or 0) / (1024 * 1024)
        lines.append(f"  {sid} {tp:8s} {status:10s} created={created}  expires={expires}  size={size_mb:.0f}MB")

    return ("\n".join(lines), exit_code)


def main() -> int:
    parser = argparse.ArgumentParser(description="Atlas backup snapshot status (read-only)")
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--max-age-hours", type=float, default=26.0,
                        help="Warn if latest snapshot older than this (default: 26h ~ 1 daily backup)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        snapshots = fetch_snapshots(args.cluster, args.project_id)
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(snapshots, indent=2, default=str))
        return 0

    text, exit_code = summarize(snapshots, args.max_age_hours)
    emit_human(f"Backups — {args.cluster}", text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
