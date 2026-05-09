#!/usr/bin/env python3
"""Generate / fetch the n8n security audit report.

Read-only. Wraps the n8n CLI `n8n audit` command (self-hosted only) — that
produces a markdown audit covering credentials, database, filesystem, nodes,
and instance settings.

API-side equivalent: GET /api/v1/audit (n8n 1.x+).

Usage:
  python3 audit_log.py                            # API form
  python3 audit_log.py --backend cli              # CLI form (richer markdown)
  python3 audit_log.py --categories credentials,nodes
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, resolve_backend, run_n8n_cli  # noqa: E402


def fetch_via_api(categories: list[str] | None) -> dict:
    from _api import request
    body: dict = {}
    if categories:
        body["additionalOptions"] = {"categories": categories}
    return request("POST", "/api/v1/audit", body=body)


def fetch_via_cli(categories: list[str] | None) -> str:
    args = ["audit"]
    if categories:
        args += ["--categories", ",".join(categories)]
    out = run_n8n_cli(args, json_out=False)
    return out if isinstance(out, str) else str(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="n8n security audit (read-only)")
    parser.add_argument("--backend", choices=["cli", "api"])
    parser.add_argument("--categories",
                        help="Comma-separated subset: credentials,database,filesystem,nodes,instance")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cats = [c.strip() for c in (args.categories or "").split(",") if c.strip()] or None

    try:
        backend = resolve_backend(args.backend)
        if backend == "api":
            result = fetch_via_api(cats)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                print("\n=== n8n Audit (API) ===\n", file=sys.stderr)
                print(json.dumps(result, indent=2, default=str), file=sys.stderr)
        else:
            result = fetch_via_cli(cats)
            print(result)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
