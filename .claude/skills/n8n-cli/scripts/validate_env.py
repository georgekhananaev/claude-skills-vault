#!/usr/bin/env python3
"""Validate n8n skill environment — backend availability, auth, version.

Checks:
  1. Either CLI installed OR API creds set (or both)
  2. API auth works (if creds set) — hits /api/v1/workflows?limit=1
  3. CLI version (if installed)
  4. n8n version (CLI: `n8n --version`; API: from response or settings)

Exits 0 if at least one backend is ready, non-zero otherwise.

Usage:
  python3 validate_env.py
  python3 validate_env.py --backend api    # only check REST API
  python3 validate_env.py --backend cli    # only check CLI
  python3 validate_env.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, emit_missing  # noqa: E402


def check_cli() -> dict:
    info: dict = {"backend": "cli", "available": False}
    if not shutil.which("n8n"):
        info["error"] = "n8n CLI not on PATH"
        info["install_hint"] = "npm install -g n8n  (or `npx n8n <command>`)"
        return info
    info["available"] = True
    info["binary"] = shutil.which("n8n")
    try:
        result = subprocess.run(["n8n", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            info["version"] = result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        info["error"] = f"version probe failed: {e}"
    return info


def check_api() -> dict:
    info: dict = {"backend": "api", "available": False}
    base = os.environ.get("N8N_API_URL")
    key = os.environ.get("N8N_API_KEY")
    if not base:
        info["error"] = "N8N_API_URL not set"
        return info
    if not key:
        info["error"] = "N8N_API_KEY not set"
        return info
    info["base_url"] = base
    try:
        from _api import health_check
        result = health_check()
        info["available"] = bool(result.get("ok"))
        info["health"] = result
    except N8nError as e:
        info["error"] = str(e)
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate n8n backend availability + auth")
    parser.add_argument("--backend", choices=["cli", "api", "both"], default="both")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results: dict = {}
    if args.backend in ("cli", "both"):
        results["cli"] = check_cli()
    if args.backend in ("api", "both"):
        results["api"] = check_api()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("=== n8n environment check ===", file=sys.stderr)
        for backend, info in results.items():
            status = "✓" if info.get("available") else "✗"
            print(f"\n{status} {backend.upper()}:", file=sys.stderr)
            for k, v in info.items():
                if k == "available":
                    continue
                print(f"    {k}: {v}", file=sys.stderr)

    any_ok = any(r.get("available") for r in results.values())
    if not any_ok:
        print("\nNo backend ready. Set N8N_API_URL+N8N_API_KEY or install `n8n` CLI.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
