#!/usr/bin/env python3
"""
Environment Validator for Supabase
Checks .env for required Supabase credentials and validates their format.

Usage:
  python3 validate_env.py [--check-connection] [--env-file .env]

Options:
  --check-connection  Test actual connection to Supabase (requires network)
  --env-file FILE     Path to env file (default: .env)
"""

import os
import re
import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse


# Required environment variables with validation rules
REQUIRED_VARS = {
    "SUPABASE_URL": {
        "description": "Supabase Project URL",
        "pattern": r"^https://[a-z0-9]+\.supabase\.co$",
        "location": "Dashboard > Project Settings > API > Project URL",
        "example": "https://xxxxx.supabase.co",
    },
    "SUPABASE_ANON_KEY": {
        "description": "Supabase Anonymous/Public Key",
        "pattern": r"^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$",
        "location": "Dashboard > Project Settings > API > anon public key",
        "example": "eyJhbGciOiJIUzI1NiIs...",
    },
}

OPTIONAL_VARS = {
    "SUPABASE_SERVICE_ROLE_KEY": {
        "description": "Supabase Service Role Key (admin access)",
        "pattern": r"^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$",
        "location": "Dashboard > Project Settings > API > service_role key",
        "example": "eyJhbGciOiJIUzI1NiIs...",
        "warning": "SECURITY: Never expose in client-side code",
    },
    "POSTGRES_DB": {
        "description": "Direct PostgreSQL Connection URL",
        "pattern": r"^postgresql://[^:]+:[^@]+@[^/]+/\w+",
        "location": "Dashboard > Database > Connection String > URI",
        "example": "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres",
    },
}


def parse_env_file(filepath: str) -> dict[str, str]:
    """Parse .env file into a dictionary."""
    env = {}
    path = Path(filepath)

    if not path.exists():
        return env

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

                env[key] = value

    return env


def validate_var(name: str, value: str, config: dict) -> tuple[bool, str]:
    """Validate a single environment variable."""
    if not value:
        return False, "Empty value"

    pattern = config.get("pattern")
    if pattern and not re.match(pattern, value):
        return False, f"Invalid format. Expected: {config.get('example', pattern)}"

    return True, "Valid"


def check_gitignore(env_file: str) -> bool:
    """Check if .env is in .gitignore."""
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        return False

    with open(gitignore_path) as f:
        patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    env_basename = Path(env_file).name
    return env_basename in patterns or ".env" in patterns or ".env*" in patterns


def test_connection(url: str, anon_key: str) -> tuple[bool, str]:
    """Test connection to Supabase API."""
    try:
        import urllib.request
        import json

        # Test the REST API health
        req = urllib.request.Request(
            f"{url}/rest/v1/",
            headers={
                "apikey": anon_key,
                "Authorization": f"Bearer {anon_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return True, "Connection successful"
            return False, f"Unexpected status: {response.status}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # 404 on root is fine - API is working
            return True, "Connection successful"
        return False, f"HTTP Error: {e.code} {e.reason}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Validate Supabase environment variables")
    parser.add_argument(
        "--check-connection",
        action="store_true",
        help="Test actual connection to Supabase",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env)",
    )
    args = parser.parse_args()

    # Load environment variables
    env = parse_env_file(args.env_file)

    # Also check actual environment
    for key in list(REQUIRED_VARS.keys()) + list(OPTIONAL_VARS.keys()):
        if key not in env and key in os.environ:
            env[key] = os.environ[key]

    print("=" * 60)
    print("SUPABASE ENVIRONMENT VALIDATION")
    print("=" * 60)
    print(f"\nEnv file: {args.env_file}")
    print(f"File exists: {Path(args.env_file).exists()}")

    # Check gitignore
    if Path(args.env_file).exists():
        in_gitignore = check_gitignore(args.env_file)
        print(f"In .gitignore: {'Yes ✓' if in_gitignore else 'NO ⚠️  - Add to .gitignore!'}")

    print("\n" + "-" * 60)
    print("REQUIRED VARIABLES")
    print("-" * 60)

    missing_required = []
    all_valid = True

    for name, config in REQUIRED_VARS.items():
        value = env.get(name, "")
        if not value:
            print(f"\n❌ {name}")
            print(f"   MISSING: {config['description']}")
            print(f"   ASK_USER: Please provide your {config['description']}.")
            print(f"   LOCATION: {config['location']}")
            missing_required.append(name)
            all_valid = False
        else:
            valid, message = validate_var(name, value, config)
            if valid:
                print(f"\n✓ {name}")
                print(f"   {config['description']}")
                # Mask sensitive values
                masked = value[:20] + "..." if len(value) > 20 else value
                print(f"   Value: {masked}")
            else:
                print(f"\n⚠️  {name}")
                print(f"   {message}")
                all_valid = False

    print("\n" + "-" * 60)
    print("OPTIONAL VARIABLES")
    print("-" * 60)

    for name, config in OPTIONAL_VARS.items():
        value = env.get(name, "")
        if not value:
            print(f"\n○ {name}")
            print(f"   Not set - {config['description']}")
            print(f"   LOCATION: {config['location']}")
        else:
            valid, message = validate_var(name, value, config)
            if valid:
                print(f"\n✓ {name}")
                print(f"   {config['description']}")
                if "warning" in config:
                    print(f"   ⚠️  {config['warning']}")
            else:
                print(f"\n⚠️  {name}")
                print(f"   {message}")

    # Connection test
    if args.check_connection:
        print("\n" + "-" * 60)
        print("CONNECTION TEST")
        print("-" * 60)

        url = env.get("SUPABASE_URL")
        anon_key = env.get("SUPABASE_ANON_KEY")

        if url and anon_key:
            success, message = test_connection(url, anon_key)
            if success:
                print(f"\n✓ {message}")
            else:
                print(f"\n❌ {message}")
                all_valid = False
        else:
            print("\n⚠️  Cannot test connection - missing URL or ANON_KEY")

    # Summary
    print("\n" + "=" * 60)
    if missing_required:
        print("STATUS: ❌ MISSING REQUIRED CREDENTIALS")
        print(f"\nMissing: {', '.join(missing_required)}")
        sys.exit(1)
    elif all_valid:
        print("STATUS: ✓ ALL VALIDATIONS PASSED")
        sys.exit(0)
    else:
        print("STATUS: ⚠️  SOME VALIDATION WARNINGS")
        sys.exit(0)


if __name__ == "__main__":
    main()
