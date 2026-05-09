#!/usr/bin/env python3
"""End-to-end read-only performance audit of an Atlas cluster.

Combines:
  - Suggested indexes
  - Slow queries summary (last 24h)
  - Schema advice
  - Drop-index hints (advisory, never executed)
  - Cluster process metrics (CPU/mem/connections)

All read-only. Outputs a single consolidated report.

Usage:
  python3 performance_audit.py --cluster Cluster0
  python3 performance_audit.py --cluster Cluster0 --hours 6
  python3 performance_audit.py --cluster Cluster0 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, get_processes_for_cluster  # noqa: E402

# Re-import sibling modules for orchestration
import drop_index_hints  # noqa: E402
import schema_advice  # noqa: E402
import slow_queries  # noqa: E402
import suggest_indexes  # noqa: E402


def run_audit(cluster: str, project_id: str | None, hours: int) -> dict:
    report: dict = {"cluster": cluster, "errors": []}

    try:
        procs = get_processes_for_cluster(cluster, project_id)
        report["processes"] = [{"id": p.get("id"), "type": p.get("typeName"), "rs": p.get("replicaSetName")} for p in procs]
    except AtlasError as e:
        report["errors"].append(f"processes: {e}")
        report["processes"] = []

    try:
        report["suggestedIndexes"] = suggest_indexes.fetch_suggestions(
            cluster=cluster, project_id=project_id,
            namespaces=None, n_indexes=20, n_examples=2, since=None, duration=None,
        )
    except AtlasError as e:
        report["errors"].append(f"suggestedIndexes: {e}")
        report["suggestedIndexes"] = []

    try:
        report["slowQueries"] = slow_queries.fetch_slow_queries(
            cluster=cluster, project_id=project_id,
            namespaces=None, hours=hours, n_log=2000,
        )
    except AtlasError as e:
        report["errors"].append(f"slowQueries: {e}")
        report["slowQueries"] = []

    try:
        report["schemaAdvice"] = schema_advice.fetch_schema_advice(cluster, project_id)
    except AtlasError as e:
        report["errors"].append(f"schemaAdvice: {e}")
        report["schemaAdvice"] = {}

    try:
        report["dropHints"] = drop_index_hints.fetch_drop_hints(cluster, project_id)
    except AtlasError as e:
        report["errors"].append(f"dropHints: {e}")
        report["dropHints"] = {}

    return report


def render_report(report: dict, hours: int) -> str:
    sections = [f"╔══ Performance Audit — {report['cluster']} ══════════════════════"]

    if report.get("errors"):
        sections.append("║")
        sections.append("║ ⚠️  Partial run — some sections failed:")
        for err in report["errors"]:
            sections.append(f"║   - {err.splitlines()[0][:120]}")

    procs = report.get("processes", [])
    sections.append(f"║\n║ Processes: {len(procs)}")
    for p in procs[:5]:
        sections.append(f"║   - {p['id']} ({p.get('type', '?')})")

    sections.append("║\n║ ── Suggested Indexes ─────────────────────────────")
    sections.append("║ " + suggest_indexes.format_summary(report.get("suggestedIndexes", [])).replace("\n", "\n║ "))

    sections.append("║\n║ ── Slow Queries (last %dh) ──────────────────────" % hours)
    sections.append("║ " + slow_queries.summarize(report.get("slowQueries", [])).replace("\n", "\n║ "))

    sections.append("║\n║ ── Schema Advice ─────────────────────────────────")
    sections.append("║ " + schema_advice.summarize(report.get("schemaAdvice", {})).replace("\n", "\n║ "))

    sections.append("║\n║ ── Drop Index Hints (ADVISORY) ──────────────────")
    sections.append("║ " + drop_index_hints.summarize(report.get("dropHints", {})).replace("\n", "\n║ "))

    sections.append("╚══════════════════════════════════════════════════════════")
    sections.append("\nNext step: pick a high-impact suggested index → safe_index_create.py --confirm")
    return "\n".join(sections)


def main() -> int:
    parser = argparse.ArgumentParser(description="End-to-end read-only Atlas perf audit")
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run_audit(args.cluster, args.project_id, args.hours)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(render_report(report, args.hours), file=sys.stderr)
    # Partial data is still useful — exit 0 even if some sections errored.
    # Callers needing strict status should inspect report["errors"] in JSON mode.
    return 0


if __name__ == "__main__":
    sys.exit(main())
