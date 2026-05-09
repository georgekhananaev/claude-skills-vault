"""Shared utilities for n8n skill — backend selection, refusal guard, env resolution.

Two backends:
  - CLI: `n8n` binary (self-hosted, full surface incl. decrypted creds export, db ops)
  - API: REST API w/ X-N8N-API-KEY header (works for cloud + remote self-hosted)

Backend selection (per-call):
  - User can force via `backend="cli"` or `backend="api"`
  - Auto-detect: prefer API if `N8N_API_URL` + `N8N_API_KEY` set; else CLI

Refusal guard pattern matches `mongodb-atlas-cli`:
  - Build positional list (strip flags + their values)
  - Match forbidden prefix at any chain depth (case-insensitive)
  - Generic destructive token scan across ALL positionals
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from typing import Any

# Hard-blocked tokens — any subcommand or flag containing these is refused.
DESTRUCTIVE_TOKENS = {
    "delete", "drop", "destroy", "remove", "purge", "wipe",
    "reset", "force", "kill", "terminate",
}

# CLI subcommand prefixes that are wholly forbidden.
# n8n CLI is `n8n <verb>:<noun>` style (e.g. `n8n delete:workflow`).
FORBIDDEN_CLI_PREFIXES = (
    # Workflow / credential lifecycle
    ("delete:workflow",),
    ("delete:credentials",),
    # User management — auth changes
    ("user-management:reset",),
    ("user-management:promote",),
    ("user-management:revoke",),
    # MFA / LDAP — security surface
    ("mfa:disable",),
    ("ldap:reset",),
    # Database — destructive
    ("db:revert",),
    ("db:drop",),
    # Encryption — rotation can break credentials
    ("encryption-key:reset",),
    ("encryption-key:rotate",),
    # License — billing-sensitive
    ("license:clear",),
    # Execution data — destroys history
    ("executionData:prune",),
    ("executionData:delete",),
)

# API endpoints that are wholly forbidden.
# Format: (HTTP_METHOD, path_prefix). Path prefix matches start of URL path.
FORBIDDEN_API_PATHS = (
    # Workflows — destructive + bulk-mutation
    ("DELETE", "/api/v1/workflows/"),
    ("PUT",    "/api/v1/workflows/"),       # full replacement; treat as destructive
    ("PATCH",  "/api/v1/workflows/"),       # mutation incl. activation
    # Credentials
    ("DELETE", "/api/v1/credentials/"),
    ("POST",   "/api/v1/credentials"),      # secret injection (creation)
    ("PUT",    "/api/v1/credentials/"),
    ("PATCH",  "/api/v1/credentials/"),
    # Executions
    ("DELETE", "/api/v1/executions/"),
    # Users
    ("DELETE", "/api/v1/users/"),
    ("POST",   "/api/v1/users"),
    ("PATCH",  "/api/v1/users/"),
    ("PUT",    "/api/v1/users/"),
    # Projects / tags / variables
    ("DELETE", "/api/v1/projects/"),
    ("DELETE", "/api/v1/tags/"),
    ("DELETE", "/api/v1/variables/"),
    # Source-control
    ("POST",   "/api/v1/source-control/pull"),
    ("POST",   "/api/v1/source-control/push"),
    ("POST",   "/api/v1/source-control/disconnect"),
    ("DELETE", "/api/v1/source-control"),
    # License
    ("POST",   "/api/v1/license"),
    ("DELETE", "/api/v1/license"),
)


# Strict regex for resource IDs interpolated into URL paths. Prevents path traversal
# (1/../users) and injection. n8n IDs are UUIDs, slugs, or short alphanumeric strings.
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def validate_resource_id(value: str, kind: str = "id") -> str:
    """Validate a workflow/execution/credential ID. Raises N8nError on bad input."""
    if not isinstance(value, str) or not value:
        raise N8nError(f"INVALID: {kind} must be non-empty string (got {value!r})")
    if not _ID_RE.match(value):
        raise N8nError(
            f"INVALID: {kind} {value!r} contains unsafe characters or is too long.\n"
            f"  Allowed: alphanumerics, underscore, hyphen (max 64 chars).\n"
            f"  Blocked: slashes, dots, traversal sequences, query strings, etc."
        )
    return value


class N8nError(RuntimeError):
    pass


def refuse_if_destructive_cli(args: list[str]) -> None:
    """Refuse destructive CLI invocations. Raises N8nError on hit.

    Pattern (matches mongodb-atlas-cli):
      1. Strip leading 'n8n' if present.
      2. Drop flags (--foo and -f) and their values to build a positional list.
      3. Match forbidden prefix anywhere in the positional chain (case-insensitive).
      4. Generic destructive token scan across ALL positionals.

    This blocks bypasses like `["--verbose", "delete:workflow"]` or
    `["-q", "executionData:prune"]` that the previous head-only check missed.
    """
    parts = list(args)
    if parts and parts[0].lower() == "n8n":
        parts = parts[1:]

    # Build positional list — drop flags + their values.
    # CRITICAL: n8n subcommands use the `verb:noun` form. If the token AFTER a
    # flag contains a `:`, treat it as a subcommand (positional), NOT as the
    # flag's value. This blocks bypasses like `["--verbose", "delete:workflow"]`
    # where a boolean flag's "value" is actually the next subcommand.
    def looks_like_subcommand(s: str) -> bool:
        return ":" in s and not s.startswith("-")

    positional: list[str] = []
    skip_next = False
    for i, p in enumerate(parts):
        if skip_next:
            skip_next = False
            continue
        if p.startswith("--"):
            # --flag=value : just a flag (no separate value)
            # --flag <subcmd> : subcmd is NOT a value, treat as positional
            # --flag <value> : value is consumed
            if (
                "=" not in p
                and i + 1 < len(parts)
                and not parts[i + 1].startswith("-")
                and not looks_like_subcommand(parts[i + 1])
            ):
                skip_next = True
            continue
        if p.startswith("-") and len(p) >= 2 and not p[1:].lstrip("-").isdigit():
            # Short flag like -q, -h
            if (
                len(p) == 2
                and i + 1 < len(parts)
                and not parts[i + 1].startswith("-")
                and not looks_like_subcommand(parts[i + 1])
            ):
                skip_next = True
            continue
        positional.append(p)

    if not positional:
        return

    pos_lower = [p.lower() for p in positional]

    # Check forbidden prefixes — match at any chain position
    for prefix in FORBIDDEN_CLI_PREFIXES:
        prefix_lower = tuple(p.lower() for p in prefix)
        # Check whether the prefix appears starting anywhere in pos_lower
        plen = len(prefix_lower)
        for i in range(len(pos_lower) - plen + 1):
            if tuple(pos_lower[i : i + plen]) == prefix_lower:
                raise N8nError(
                    f"REFUSED: `n8n {' '.join(positional)}` is a destructive op blocked by this skill.\n"
                    f"  Matched forbidden prefix: {' '.join(prefix)}\n"
                    f"  Run it manually if you intend to."
                )

    # Generic destructive token scan across ALL positionals
    for tok in positional:
        # n8n verb:noun → check both halves
        for sub in tok.lower().replace(":", " ").split():
            if sub in DESTRUCTIVE_TOKENS:
                raise N8nError(
                    f"REFUSED: `n8n {' '.join(positional)}` contains destructive token `{sub}`.\n"
                    f"  This skill never runs delete/drop/reset/force/kill ops."
                )


def refuse_if_destructive_api(method: str, path: str) -> None:
    """Refuse destructive API calls.

    Path-prefix match is case-sensitive on path (n8n paths are lowercase by convention)
    but method comparison is upper-cased.
    """
    method_upper = method.upper()
    for fmethod, fpath in FORBIDDEN_API_PATHS:
        if method_upper == fmethod and path.startswith(fpath):
            raise N8nError(
                f"REFUSED: `{method_upper} {path}` is destructive — blocked.\n"
                f"  Use the n8n UI or REST client directly if you intend to."
            )


def resolve_backend(explicit: str | None = None) -> str:
    """Pick CLI or API based on explicit arg, env vars, or availability.

    Returns 'cli' or 'api'. Raises N8nError if neither is available.
    """
    if explicit:
        if explicit not in ("cli", "api"):
            raise N8nError(f"--backend must be 'cli' or 'api' (got: {explicit!r})")
        return explicit

    # Prefer API if creds present (cloud-friendly, faster for read ops)
    if os.environ.get("N8N_API_URL") and os.environ.get("N8N_API_KEY"):
        return "api"

    # Fall back to CLI if installed
    if shutil.which("n8n"):
        return "cli"

    raise N8nError(
        "MISSING: no n8n backend available.\n"
        "ASK_USER: set N8N_API_URL + N8N_API_KEY (REST API) "
        "or install n8n CLI (`npm install -g n8n` for self-hosted ops)."
    )


def run_n8n_cli(args: list[str], json_out: bool = False, check: bool = True) -> Any:
    """Run `n8n <args>`. Refuses destructive ops. Returns raw stdout (or parsed JSON)."""
    if not shutil.which("n8n"):
        raise N8nError(
            "MISSING: n8n CLI binary.\n"
            "Install: `npm install -g n8n` or `npx n8n <command>`."
        )
    refuse_if_destructive_cli(args)

    cmd = ["n8n", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip()
        if check:
            raise N8nError(
                f"n8n CLI failed (exit {proc.returncode}):\n  "
                f"{' '.join(shlex.quote(c) for c in cmd)}\n  {msg}"
            )
        return None

    if json_out:
        import json
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return proc.stdout
    return proc.stdout


def emit_human(label: str, payload: Any) -> None:
    """Pretty-print payload to stderr w/ a label."""
    import json
    import sys
    print(f"\n=== {label} ===", file=sys.stderr)
    if isinstance(payload, (dict, list)):
        print(json.dumps(payload, indent=2, default=str)[:4000], file=sys.stderr)
    else:
        print(str(payload)[:4000], file=sys.stderr)


def emit_missing(var: str, hint: str, location: str = "") -> None:
    """Emit MISSING/ASK_USER block in the standard format."""
    import sys
    print(f"MISSING: {var}", file=sys.stderr)
    print(f"ASK_USER: {hint}", file=sys.stderr)
    if location:
        print(f"LOCATION: {location}", file=sys.stderr)
