"""Shared utilities for atlas CLI wrapper scripts.

Centralizes:
  - Subprocess invocation w/ JSON parsing
  - Destructive-op refusal guard
  - Process/host resolution per cluster
  - Pretty-print helpers

Import as:  from _common import run_atlas, refuse_if_destructive, get_process_for_cluster
"""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any

# Hard-blocked tokens — any atlas subcommand or flag containing these is refused.
DESTRUCTIVE_TOKENS = {
    "delete", "drop", "terminate", "pause", "restore",
    "kill", "force", "destroy", "remove", "purge",
}

# Subcommand prefixes that are allowed to perform additive writes
# (still gated behind --confirm in caller).
ALLOWED_WRITE_PREFIXES = (
    ("clusters", "indexes", "create"),
)

# Subcommands that are wholly forbidden — even read-only mode of these touches sensitive surface.
# Comparison is case-insensitive (Atlas CLI subcommands are case-sensitive in practice
# but defense-in-depth covers any future plugin layer that normalizes case).
FORBIDDEN_PREFIXES = (
    # Cluster lifecycle
    ("clusters", "delete"),
    ("clusters", "terminate"),
    ("clusters", "pause"),
    ("clusters", "update"),                 # tier change, scaling, encryption, etc.
    ("clusters", "upgrade"),
    ("clusters", "indexes", "delete"),
    # Backup / restore
    ("backups", "restore"),
    ("backups", "restores", "start"),
    ("backups", "snapshots", "delete"),
    ("backups", "compliancePolicy", "update"),
    ("backups", "schedule", "update"),
    ("backups", "schedule", "delete"),
    # Auth changes
    ("dbusers", "create"),
    ("dbusers", "update"),
    ("dbusers", "delete"),
    # Network changes
    ("networking", "peering", "create"),
    ("networking", "peering", "delete"),
    ("networking", "peering", "update"),
    ("networking", "containers", "create"),
    ("networking", "containers", "delete"),
    ("privateEndpoints", "create"),
    ("privateEndpoints", "delete"),
    ("privateEndpoints", "interfaces", "create"),
    ("privateEndpoints", "interfaces", "delete"),
    ("accessLists", "create"),
    ("accessLists", "delete"),
    ("accessLists", "update"),
    # Project / org / team
    ("projects", "delete"),
    ("projects", "users", "delete"),
    ("projects", "apiKeys", "create"),
    ("projects", "apiKeys", "delete"),
    ("teams", "create"),
    ("teams", "delete"),
    ("teams", "update"),
    ("organizations", "delete"),
    ("organizations", "apiKeys", "create"),
    ("organizations", "apiKeys", "delete"),
    # Search index lifecycle (deletes only — creates handled by atlas_search_create.py)
    ("clusters", "search", "indexes", "delete"),
    ("clusters", "search", "indexes", "update"),
    # Online archive
    ("clusters", "onlineArchives", "delete"),
    # Alert config (operational settings)
    ("alerts", "settings", "delete"),
    # Federated DB
    ("dataFederation", "delete"),
    # Search nodes
    ("clusters", "searchNodes", "delete"),
    ("clusters", "searchNodes", "update"),
)


class AtlasError(RuntimeError):
    pass


def refuse_if_destructive(args: list[str]) -> None:
    """Raise AtlasError if args target a destructive op.

    Catches:
      * Any FORBIDDEN_PREFIXES match
      * Any token matching DESTRUCTIVE_TOKENS, unless arg is a flag VALUE (after --flag)
        and not a subcommand position.
    """
    # Strip leading "atlas" if present
    parts = list(args)
    if parts and parts[0] == "atlas":
        parts = parts[1:]

    # Drop flags + their values to focus on positional subcommand chain
    positional: list[str] = []
    skip_next = False
    for i, p in enumerate(parts):
        if skip_next:
            skip_next = False
            continue
        if p.startswith("--"):
            if "=" not in p and i + 1 < len(parts) and not parts[i + 1].startswith("-"):
                skip_next = True
            continue
        if p.startswith("-") and len(p) == 2:
            # short flag — its value (if any) follows
            if i + 1 < len(parts) and not parts[i + 1].startswith("-"):
                skip_next = True
            continue
        positional.append(p)

    # Check FORBIDDEN_PREFIXES (case-insensitive — defense in depth)
    pos_lower = [p.lower() for p in positional]
    for prefix in FORBIDDEN_PREFIXES:
        prefix_lower = tuple(p.lower() for p in prefix)
        if len(pos_lower) >= len(prefix) and tuple(pos_lower[: len(prefix)]) == prefix_lower:
            raise AtlasError(
                f"REFUSED: `atlas {' '.join(positional)}` is a destructive op blocked by this skill.\n"
                f"  Matched forbidden prefix: {' '.join(prefix)}\n"
                f"  Run it manually in Atlas UI or via `atlas` directly if you intend to."
            )

    # Generic destructive token scan in subcommand chain
    for tok in positional:
        if tok.lower() in DESTRUCTIVE_TOKENS:
            raise AtlasError(
                f"REFUSED: subcommand contains destructive token `{tok}`.\n"
                f"  Full chain: atlas {' '.join(positional)}\n"
                f"  This skill never runs delete/drop/restore/terminate/pause/kill ops."
            )


