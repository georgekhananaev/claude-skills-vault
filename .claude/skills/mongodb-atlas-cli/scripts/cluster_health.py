#!/usr/bin/env python3
"""Pull cluster process metrics — CPU, memory, opcounters, connections.

Read-only. Wraps `atlas metrics processes <host:port>`.

Usage:
  python3 cluster_health.py --cluster Cluster0
  python3 cluster_health.py --cluster Cluster0 --period PT1H
  python3 cluster_health.py --cluster Cluster0 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import AtlasError, emit_human, get_processes_for_cluster, run_atlas  # noqa: E402


KEY_METRICS = {
    "PROCESS_CPU_USER",
    "PROCESS_NORMALIZED_CPU_USER",
    "MEMORY_RESIDENT",
    "OPCOUNTER_QUERY",
    "OPCOUNTER_INSERT",
    "OPCOUNTER_UPDATE",
    "OPCOUNTER_DELETE",
    "CONNECTIONS",
    "QUERY_TARGETING_SCANNED_OBJECTS_PER_RETURNED",
    "QUERY_EXECUTOR_SCANNED_OBJECTS",
}


def fetch_metrics(host_port: str, project_id: str | None, granularity: str, period: str) -> dict:
    args = [
        "metrics", "processes", host_port,
        "--granularity", granularity,
        "--period", period,
    ]
    if project_id:
        args += ["--projectId", project_id]
    data = run_atlas(args)
    return data if isinstance(data, dict) else {}


def latest_value(measurements: list[dict], name: str) -> float | None:
    for m in measurements:
        if m.get("name") == name:
            datapoints = m.get("dataPoints", [])
            for dp in reversed(datapoints):
                v = dp.get("value")
                if v is not None:
                    return v
    return None


def summarize(host_port: str, payload: dict) -> str:
    measurements = payload.get("measurements", [])
    lines = [f"Process: {host_port}\n"]

    cpu = latest_value(measurements, "PROCESS_NORMALIZED_CPU_USER")
    mem = latest_value(measurements, "MEMORY_RESIDENT")
    conn = latest_value(measurements, "CONNECTIONS")
    if cpu is not None:
        lines.append(f"  CPU (normalized user): {cpu:.1f}%")
    if mem is not None:
        lines.append(f"  Resident memory:        {mem / 1024:.0f} MB")
    if conn is not None:
        lines.append(f"  Active connections:     {conn:.0f}")

    lines.append("\n  Op counters (most recent):")
    for op_name, label in [
        ("OPCOUNTER_QUERY", "query "),
        ("OPCOUNTER_INSERT", "insert"),
        ("OPCOUNTER_UPDATE", "update"),
        ("OPCOUNTER_DELETE", "delete"),
    ]:
        v = latest_value(measurements, op_name)
        if v is not None:
            lines.append(f"    {label}: {v:.1f}/s")

    targeting = latest_value(measurements, "QUERY_TARGETING_SCANNED_OBJECTS_PER_RETURNED")
    if targeting is not None:
        flag = "  ⚠️  HIGH (consider indexes)" if targeting > 1000 else ""
        lines.append(f"\n  Query targeting (scanned/returned): {targeting:.1f}{flag}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cluster process metrics summary")
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--projectId", dest="project_id")
    parser.add_argument("--granularity", default="PT1M", help="ISO 8601 (PT10S, PT1M, PT5M, PT1H, P1D)")
    parser.add_argument("--period", default="PT1H", help="ISO 8601 lookback (PT1H, P1D, P7D)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        procs = get_processes_for_cluster(args.cluster, args.project_id)
        if not procs:
            print(f"ERROR: no processes found for cluster `{args.cluster}`", file=sys.stderr)
            return 1
        # Parallelize per-process metric fetches — each is an independent API call.
        from concurrent.futures import ThreadPoolExecutor, as_completed
        all_metrics: dict = {}
        host_ports = [p.get("id") for p in procs if p.get("id")]
        with ThreadPoolExecutor(max_workers=min(8, len(host_ports) or 1)) as ex:
            futures = {
                ex.submit(fetch_metrics, hp, args.project_id, args.granularity, args.period): hp
                for hp in host_ports
            }
            for fut in as_completed(futures):
                hp = futures[fut]
                try:
                    all_metrics[hp] = fut.result()
                except AtlasError as e:
                    print(f"WARN: fetch failed for {hp}: {e}", file=sys.stderr)
        # Render in stable host order
        summaries = [summarize(hp, all_metrics[hp]) for hp in host_ports if hp in all_metrics]
    except AtlasError as e:
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(all_metrics, indent=2))
    else:
        emit_human(f"Cluster Health — {args.cluster}", "\n\n".join(summaries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
