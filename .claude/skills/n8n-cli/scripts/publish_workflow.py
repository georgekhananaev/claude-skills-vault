#!/usr/bin/env python3
"""Activate or deactivate a workflow — gated.

n8n's REST API uses `/activate` and `/deactivate` endpoints across both 1.x and
2.x. (Earlier versions of this script wrongly tried `/publish` & `/unpublish`,
which don't exist in the public API.)

Aliases: `--action publish` / `--action unpublish` are accepted as synonyms for
`activate` / `deactivate` for users coming from n8n's UI terminology.

Usage:
  # Show current state (read-only)
  python3 publish_workflow.py --id <wfid>

  # Activate (publish)
  python3 publish_workflow.py --id <wfid> --action activate --confirm

  # Deactivate (unpublish)
  python3 publish_workflow.py --id <wfid> --action deactivate --confirm
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, validate_resource_id  # noqa: E402


def get_state(wfid: str) -> dict:
    from _api import request
    validate_resource_id(wfid, "workflow_id")
    return request("GET", f"/api/v1/workflows/{wfid}")


def set_state(wfid: str, action: str) -> dict:
    """Call /activate or /deactivate (both n8n 1.x and 2.x use these names)."""
    from _api import request
    validate_resource_id(wfid, "workflow_id")
    suffix = {
        "activate":   "/activate",
        "deactivate": "/deactivate",
        "publish":    "/activate",     # alias
        "unpublish":  "/deactivate",   # alias
    }.get(action)
    if not suffix:
        raise N8nError(f"set_state: unknown action {action!r}")
    return request("POST", f"/api/v1/workflows/{wfid}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Activate/deactivate a workflow (gated)")
    parser.add_argument("--id", required=True, dest="workflow_id")
    parser.add_argument("--action", choices=["activate", "deactivate", "publish", "unpublish"],
                        help="activate/publish or deactivate/unpublish. Omit to just read state.")
    parser.add_argument("--confirm", action="store_true",
                        help="EXECUTE state change (without this, dry-run only)")
    args = parser.parse_args()

    try:
        wf = get_state(args.workflow_id)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    name = wf.get("name", "?")
    active = wf.get("active")
    print(f"Workflow: {name} (id={args.workflow_id})", file=sys.stderr)
    print(f"  current state: {'ACTIVE' if active else 'INACTIVE'}", file=sys.stderr)

    if not args.action:
        return 0

    is_activate = args.action in ("activate", "publish")
    if is_activate and active:
        print("\nNote: workflow is already active. No-op.", file=sys.stderr)
        return 0
    if not is_activate and active is False:
        print("\nNote: workflow is already inactive. No-op.", file=sys.stderr)
        return 0

    if not args.confirm:
        print(f"\n[DRY RUN] Would {args.action} workflow id={args.workflow_id}.", file=sys.stderr)
        print(f"          Add --confirm to execute.", file=sys.stderr)
        return 0

    try:
        result = set_state(args.workflow_id, args.action)
        print(f"\n✓ {args.action.upper()} succeeded.", file=sys.stderr)
        new_state = result.get("active") if isinstance(result, dict) else None
        if new_state is not None:
            print(f"  new state: {'ACTIVE' if new_state else 'INACTIVE'}", file=sys.stderr)
    except N8nError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
