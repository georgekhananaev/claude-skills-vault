#!/usr/bin/env python3
"""Import a workflow from JSON — gated, dry-run by default.

Safety gates:
  1. Default = dry-run (parses & validates JSON, prints summary, never writes)
  2. Requires `--confirm` to execute
  3. If workflow ID in file collides w/ existing, refuses unless `--overwrite`
     AND `--confirm` are BOTH set
  4. Imported workflow is INACTIVE by default (n8n CLI's --activeState=fromJson
     can preserve, but we default to safe inactive)

Two backends:
  - CLI: `n8n import:workflow --input=<file>` — preserves IDs by default
  - API: POST /api/v1/workflows — generates new ID

Usage:
  # Dry-run: validate JSON
  python3 import_workflow.py --file workflow.json

  # Execute via API (creates new workflow w/ fresh ID)
  python3 import_workflow.py --file workflow.json --confirm

  # Execute via CLI (preserves ID — refuse if exists unless --overwrite)
  python3 import_workflow.py --file workflow.json --backend cli --confirm

  # Force overwrite of existing same-ID workflow (dangerous)
  python3 import_workflow.py --file workflow.json --backend cli --overwrite --confirm
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import os  # noqa: E402

from _common import N8nError, resolve_backend, run_n8n_cli, validate_resource_id  # noqa: E402


def validate_workflow_json(path: Path) -> list[dict]:
    """Parse JSON file. Accept either single workflow dict or array of workflows."""
    if not path.exists():
        raise N8nError(f"INPUT NOT FOUND: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise N8nError(f"INVALID JSON: {path} → {e}")

    workflows = data if isinstance(data, list) else [data]
    for i, wf in enumerate(workflows):
        if not isinstance(wf, dict):
            raise N8nError(f"workflow #{i} is not a JSON object")
        if not wf.get("name"):
            raise N8nError(f"workflow #{i} missing required field `name`")
        if "nodes" not in wf or not isinstance(wf["nodes"], list):
            raise N8nError(f"workflow #{i} ({wf.get('name')}) missing `nodes` array")
    return workflows


def check_existing_via_api(workflow_id: str | None) -> tuple[dict | None, str | None]:
    """Returns (existing_workflow_dict_or_None, error_msg_or_None).

    Distinguishes "doesn't exist" from "couldn't check" — caller MUST treat
    error_msg != None as a hard fail (don't proceed w/ overwrite blindly).
    """
    if not workflow_id:
        return None, None
    if not os.environ.get("N8N_API_URL") or not os.environ.get("N8N_API_KEY"):
        return None, "API creds not set — cannot pre-flight ID collision"
    try:
        validate_resource_id(workflow_id, "workflow_id")
        from _api import request
        wf = request("GET", f"/api/v1/workflows/{workflow_id}")
        return wf, None
    except N8nError as e:
        msg = str(e)
        # 404 means it doesn't exist — that's a clean "no collision" signal
        if "HTTP 404" in msg:
            return None, None
        # Anything else (auth fail, network) — surface as error
        return None, msg


def import_via_api(workflows: list[dict], force_inactive: bool = True) -> list[dict]:
    """POST each workflow. API generates new IDs.

    Note: n8n's POST /api/v1/workflows treats `active` as READ-ONLY — sending
    it returns HTTP 400 "request/body/active is read-only". Newly created
    workflows are always inactive; activation is a separate POST to /activate
    (which we never do here — it's gated behind publish_workflow.py --confirm).

    The `force_inactive` arg is therefore effectively a no-op via the API path
    (workflows ARE inactive after creation). It's kept for symmetry w/ the CLI
    path and as a future-proof signal of intent.
    """
    from _api import request
    # Allowed top-level fields per n8n REST API workflow create body.
    # Explicitly excluding: `active` (read-only on POST), `id` (server-generated),
    # `versionId`, `webhookId`, `triggerCount`, `updatedAt`, `createdAt` — all server-managed.
    ALLOWED = {"name", "nodes", "connections", "settings", "staticData", "tags"}
    created = []
    for wf in workflows:
        body = {k: v for k, v in wf.items() if k in ALLOWED}
        # n8n requires `settings` to be present (even if empty)
        body.setdefault("settings", {})
        new = request("POST", "/api/v1/workflows", body=body)
        created.append(new)
    return created


def import_via_cli(file_path: Path, overwrite: bool) -> str:
    args = ["import:workflow", f"--input={file_path}"]
    # Note: the CLI overwrites by ID by default. We never pass an "overwrite" flag —
    # if the user wants to overwrite, they're acknowledging it via --overwrite at OUR level.
    # If --overwrite is NOT set, we pre-check via API (caller does that).
    out = run_n8n_cli(args, json_out=False)
    return out if isinstance(out, str) else str(out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely import workflow JSON (dry-run by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--backend", choices=["cli", "api"])
    parser.add_argument("--overwrite", action="store_true",
                        help="Allow overwriting existing same-ID workflow (CLI only)")
    parser.add_argument("--allow-active", action="store_true",
                        help="Don't force imported workflows to inactive (API only)")
    parser.add_argument("--confirm", action="store_true",
                        help="EXECUTE (without this, dry-run only)")
    args = parser.parse_args()

    try:
        workflows = validate_workflow_json(args.file)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    print(f"Parsed {len(workflows)} workflow(s) from {args.file}:", file=sys.stderr)
    for wf in workflows[:5]:
        node_count = len(wf.get("nodes", []))
        print(f"  - {wf.get('name', '?')}  (id={wf.get('id', 'n/a')}, nodes={node_count})", file=sys.stderr)
    if len(workflows) > 5:
        print(f"  ... +{len(workflows) - 5} more", file=sys.stderr)

    try:
        backend = resolve_backend(args.backend)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    print(f"\nBackend: {backend}", file=sys.stderr)

    # Pre-flight: check for ID collision (CLI overwrites by ID).
    # If the API check itself fails (auth error etc.), refuse rather than
    # silently treating as "no collision" — that would let CLI overwrite proceed.
    if backend == "cli":
        for wf in workflows:
            wid = wf.get("id")
            if not wid:
                continue
            existing, err = check_existing_via_api(wid)
            if err:
                print(f"⚠️  Pre-flight check for id={wid} failed: {err}", file=sys.stderr)
                if not args.overwrite:
                    print(f"   Refusing — set N8N_API_URL+N8N_API_KEY for pre-flight, "
                          f"or pass --overwrite to skip pre-flight.", file=sys.stderr)
                    return 2
                print(f"   --overwrite set — proceeding without pre-flight (CLI will overwrite by ID).", file=sys.stderr)
                continue
            if existing:
                print(f"⚠️  Workflow id={wid} ({existing.get('name')}) already exists.", file=sys.stderr)
                if not args.overwrite:
                    print(f"   Refusing: pass --overwrite to allow overwriting via CLI import.", file=sys.stderr)
                    return 2
                print(f"   --overwrite set — will overwrite if --confirm.", file=sys.stderr)

    if not args.confirm:
        print("\n[DRY RUN] Add --confirm to execute import.", file=sys.stderr)
        return 0

    try:
        if backend == "api":
            created = import_via_api(workflows, force_inactive=not args.allow_active)
            print(f"\n✓ Created {len(created)} workflow(s):", file=sys.stderr)
            for wf in created:
                print(f"  - id={wf.get('id')} name={wf.get('name')}", file=sys.stderr)
        else:
            out = import_via_cli(args.file, args.overwrite)
            print(out, file=sys.stderr)
            print("\n✓ Import via CLI complete (workflows imported as inactive).", file=sys.stderr)
    except N8nError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
