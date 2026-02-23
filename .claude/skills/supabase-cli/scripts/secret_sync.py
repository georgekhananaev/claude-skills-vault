#!/usr/bin/env python3
"""
Supabase Secret Sync
Syncs environment variables from .env to Supabase remote secrets.

Usage:
  python3 secret_sync.py [--dry-run] [--prefix PREFIX] [--exclude KEY,KEY,...]

Options:
  --dry-run           Show what would be synced without making changes
  --prefix PREFIX     Only sync variables starting with PREFIX (e.g., APP_)
  --exclude KEYS      Comma-separated list of keys to exclude
  --env-file FILE     Path to .env file (default: .env)

Examples:
  python3 secret_sync.py --dry-run
  python3 secret_sync.py --prefix APP_ --exclude APP_DEBUG
  python3 secret_sync.py --prefix STRIPE_
"""

import os
import re
import sys
import subprocess
import argparse
from pathlib import Path

# Variables that should NEVER be synced (Supabase core or dangerous)
ALWAYS_EXCLUDE = {
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWT_SECRET",
    "POSTGRES_DB",
    "POSTGRES_PASSWORD",
    "PGPASSWORD",
    "DATABASE_URL",
    # Common sensitive vars
    "PATH",
    "HOME",
    "USER",
    "SHELL",
    "PWD",
    "TERM",
}


def parse_env_file(filepath: str) -> dict[str, str]:
    """Parse .env file into a dictionary."""
    env = {}
    path = Path(filepath)

    if not path.exists():
        print(f"Error: {filepath} not found")
        sys.exit(1)

    with open(path) as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse KEY=value
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]

                if key and value:
                    env[key] = value

    return env


def filter_secrets(
    env: dict[str, str],
    prefix: str | None = None,
    exclude: set[str] | None = None,
) -> dict[str, str]:
    """Filter environment variables for syncing."""
    exclude = exclude or set()
    exclude = exclude.union(ALWAYS_EXCLUDE)

    filtered = {}
    for key, value in env.items():
        # Skip excluded keys
        if key in exclude:
            continue

        # Apply prefix filter if specified
        if prefix and not key.startswith(prefix):
            continue

        filtered[key] = value

    return filtered


def get_remote_secrets() -> set[str]:
    """Get list of currently set remote secrets."""
    try:
        result = subprocess.run(
            ["supabase", "secrets", "list"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Parse output - format is "NAME  DIGEST"
        secrets = set()
        for line in result.stdout.strip().split("\n"):
            if line and not line.startswith("NAME"):  # Skip header
                parts = line.split()
                if parts:
                    secrets.add(parts[0])
        return secrets
    except subprocess.CalledProcessError as e:
        print(f"Error listing secrets: {e.stderr}")
        return set()
    except FileNotFoundError:
        print("Error: supabase CLI not found. Install with: brew install supabase/tap/supabase")
        sys.exit(1)


def sync_secrets(secrets: dict[str, str], dry_run: bool = False) -> bool:
    """Sync secrets to Supabase."""
    if not secrets:
        print("No secrets to sync.")
        return True

    # Build command arguments
    args = []
    for key, value in secrets.items():
        args.append(f"{key}={value}")

    cmd = ["supabase", "secrets", "set"] + args

    if dry_run:
        print("\nDRY RUN - Would execute:")
        # Mask values in output
        masked_args = [f"{k}=***" for k in secrets.keys()]
        print(f"  supabase secrets set {' '.join(masked_args)}")
        return True

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error syncing secrets: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Sync environment variables to Supabase secrets"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        help="Only sync variables starting with PREFIX",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        help="Comma-separated list of keys to exclude",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env)",
    )
    args = parser.parse_args()

    # Parse exclude list
    exclude = set()
    if args.exclude:
        exclude = set(k.strip() for k in args.exclude.split(","))

    print("=" * 60)
    print("SUPABASE SECRET SYNC")
    print("=" * 60)
    print(f"\nEnv file: {args.env_file}")
    if args.prefix:
        print(f"Prefix filter: {args.prefix}")
    if exclude:
        print(f"User excludes: {', '.join(exclude)}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")

    # Load and filter secrets
    env = parse_env_file(args.env_file)
    secrets = filter_secrets(env, prefix=args.prefix, exclude=exclude)

    print(f"\n{'-' * 60}")
    print(f"Found {len(env)} variables in {args.env_file}")
    print(f"Filtered to {len(secrets)} secrets for sync")

    if not secrets:
        print("\nNo secrets match the filter criteria.")
        return

    # Show what will be synced
    print(f"\n{'-' * 60}")
    print("SECRETS TO SYNC:")
    print(f"{'-' * 60}")

    max_key_len = max(len(k) for k in secrets.keys())
    for key, value in sorted(secrets.items()):
        # Mask value
        if len(value) > 10:
            masked = value[:4] + "***" + value[-3:]
        else:
            masked = "***"
        print(f"  {key.ljust(max_key_len)}  {masked}")

    # Check for existing secrets (to show new vs update)
    existing = get_remote_secrets()
    new_secrets = set(secrets.keys()) - existing
    update_secrets = set(secrets.keys()) & existing

    if new_secrets:
        print(f"\n  NEW: {', '.join(sorted(new_secrets))}")
    if update_secrets:
        print(f"  UPDATE: {', '.join(sorted(update_secrets))}")

    # Confirm and sync
    if not args.dry_run:
        print(f"\n{'-' * 60}")
        response = input("Proceed with sync? [y/N]: ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(0)

    # Perform sync
    success = sync_secrets(secrets, dry_run=args.dry_run)

    print(f"\n{'=' * 60}")
    if success:
        if args.dry_run:
            print("DRY RUN COMPLETE - No changes made")
        else:
            print("✓ SECRET SYNC COMPLETE")
            print("\nNote: If you updated Edge Function secrets, redeploy with:")
            print("  supabase functions deploy <function-name>")
    else:
        print("❌ SECRET SYNC FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
