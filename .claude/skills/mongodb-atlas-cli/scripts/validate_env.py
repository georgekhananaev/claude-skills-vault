#!/usr/bin/env python3
"""Validate Atlas CLI install + auth + project access.

Checks (in order):
  1. `atlas` binary present on PATH
  2. CLI version >= 1.20
  3. Auth resolves (env vars, profile, or login session)
  4. Project ID resolves
  5. `atlas clusters list` succeeds (read perm sanity check)

Exits 0 if ready, non-zero w/ structured MISSING:/ASK_USER: lines for Claude to parse.

Usage:
  python3 validate_env.py
  python3 validate_env.py --install   # offers to brew-install if missing
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

MIN_VERSION = (1, 20, 0)


def _run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _emit_missing(var: str, hint: str, location: str) -> None:
    print(f"MISSING: {var}", file=sys.stderr)
    print(f"ASK_USER: {hint}", file=sys.stderr)
    print(f"LOCATION: {location}", file=sys.stderr)


def check_binary(install: bool) -> bool:
    if shutil.which("atlas"):
        return True
    print("MISSING: atlas CLI binary", file=sys.stderr)
    sys_name = platform.system()
    if sys_name == "Darwin":
        cmd = "brew install mongodb-atlas"
    elif sys_name == "Linux":
        cmd = "See https://www.mongodb.com/docs/atlas/cli/current/install-atlas-cli/ (apt/yum/docker)"
    else:
        cmd = "Download from https://www.mongodb.com/try/download/atlascli"
    print(f"INSTALL_HINT: {cmd}", file=sys.stderr)

    if install and sys_name == "Darwin" and shutil.which("brew"):
        print("Running: brew install mongodb-atlas", file=sys.stderr)
        result = _run(["brew", "install", "mongodb-atlas"])
        if result.returncode == 0 and shutil.which("atlas"):
            return True
        print(result.stderr, file=sys.stderr)
    return False


def parse_version(text: str) -> tuple[int, int, int] | None:
    # `atlas --version` → "atlascli version: 1.41.0"
    for line in text.splitlines():
        line = line.strip().lower()
        if "version" in line:
            for token in line.replace(":", " ").split():
                parts = token.split(".")
                if len(parts) >= 3 and all(p.split("-")[0].isdigit() for p in parts[:3]):
                    return (
                        int(parts[0]),
                        int(parts[1]),
                        int(parts[2].split("-")[0]),
                    )
    return None


def check_version() -> bool:
    result = _run(["atlas", "--version"])
    if result.returncode != 0:
        print(f"ERROR: atlas --version failed: {result.stderr}", file=sys.stderr)
        return False
    ver = parse_version(result.stdout + result.stderr)
    if not ver:
        print(f"WARN: could not parse atlas version from: {result.stdout!r}", file=sys.stderr)
        return True
    if ver < MIN_VERSION:
        print(
            f"WARN: atlas {ver[0]}.{ver[1]}.{ver[2]} < recommended {MIN_VERSION[0]}.{MIN_VERSION[1]}.{MIN_VERSION[2]}",
            file=sys.stderr,
        )
    print(f"OK: atlas version {ver[0]}.{ver[1]}.{ver[2]}", file=sys.stderr)
    return True


def check_auth() -> bool:
    pub = os.environ.get("MONGODB_ATLAS_PUBLIC_API_KEY")
    priv = os.environ.get("MONGODB_ATLAS_PRIVATE_API_KEY")
    project = os.environ.get("MONGODB_ATLAS_PROJECT_ID")

    if pub and priv:
        print("OK: API key auth via env vars", file=sys.stderr)
    else:
        # Fall back to profile / login session — try a no-op auth check
        result = _run(["atlas", "auth", "whoami"])
        if result.returncode != 0:
            _emit_missing(
                "MONGODB_ATLAS_PUBLIC_API_KEY",
                "Atlas API key pair (public + private). Or run `atlas auth login`.",
                "Atlas UI → Project Settings → Access Manager → API Keys → Create API Key",
            )
            _emit_missing(
                "MONGODB_ATLAS_PRIVATE_API_KEY",
                "Private half of the API key pair (shown only at creation).",
                "Atlas UI → Project Settings → Access Manager → API Keys → Create API Key",
            )
            return False
        print(f"OK: auth via profile/login: {result.stdout.strip()}", file=sys.stderr)

    if not project:
        # Project may also be set in profile config — check via clusters list later
        print("INFO: MONGODB_ATLAS_PROJECT_ID not set; relying on profile default", file=sys.stderr)
    else:
        if len(project) != 24 or not all(c in "0123456789abcdefABCDEF" for c in project):
            print(
                f"WARN: MONGODB_ATLAS_PROJECT_ID={project} doesn't look like a 24-hex string",
                file=sys.stderr,
            )
    return True


def check_project_access() -> bool:
    result = _run(["atlas", "clusters", "list", "--output", "json"])
    if result.returncode != 0:
        if "PROJECT_ID" in result.stderr.upper() or "project" in result.stderr.lower():
            _emit_missing(
                "MONGODB_ATLAS_PROJECT_ID",
                "24-hex project ID. Find it in Atlas UI URL: /v2/<project_id>/...",
                "Atlas UI → Project Settings → General → Project ID",
            )
        else:
            print(f"ERROR: atlas clusters list failed:\n{result.stderr}", file=sys.stderr)
        return False
    try:
        data = json.loads(result.stdout)
        clusters = data.get("results", data) if isinstance(data, dict) else data
        names = [c.get("name", "?") for c in clusters] if isinstance(clusters, list) else []
        print(f"OK: project access — {len(names)} cluster(s): {', '.join(names) or '(none)'}", file=sys.stderr)
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        print(f"WARN: clusters list returned non-JSON: {e}", file=sys.stderr)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Atlas CLI environment")
    parser.add_argument("--install", action="store_true", help="Attempt brew install if missing (macOS only)")
    args = parser.parse_args()

    if not check_binary(args.install):
        return 2
    if not check_version():
        return 3
    if not check_auth():
        return 4
    if not check_project_access():
        return 5
    print("READY", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
