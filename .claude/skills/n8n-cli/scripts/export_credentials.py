#!/usr/bin/env python3
"""Export credentials — encrypted by default, --decrypted requires explicit confirm.

Two modes:
  Encrypted export (default, safe):
    Credentials exported as the encrypted blobs. Useless without n8n's
    encryption key. Safe to store in normal backups.

  Decrypted export (DANGEROUS):
    Plain-text secret values. Requires --decrypted AND --confirm-secrets.
    Use only when migrating to a new n8n instance w/ a different encryption
    key. Treat output file as a credential vault — never commit, never log.

CLI-only feature (REST API doesn't expose decrypted creds).

Usage:
  # Safe encrypted backup
  python3 export_credentials.py --output ./backup

  # All credentials, encrypted, separate files
  python3 export_credentials.py --output ./backup --separate

  # DECRYPTED (requires both flags + acknowledges risk)
  python3 export_credentials.py --output ./backup/creds.json \\
    --decrypted --confirm-secrets

  # Single credential by ID
  python3 export_credentials.py --output ./backup --id 7
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import N8nError, run_n8n_cli, validate_resource_id  # noqa: E402


# Allowed characters in --output path; rejects shell-meaningful chars even though
# we use argv (defense in depth — n8n CLI may shell-out internally).
_OUTPUT_PATH_RE = re.compile(r"^[A-Za-z0-9_./\-:]+$")


def validate_output_path(p: Path) -> Path:
    """Reject paths with shell-meaningful chars or that escape to system dirs."""
    s = str(p)
    if not _OUTPUT_PATH_RE.match(s):
        raise N8nError(
            f"INVALID --output: contains unsafe chars (got {s!r}).\n"
            f"  Allowed: alphanumerics, slash, dash, underscore, dot, colon."
        )
    # Don't allow writing to common sensitive locations
    forbidden_prefixes = ("/etc/", "/usr/", "/bin/", "/sbin/", "/root/", "/var/log/")
    abs_str = str(p.expanduser().resolve())
    for f in forbidden_prefixes:
        if abs_str.startswith(f):
            raise N8nError(f"INVALID --output: refusing to write to {abs_str} (system path)")
    return p


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export credentials (encrypted by default)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--output", required=True, type=Path,
                        help="Output directory or file")
    parser.add_argument("--id", help="Export only this credential ID")
    parser.add_argument("--separate", action="store_true",
                        help="One file per credential (only w/ --all, not --id)")
    parser.add_argument("--decrypted", action="store_true",
                        help="DANGEROUS — export plain-text secrets. Requires --confirm-secrets.")
    parser.add_argument("--confirm-secrets", action="store_true",
                        help="Acknowledge that decrypted output contains plain-text secrets")
    args = parser.parse_args()

    if args.decrypted and not args.confirm_secrets:
        print("ERROR: --decrypted requires --confirm-secrets to acknowledge the risk.", file=sys.stderr)
        print("       The decrypted file will contain plain-text API keys, passwords, OAuth tokens.", file=sys.stderr)
        print("       NEVER commit it. NEVER log it. Treat it like a password vault.", file=sys.stderr)
        return 2
    if args.confirm_secrets and not args.decrypted:
        print("ERROR: --confirm-secrets w/o --decrypted is meaningless.", file=sys.stderr)
        return 2

    # Validate output path before any side effects
    try:
        validate_output_path(args.output)
        if args.id:
            validate_resource_id(args.id, "credential_id")
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 2

    # Decide if --output is a file or directory based on heuristic:
    # - has suffix → file
    # - --separate → directory
    # - else → directory
    is_file = bool(args.output.suffix) and not args.separate
    if is_file:
        args.output.parent.mkdir(parents=True, exist_ok=True)
    else:
        args.output.mkdir(parents=True, exist_ok=True)

    cli_args = ["export:credentials"]
    if args.id:
        cli_args += [f"--id={args.id}"]
    else:
        cli_args += ["--all"]
    if args.separate:
        cli_args += ["--separate"]
    if args.decrypted:
        cli_args += ["--decrypted"]
    cli_args += [f"--output={args.output}"]

    try:
        out = run_n8n_cli(cli_args)
        print(out, file=sys.stderr)
        if args.decrypted:
            print(f"\n⚠️  DECRYPTED file written: {args.output}", file=sys.stderr)
            print(f"     Contains plain-text secrets. Add to .gitignore. Delete after use.", file=sys.stderr)
        else:
            print(f"\n✓ Encrypted backup written: {args.output}", file=sys.stderr)
    except N8nError as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
