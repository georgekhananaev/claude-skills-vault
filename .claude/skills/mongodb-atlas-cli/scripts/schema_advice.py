#!/usr/bin/env python3
"""Fetch Performance Advisor's schema recommendations for a cluster.

Read-only. Wraps `atlas api performanceAdvisor listSchemaAdvice`.

Returns schema anti-pattern findings: bloated docs, unbounded arrays, unindexed
filterable fields, etc. Recommendations only — no auto-fix.

Usage:
  python3 schema_advice.py --cluster Cluster0
  python3 schema_advice.py --cluster Cluster0 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, emit_human, resolve_project_id, run_atlas  # noqa: E402


def fetch_schema_advice(cluster: str, project_id: str | None) -> dict:
    pid = resolve_project_id(project_id)
    if not pid:
        raise AtlasError(
            "MISSING: project ID — pass --projectId, set MONGODB_ATLAS_PROJECT_ID, "
            "or run `atlas config init` to set it in your profile."
        )
    args = [
        "api", "performanceAdvisor", "listSchemaAdvice",
        "--clusterName", cluster,
        "--version", "2024-08-05",
        "--groupId", pid,
    ]
    data = run_atlas(args)
    return data if isinstance(data, dict) else {}


def summarize(advice: dict) -> str:
    # Atlas API wraps the payload: {"content": {"recommendations": [...]}, "status": 200}
    if isinstance(advice, dict) and isinstance(advice.get("content"), dict):
        rec = advice["content"].get("recommendations") or []
    elif isinstance(advice, list):
        rec = advice
    else:
        rec = advice.get("recommendations") if isinstance(advice, dict) else [] or []

    if not rec:
        return "No schema recommendations. Either schemas look healthy or sample size is too small."

    lines = [f"Schema recommendations: {len(rec)}\n"]
    for i, r in enumerate(rec, 1):
        desc = r.get("description") or r.get("recommendation") or "?"
        code = r.get("recommendation") or ""
        affected = r.get("affectedNamespaces") or []
        ns_lines: list[str] = []
        triggers_seen: set[str] = set()
        for a in affected[:5]:
            if isinstance(a, dict):
                ns = a.get("namespace", "?")
                trig_descs = []
                for t in a.get("triggers") or []:
                    if isinstance(t, dict):
                        t_desc = t.get("description") or t.get("triggerType", "?")
                        triggers_seen.add(t.get("triggerType", t_desc))
                        trig_descs.append(t_desc)
                ns_lines.append(f"        {ns}" + (f" — {trig_descs[0]}" if trig_descs else ""))
            else:
                ns_lines.append(f"        {a}")
        more = len(affected) - len(ns_lines)
        lines.append(f"  [{i}] {desc}" + (f"  [{code}]" if code and code != desc else ""))
        if ns_lines:
            lines.append("      affected namespaces:")
            lines.extend(ns_lines)
            if more > 0:
                lines.append(f"        (+{more} more)")
    lines.append(
        "\nAdvisory only. Schema changes require app-side coordination — review w/ "
        "your team before migrating data."
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Get schema recommendations from Performance Advisor")
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        advice = fetch_schema_advice(args.cluster, args.project_id)
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(advice, indent=2))
    else:
        emit_human("Schema Advice", summarize(advice))
    return 0


if __name__ == "__main__":
    sys.exit(main())
