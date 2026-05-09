#!/usr/bin/env python3
"""Export workflows to JSON files — for backup or version-control.

Read-only on the n8n side (only writes local files).

Two backends:
  - CLI: `n8n export:workflow --all/--id ...` — bundles owner/tags
  - API: GET /api/v1/workflows + per-workflow GET — works against cloud

Usage:
  python3 export_workflows.py --output ./backup                        # all, separate files
  python3 export_workflows.py --output ./backup --all-in-one all.json  # all in one file
  python3 export_workflows.py --output ./backup --id <wfid>            # single workflow
  python3 export_workflows.py --backend cli --output ./backup --separate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, resolve_backend, run_n8n_cli  # noqa: E402


def export_via_api(out_dir: Path, workflow_id: str | None, all_in_one: str | None) -> int:
    from _api import list_paginated, request
    out_dir.mkdir(parents=True, exist_ok=True)

    if workflow_id:
        wfs = [request("GET", f"/api/v1/workflows/{workflow_id}")]
    else:
        items = list_paginated("/api/v1/workflows", query={"limit": 250})
        # Each item from list may be summary; fetch full detail per id
        wfs = []
        for item in items:
            wid = item.get("id")
            if wid:
                wfs.append(request("GET", f"/api/v1/workflows/{wid}"))

    if all_in_one:
        path = out_dir / all_in_one
        path.write_text(json.dumps(wfs, indent=2, default=str))
        print(f"Wrote {len(wfs)} workflow(s) → {path}", file=sys.stderr)
    else:
        for wf in wfs:
            wid = wf.get("id", "?")
            name = (wf.get("name") or "unnamed").replace("/", "_").replace(" ", "_")[:80]
            path = out_dir / f"{wid}_{name}.json"
            path.write_text(json.dumps(wf, indent=2, default=str))
        print(f"Wrote {len(wfs)} workflow(s) → {out_dir}/", file=sys.stderr)
    return len(wfs)


def export_via_cli(out_dir: Path, workflow_id: str | None, separate: bool, all_in_one: str | None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if workflow_id:
        out_path = out_dir / f"workflow-{workflow_id}.json"
        run_n8n_cli(["export:workflow", f"--id={workflow_id}", f"--output={out_path}"])
        print(f"Wrote → {out_path}", file=sys.stderr)
        return
    if separate:
        run_n8n_cli(["export:workflow", "--all", "--separate", f"--output={out_dir}"])
        print(f"Wrote separate files → {out_dir}/", file=sys.stderr)
    else:
        out_path = out_dir / (all_in_one or "workflows.json")
        run_n8n_cli(["export:workflow", "--all", f"--output={out_path}"])
        print(f"Wrote → {out_path}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export workflows for backup")
    parser.add_argument("--output", required=True, type=Path,
                        help="Output directory (or file if --all-in-one)")
    parser.add_argument("--id", dest="workflow_id", help="Export only this workflow ID")
    parser.add_argument("--separate", action="store_true",
                        help="One file per workflow (CLI default w/ --all)")
    parser.add_argument("--all-in-one", dest="all_in_one",
                        help="Filename to bundle all workflows into one file (e.g. all.json)")
    parser.add_argument("--backend", choices=["cli", "api"])
    args = parser.parse_args()

    try:
        backend = resolve_backend(args.backend)
        if backend == "api":
            export_via_api(args.output, args.workflow_id, args.all_in_one)
        else:
            export_via_cli(args.output, args.workflow_id, args.separate, args.all_in_one)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
