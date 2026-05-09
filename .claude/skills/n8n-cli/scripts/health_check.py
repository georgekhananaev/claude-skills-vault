#!/usr/bin/env python3
"""Quick health check on an n8n instance — version, reachable, recent execution success rate.

Read-only.

Usage:
  python3 health_check.py
  python3 health_check.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError  # noqa: E402


def _probe_healthz() -> dict:
    """Hit /healthz directly via the base host (NOT through the API client —
    /healthz is unauthenticated & lives outside /api/v1)."""
    import os
    import urllib.error
    import urllib.parse
    import urllib.request

    base = (os.environ.get("N8N_API_URL") or "").rstrip("/")
    if not base:
        return {"reachable": False, "error": "N8N_API_URL not set"}
    url = base + "/healthz"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return {"reachable": True, "status": resp.status, "body": resp.read().decode("utf-8", errors="replace")[:200]}
    except urllib.error.HTTPError as e:
        # /healthz might 404 on some setups but the host is up
        return {"reachable": True, "status": e.code, "note": "host reachable"}
    except urllib.error.URLError as e:
        return {"reachable": False, "error": str(e.reason)}


def gather() -> dict:
    from _api import request
    info: dict = {}

    # Pre-API host reachability check (no auth required)
    info["healthz"] = _probe_healthz()

    # Health probe via workflows list (auth + reachability + DB)
    try:
        wf_resp = request("GET", "/api/v1/workflows", query={"limit": 1})
        info["api_reachable"] = True
        info["api_authenticated"] = True
        info["sample_workflow_count_in_first_page"] = len((wf_resp or {}).get("data") or [])
    except N8nError as e:
        info["api_reachable"] = False
        info["api_error"] = str(e)
        return info

    # Active workflow check
    try:
        active_resp = request("GET", "/api/v1/workflows", query={"active": "true", "limit": 1})
        info["has_active_workflows"] = bool((active_resp or {}).get("data"))
    except N8nError:
        pass

    # n8n CLI version (if available — best-effort)
    try:
        import shutil
        import subprocess
        if shutil.which("n8n"):
            r = subprocess.run(["n8n", "--version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                info["cli_version"] = r.stdout.strip()
    except Exception:
        pass

    # Recent execution stats (last 100)
    try:
        ex_resp = request("GET", "/api/v1/executions", query={"limit": 100})
        executions = (ex_resp or {}).get("data") or []
        from collections import Counter
        statuses = Counter()
        for e in executions:
            s = e.get("status") or ("success" if e.get("finished") else "?")
            statuses[s] += 1
        total = sum(statuses.values()) or 1
        info["recent_executions"] = {
            "total_sampled": total,
            "by_status": dict(statuses),
            "success_rate": round(100 * statuses.get("success", 0) / total, 1),
            "error_rate": round(100 * statuses.get("error", 0) / total, 1),
        }
    except N8nError:
        info["recent_executions"] = "unavailable"

    return info


def render(info: dict) -> str:
    lines = []
    if not info.get("api_reachable"):
        lines.append(f"❌ API unreachable: {info.get('api_error', '?')}")
        return "\n".join(lines)
    lines.append("✓ API reachable")
    if info.get("has_active_workflows"):
        lines.append("✓ At least one active workflow")
    rec = info.get("recent_executions")
    if isinstance(rec, dict):
        lines.append(f"\nRecent executions (last {rec.get('total_sampled')} sampled):")
        for s, c in (rec.get("by_status") or {}).items():
            lines.append(f"  {s}: {c}")
        sr = rec.get("success_rate")
        er = rec.get("error_rate")
        if er is not None and er > 10:
            lines.append(f"\n⚠️  High error rate: {er}% — investigate w/ list_executions.py --status error")
        else:
            lines.append(f"\nSuccess rate: {sr}% / Error rate: {er}%")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="n8n instance health check (read-only)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    info = gather()

    if args.json:
        print(json.dumps(info, indent=2, default=str))
    else:
        print("\n=== n8n Health Check ===\n", file=sys.stderr)
        print(render(info), file=sys.stderr)
    return 0 if info.get("api_reachable") else 1


if __name__ == "__main__":
    sys.exit(main())
