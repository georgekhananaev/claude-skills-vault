#!/usr/bin/env python3
"""Compare two performance audits — show what changed week-over-week.

Pure local script. Reads two JSON outputs from `performance_audit.py --json`
and produces a diff report.

Usage:
  # Save snapshots over time
  python3 performance_audit.py --cluster Cluster0 --json > audit-2026-05-09.json
  # ... 1 week later ...
  python3 performance_audit.py --cluster Cluster0 --json > audit-2026-05-16.json

  # Compare
  python3 audit_diff.py audit-2026-05-09.json audit-2026-05-16.json

  # Markdown output
  python3 audit_diff.py audit-2026-05-09.json audit-2026-05-16.json --markdown > diff.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def index_set(items: list[dict]) -> dict[str, dict]:
    """Map ns::name -> entry."""
    out = {}
    for it in items or []:
        ns = it.get("namespace", "?")
        name = it.get("name") or json.dumps(it.get("index"), sort_keys=True)
        out[f"{ns}::{name}"] = it
    return out


def suggested_set(items: list[dict]) -> dict[str, dict]:
    out = {}
    for s in items or []:
        ns = s.get("namespace", "?")
        keys = json.dumps(s.get("index"), sort_keys=True)
        out[f"{ns}::{keys}"] = s
    return out


def render(diff: dict, markdown: bool) -> str:
    h1 = "# " if markdown else "=== "
    h2 = "## " if markdown else "--- "
    bullet = "- " if markdown else "  - "
    lines = []

    lines.append(f"{h1}Audit Diff — {diff['cluster']}")
    lines.append(f"")
    lines.append(f"_Compared_: `{diff['old_file']}` → `{diff['new_file']}`")
    lines.append("")

    # Summary table
    s = diff["summary"]
    lines.append(f"{h2}Summary of changes")
    lines.append("")
    lines.append("| Metric | Old | New | Δ |")
    lines.append("|---|---:|---:|---:|")
    for k, (old, new) in s.items():
        delta = new - old if isinstance(old, (int, float)) and isinstance(new, (int, float)) else "?"
        if isinstance(delta, (int, float)):
            arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "—")
            lines.append(f"| {k} | {old} | {new} | {arrow} {abs(delta)} |")
        else:
            lines.append(f"| {k} | {old} | {new} | — |")
    lines.append("")

    # Suggested indexes
    sug = diff["suggested"]
    lines.append(f"{h2}Suggested indexes")
    lines.append("")
    if sug["resolved"]:
        lines.append(f"### ✅ Resolved ({len(sug['resolved'])}) — advisor no longer flags these")
        lines.append("")
        for k in sug["resolved"]:
            lines.append(f"{bullet}{k}")
        lines.append("")
    if sug["new"]:
        lines.append(f"### 🆕 New ({len(sug['new'])}) — advisor newly suggests these")
        lines.append("")
        for k, v in sug["new"].items():
            lines.append(f"{bullet}{k} (weight {v.get('weight', 0):.0f})")
        lines.append("")
    if not (sug["resolved"] or sug["new"]):
        lines.append("_No change._")
        lines.append("")

    # Drop hints
    dh = diff["drop_hints"]
    lines.append(f"{h2}Drop-index hints (redundant)")
    lines.append("")
    if dh["resolved"]:
        lines.append(f"### ✅ Resolved ({len(dh['resolved'])}) — no longer flagged (likely dropped or now used)")
        lines.append("")
        for k in dh["resolved"]:
            lines.append(f"{bullet}{k}")
        lines.append("")
    if dh["new"]:
        lines.append(f"### 🆕 New ({len(dh['new'])}) — newly flagged as redundant")
        lines.append("")
        for k in dh["new"]:
            lines.append(f"{bullet}{k}")
        lines.append("")
    if not (dh["resolved"] or dh["new"]):
        lines.append("_No change._")
        lines.append("")

    # Schema advice
    sch = diff["schema"]
    lines.append(f"{h2}Schema recommendations")
    lines.append("")
    if sch["resolved"]:
        lines.append(f"### ✅ Resolved ({len(sch['resolved'])})")
        lines.append("")
        for c in sch["resolved"]:
            lines.append(f"{bullet}{c}")
        lines.append("")
    if sch["new"]:
        lines.append(f"### 🆕 New ({len(sch['new'])})")
        lines.append("")
        for c in sch["new"]:
            lines.append(f"{bullet}{c}")
        lines.append("")
    if not (sch["resolved"] or sch["new"]):
        lines.append("_No change._")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff two performance_audit JSON snapshots")
    parser.add_argument("old", type=Path, help="Older audit JSON")
    parser.add_argument("new", type=Path, help="Newer audit JSON")
    parser.add_argument("--markdown", action="store_true", help="Markdown output")
    parser.add_argument("--json", action="store_true", help="Pure JSON diff")
    args = parser.parse_args()

    if not args.old.exists() or not args.new.exists():
        print(f"ERROR: input files must exist", file=sys.stderr)
        return 1

    a = load(args.old)
    b = load(args.new)

    if a.get("cluster") != b.get("cluster"):
        print(f"WARN: cluster mismatch ({a.get('cluster')} vs {b.get('cluster')})", file=sys.stderr)

    # Suggested indexes diff
    a_sug = suggested_set(a.get("suggestedIndexes") or [])
    b_sug = suggested_set(b.get("suggestedIndexes") or [])
    sug_resolved = sorted(set(a_sug) - set(b_sug))
    sug_new = {k: b_sug[k] for k in sorted(set(b_sug) - set(a_sug))}

    # Drop hints diff (only redundant; the others)
    def extract_redundant(payload):
        body = (payload or {}).get("content") or payload or {}
        out = []
        for r in (body.get("redundantIndexes") or []):
            out.append({"namespace": r.get("namespace"), "name": r.get("name"), "index": r.get("index")})
        return out
    a_drop = index_set(extract_redundant(a.get("dropHints")))
    b_drop = index_set(extract_redundant(b.get("dropHints")))

    # Schema diff (by recommendation code)
    def extract_schema(payload):
        body = (payload or {}).get("content") or payload or {}
        return [r.get("recommendation") or r.get("description", "?") for r in (body.get("recommendations") or [])]
    a_sch = set(extract_schema(a.get("schemaAdvice")))
    b_sch = set(extract_schema(b.get("schemaAdvice")))

    diff = {
        "cluster": b.get("cluster") or a.get("cluster") or "?",
        "old_file": str(args.old),
        "new_file": str(args.new),
        "summary": {
            "Suggested indexes":  (len(a_sug), len(b_sug)),
            "Redundant indexes":  (len(a_drop), len(b_drop)),
            "Schema recommendations": (len(a_sch), len(b_sch)),
            "Slow query log lines": (len(a.get("slowQueries") or []), len(b.get("slowQueries") or [])),
        },
        "suggested": {
            "resolved": sug_resolved,
            "new": sug_new,
        },
        "drop_hints": {
            "resolved": sorted(set(a_drop) - set(b_drop)),
            "new": sorted(set(b_drop) - set(a_drop)),
        },
        "schema": {
            "resolved": sorted(a_sch - b_sch),
            "new": sorted(b_sch - a_sch),
        },
    }

    if args.json:
        print(json.dumps(diff, indent=2, default=str))
    else:
        print(render(diff, args.markdown))
    return 0


if __name__ == "__main__":
    sys.exit(main())