def run_atlas(args: list[str], json_out: bool = True, check: bool = True) -> Any:
    """Run `atlas <args>`. Refuses destructive ops. Returns parsed JSON or raw stdout.

    Args:
      args: subcommand chain + flags, e.g. ["clusters", "list"]
      json_out: append --output json and parse result
      check: raise on non-zero exit
    """
    if not shutil.which("atlas"):
        raise AtlasError(
            "MISSING: atlas CLI binary.\n"
            "ASK_USER: install via `brew install mongodb-atlas` (macOS) "
            "or see https://www.mongodb.com/docs/atlas/cli/current/install-atlas-cli/"
        )

    refuse_if_destructive(args)

    cmd = ["atlas", *args]
    if json_out and "--output" not in args and "-o" not in args:
        cmd += ["--output", "json"]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip()
        if check:
            raise AtlasError(f"atlas command failed (exit {proc.returncode}):\n  {' '.join(shlex.quote(c) for c in cmd)}\n  {msg}")
        return None

    if not json_out:
        return proc.stdout

    text = proc.stdout.strip()
    if not text:
        return []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Some commands return NDJSON or non-JSON despite --output json
        return text


def get_processes_for_cluster(cluster_name: str, project_id: str | None = None) -> list[dict]:
    """Return list of processes (mongod/mongos) for the given cluster name.

    Atlas dedicated clusters expose user-facing aliases like
    `<ClusterName>-shard-00-00.<host>:27017` in the `userAlias` field, while the
    machine `replicaSetName` is opaque (`atlas-<rand>-shard-0`). We match against
    userAlias preferentially, then fall back to checking the cluster's connection
    string hosts.
    """
    args = ["processes", "list"]
    if project_id:
        args += ["--projectId", project_id]
    data = run_atlas(args)
    procs = data.get("results", data) if isinstance(data, dict) else data
    if not isinstance(procs, list):
        return []

    cn_lower = cluster_name.lower()

    # Pass 1: legacy hosting where userAlias prefixes w/ cluster name (M0/serverless)
    matched = [
        p for p in procs
        if (p.get("userAlias") or "").lower().startswith(cn_lower + "-")
        or (p.get("userAlias") or "").lower() == cn_lower
    ]
    if matched:
        return matched

    # Pass 2: resolve via `clusters describe` connection string + SRV record
    try:
        describe_args = ["clusters", "describe", cluster_name]
        if project_id:
            describe_args += ["--projectId", project_id]
        cluster = run_atlas(describe_args)
        if isinstance(cluster, dict):
            cs_obj = cluster.get("connectionStrings") or {}
            standard = cs_obj.get("standard", "") or ""
            standard_srv = cs_obj.get("standardSrv", "") or ""
            hosts: set[str] = set()
            # standard: mongodb://h1:p,h2:p,h3:p/?...
            if standard:
                body = standard.split("//", 1)[-1].split("/", 1)[0]
                for h in body.split(","):
                    host = h.split(":", 1)[0].strip().lower()
                    if host:
                        hosts.add(host)
            # SRV identifies a domain — extract bare host: mongodb+srv://itinerarydev.<rest>
            if standard_srv:
                srv_host = standard_srv.split("//", 1)[-1].split("/", 1)[0].strip().lower()
                if srv_host:
                    hosts.add(srv_host)
            if hosts:
                matched = [
                    p for p in procs
                    if (p.get("userAlias") or "").lower() in hosts
                    or (p.get("hostname") or "").lower() in hosts
                    or (p.get("id", "").split(":", 1)[0]).lower() in hosts
                ]
                if matched:
                    return matched
    except AtlasError:
        pass

    # Note: dedicated Atlas clusters use opaque replicaSetName (atlas-<rand>-shard-N),
    # so a regex match against the user-facing cluster name won't help. We rely on
    # passes 1 (userAlias) and 2 (connection-string hosts).
    return []


def resolve_project_id(explicit: str | None = None) -> str | None:
    """Get project id from arg → env → atlas profile config (in that order)."""
    import os
    if explicit:
        return explicit
    env = os.environ.get("MONGODB_ATLAS_PROJECT_ID")
    if env:
        return env
    # Fall back to CLI profile
    try:
        result = subprocess.run(
            ["atlas", "config", "describe", "default"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("project_id"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return None


def primary_process(cluster_name: str, project_id: str | None = None) -> str:
    """Return one processName (host:port) for the cluster — preferring shard-00.

    Used as the --processName arg for performanceAdvisor commands.
    """
    procs = get_processes_for_cluster(cluster_name, project_id)
    if not procs:
        raise AtlasError(
            f"No processes found for cluster `{cluster_name}`.\n"
            f"Verify cluster name w/: atlas clusters list"
        )
    # Prefer shard-00-00 (primary of first shard) if present
    for p in procs:
        rs = p.get("replicaSetName", "")
        host_id = p.get("id") or ""
        if "shard-00" in rs and "00-00" in host_id:
            return host_id
    return procs[0].get("id", "")


def emit_human(label: str, payload: Any) -> None:
    """Pretty-print payload to stderr w/ a label, leaving stdout for JSON."""
    print(f"\n=== {label} ===", file=sys.stderr)
    if isinstance(payload, (dict, list)):
        print(json.dumps(payload, indent=2)[:4000], file=sys.stderr)
    else:
        print(str(payload)[:4000], file=sys.stderr)
