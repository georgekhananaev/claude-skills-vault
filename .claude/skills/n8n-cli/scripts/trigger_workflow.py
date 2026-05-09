#!/usr/bin/env python3
"""Trigger a workflow execution manually — gated.

⚠️  Important: the n8n PUBLIC REST API does NOT have a "run workflow" endpoint
(despite earlier-version docs implying otherwise). Workflow runs are only
triggerable via:

  1. The CLI: `n8n execute --id=<wfid>` — synchronous, returns output to stdout.
     Self-hosted only. Wrapped here.
  2. The workflow's own Webhook URL (if it has a Webhook trigger node).
     This script can `--print-webhook-hint` to show how to discover it.

This script defaults to CLI mode. If you pass `--backend api`, it errors out
explaining the situation.

Usage:
  # Dry-run (just shows the command)
  python3 trigger_workflow.py --id <wfid>

  # Execute via CLI (self-hosted)
  python3 trigger_workflow.py --id <wfid> --confirm

  # With input data
  python3 trigger_workflow.py --id <wfid> --input data.json --confirm

  # Get webhook URL hint
  python3 trigger_workflow.py --id <wfid> --print-webhook-hint
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, run_n8n_cli, validate_resource_id  # noqa: E402


def trigger_via_cli(wfid: str, input_path: Path | None) -> str:
    validate_resource_id(wfid, "workflow_id")
    args = ["execute", f"--id={wfid}"]
    if input_path:
        if not input_path.exists():
            raise N8nError(f"input file not found: {input_path}")
        args += [f"--input={input_path}"]
    out = run_n8n_cli(args, json_out=False)
    return out if isinstance(out, str) else str(out)


def print_webhook_hint(wfid: str) -> int:
    """Show the user how to find/run the workflow's webhook URL."""
    validate_resource_id(wfid, "workflow_id")
    try:
        from _api import request
        wf = request("GET", f"/api/v1/workflows/{wfid}")
    except N8nError as e:
        print(f"ERROR: couldn't fetch workflow: {e}", file=sys.stderr)
        return 1

    nodes = wf.get("nodes") or []
    webhook_nodes = [n for n in nodes
                     if isinstance(n, dict)
                     and "webhook" in (n.get("type") or "").lower()]
    if not webhook_nodes:
        print(f"Workflow `{wf.get('name', wfid)}` has no Webhook trigger node.", file=sys.stderr)
        print(f"To run it externally: use `--backend cli --confirm` for synchronous CLI exec.", file=sys.stderr)
        return 2

    print(f"Workflow `{wf.get('name', wfid)}` has {len(webhook_nodes)} webhook node(s):", file=sys.stderr)
    for n in webhook_nodes:
        path = (n.get("parameters") or {}).get("path") or n.get("webhookId") or "<path>"
        method = (n.get("parameters") or {}).get("httpMethod") or "POST"
        print(f"  - {n.get('name')}: {method}  <N8N_BASE>/webhook/{path}", file=sys.stderr)
        print(f"    (For test mode: <N8N_BASE>/webhook-test/{path})", file=sys.stderr)
    print(f"\nThe workflow must be ACTIVE for the production webhook to fire.", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Trigger a workflow execution (gated; CLI-only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--id", required=True, dest="workflow_id")
    parser.add_argument("--input", type=Path, help="JSON file w/ input data")
    parser.add_argument("--backend", choices=["cli"],
                        help="Only 'cli' is supported. The public REST API has no run endpoint.")
    parser.add_argument("--print-webhook-hint", action="store_true",
                        help="Show the workflow's webhook URL (if any) instead of executing")
    parser.add_argument("--confirm", action="store_true",
                        help="EXECUTE (without this, dry-run only)")
    args = parser.parse_args()

    if args.print_webhook_hint:
        return print_webhook_hint(args.workflow_id)

    print(f"Plan:", file=sys.stderr)
    cmd = ["n8n", "execute", f"--id={args.workflow_id}"]
    if args.input:
        cmd += [f"--input={args.input}"]
    print(f"  {' '.join(shlex.quote(c) for c in cmd)}", file=sys.stderr)

    print(f"\nReminder: this triggers the workflow against LIVE integrations & credentials.", file=sys.stderr)
    print(f"          Side effects WILL occur — emails sent, API calls made, etc.", file=sys.stderr)
    print(f"\nNote: only --backend cli is supported. The n8n public REST API has no", file=sys.stderr)
    print(f"      run-workflow endpoint. For external triggers, use the workflow's", file=sys.stderr)
    print(f"      webhook URL: `--print-webhook-hint` to discover it.", file=sys.stderr)

    if not args.confirm:
        print(f"\n[DRY RUN] Add --confirm to execute via CLI.", file=sys.stderr)
        return 0

    try:
        out = trigger_via_cli(args.workflow_id, args.input)
        print(out)
        print(f"\n✓ Workflow triggered.", file=sys.stderr)
    except N8nError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
