#!/usr/bin/env python3
"""
Supabase Secrets Manager
Interactive management of Supabase remote secrets.

Usage:
  python3 manage_secrets.py <command> [options]

Commands:
  list              List all remote secrets
  get <KEY>         Get value of a specific secret (masked)
  set <KEY>=<VALUE> Set a secret value
  unset <KEY>       Remove a secret (requires --force)

Options:
  --force           Required for unset operations
  --show-values     Show actual values (use with caution)

Examples:
  python3 manage_secrets.py list
  python3 manage_secrets.py set STRIPE_KEY=sk_live_xxx
  python3 manage_secrets.py unset OLD_KEY --force
"""

import os
import sys
import subprocess
import argparse


def run_supabase(args: list[str], capture: bool = True) -> tuple[bool, str, str]:
    """Run a supabase CLI command."""
    try:
        result = subprocess.run(
            ["supabase"] + args,
            capture_output=capture,
            text=True,
            check=False,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except FileNotFoundError:
        print("Error: supabase CLI not found")
        print("Install with: brew install supabase/tap/supabase")
        sys.exit(1)


def list_secrets(show_values: bool = False):
    """List all remote secrets."""
    success, stdout, stderr = run_supabase(["secrets", "list"])

    if not success:
        print(f"Error: {stderr}")
        sys.exit(1)

    print("=" * 60)
    print("REMOTE SECRETS")
    print("=" * 60)

    lines = stdout.strip().split("\n")
    if not lines or not lines[0]:
        print("\nNo secrets found.")
        return

    # Parse and display
    secrets = []
    for line in lines:
        if not line or line.startswith("NAME"):  # Skip header
            continue
        parts = line.split()
        if len(parts) >= 2:
            secrets.append({"name": parts[0], "digest": parts[1]})

    if not secrets:
        print("\nNo secrets found.")
        return

    print(f"\n{'NAME'.ljust(30)} {'DIGEST'}")
    print("-" * 60)
    for secret in secrets:
        digest = secret["digest"][:20] + "..." if len(secret["digest"]) > 20 else secret["digest"]
        print(f"{secret['name'].ljust(30)} {digest}")

    print(f"\nTotal: {len(secrets)} secrets")


def set_secret(key_value: str):
    """Set a secret value."""
    if "=" not in key_value:
        print("Error: Format must be KEY=value")
        sys.exit(1)

    key, _, value = key_value.partition("=")
    key = key.strip()
    value = value.strip()

    if not key or not value:
        print("Error: Both key and value are required")
        sys.exit(1)

    # Validate key format
    if not key.replace("_", "").isalnum():
        print("Error: Key must be alphanumeric with underscores only")
        sys.exit(1)

    print(f"Setting secret: {key}")

    success, stdout, stderr = run_supabase(["secrets", "set", f"{key}={value}"])

    if success:
        print(f"✓ Secret '{key}' set successfully")
        print("\nNote: If this is used by Edge Functions, redeploy them:")
        print("  supabase functions deploy <function-name>")
    else:
        print(f"❌ Error: {stderr}")
        sys.exit(1)


def unset_secret(key: str, force: bool = False):
    """Remove a secret."""
    if not force:
        print("Error: Removing secrets requires --force flag")
        print("Usage: python3 manage_secrets.py unset KEY --force")
        sys.exit(1)

    key = key.strip()

    print(f"⚠️  Removing secret: {key}")
    print("This action cannot be undone.")

    # Confirm
    response = input("Are you sure? [y/N]: ")
    if response.lower() != "y":
        print("Aborted.")
        sys.exit(0)

    success, stdout, stderr = run_supabase(["secrets", "unset", key])

    if success:
        print(f"✓ Secret '{key}' removed")
        print("\nNote: If this was used by Edge Functions, redeploy them:")
        print("  supabase functions deploy <function-name>")
    else:
        print(f"❌ Error: {stderr}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Manage Supabase remote secrets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 manage_secrets.py list
  python3 manage_secrets.py set STRIPE_KEY=sk_live_xxx
  python3 manage_secrets.py unset OLD_KEY --force
        """,
    )

    parser.add_argument(
        "command",
        choices=["list", "get", "set", "unset"],
        help="Command to execute",
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Command arguments",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Required for destructive operations",
    )
    parser.add_argument(
        "--show-values",
        action="store_true",
        help="Show actual secret values (use with caution)",
    )

    args = parser.parse_args()

    if args.command == "list":
        list_secrets(show_values=args.show_values)

    elif args.command == "get":
        if not args.args:
            print("Error: get requires a key name")
            print("Usage: python3 manage_secrets.py get KEY")
            sys.exit(1)
        # Supabase CLI doesn't have a get command, list shows all
        print("Note: Supabase CLI only supports listing all secrets")
        print("Individual secret values cannot be retrieved.")
        list_secrets()

    elif args.command == "set":
        if not args.args:
            print("Error: set requires KEY=value")
            print("Usage: python3 manage_secrets.py set KEY=value")
            sys.exit(1)
        set_secret(args.args[0])

    elif args.command == "unset":
        if not args.args:
            print("Error: unset requires a key name")
            print("Usage: python3 manage_secrets.py unset KEY --force")
            sys.exit(1)
        unset_secret(args.args[0], force=args.force)


if __name__ == "__main__":
    main()
