#!/usr/bin/env python3
"""
Alembic Migration Generator Wrapper

Simplifies creating and managing database migrations for FastAPI projects.

Usage:
    python generate_migration.py "migration message" [options]

Options:
    --autogenerate    Auto-detect model changes (default: True)
    --empty           Create empty migration
    --sql             Generate SQL instead of running migration
    --upgrade         Run upgrade to head after generation
    --downgrade N     Downgrade N revisions
    --history         Show migration history
    --current         Show current revision

Examples:
    python generate_migration.py "add users table"
    python generate_migration.py "add email index" --upgrade
    python generate_migration.py --history
    python generate_migration.py --downgrade 1
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    """Run a command and handle output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
    )
    if result.returncode != 0:
        if capture:
            print(f"Error: {result.stderr}")
        sys.exit(result.returncode)
    return result


def check_alembic() -> bool:
    """Check if alembic is configured."""
    if not Path("alembic.ini").exists():
        print("Error: alembic.ini not found")
        print("Run 'alembic init alembic' first or use --with-alembic when scaffolding")
        return False
    if not Path("alembic").is_dir():
        print("Error: alembic/ directory not found")
        return False
    return True


def generate_migration(message: str, autogenerate: bool = True, empty: bool = False) -> None:
    """Generate a new migration."""
    if not check_alembic():
        sys.exit(1)

    # Sanitize message for filename
    safe_message = message.lower().replace(" ", "_")[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    cmd = ["alembic", "revision"]

    if empty:
        cmd.extend(["-m", message])
    elif autogenerate:
        cmd.extend(["--autogenerate", "-m", message])
    else:
        cmd.extend(["-m", message])

    print(f"\nGenerating migration: {message}")
    print("-" * 50)
    run_command(cmd)
    print("\nMigration created successfully!")
    print("Review the generated migration file before running upgrade.")


def upgrade(revision: str = "head") -> None:
    """Run database upgrade."""
    if not check_alembic():
        sys.exit(1)

    print(f"\nUpgrading database to: {revision}")
    print("-" * 50)
    run_command(["alembic", "upgrade", revision])
    print("\nUpgrade complete!")


def downgrade(revisions: int = 1) -> None:
    """Downgrade database by N revisions."""
    if not check_alembic():
        sys.exit(1)

    print(f"\nDowngrading database by {revisions} revision(s)")
    print("-" * 50)
    run_command(["alembic", "downgrade", f"-{revisions}"])
    print("\nDowngrade complete!")


def show_history() -> None:
    """Show migration history."""
    if not check_alembic():
        sys.exit(1)

    print("\nMigration History:")
    print("-" * 50)
    run_command(["alembic", "history", "--verbose"])


def show_current() -> None:
    """Show current revision."""
    if not check_alembic():
        sys.exit(1)

    print("\nCurrent Revision:")
    print("-" * 50)
    run_command(["alembic", "current"])


def generate_sql(revision: str = "head") -> None:
    """Generate SQL for migration."""
    if not check_alembic():
        sys.exit(1)

    print(f"\nGenerating SQL for upgrade to: {revision}")
    print("-" * 50)
    run_command(["alembic", "upgrade", revision, "--sql"])


def stamp(revision: str = "head") -> None:
    """Stamp database with revision without running migrations."""
    if not check_alembic():
        sys.exit(1)

    print(f"\nStamping database with revision: {revision}")
    print("-" * 50)
    run_command(["alembic", "stamp", revision])
    print("\nDatabase stamped!")


def main():
    parser = argparse.ArgumentParser(
        description="Alembic migration helper for FastAPI projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("message", nargs="?", help="Migration message")
    parser.add_argument("--autogenerate", action="store_true", default=True,
                        help="Auto-detect model changes (default)")
    parser.add_argument("--empty", action="store_true",
                        help="Create empty migration")
    parser.add_argument("--upgrade", action="store_true",
                        help="Run upgrade after generating")
    parser.add_argument("--downgrade", type=int, metavar="N",
                        help="Downgrade by N revisions")
    parser.add_argument("--history", action="store_true",
                        help="Show migration history")
    parser.add_argument("--current", action="store_true",
                        help="Show current revision")
    parser.add_argument("--sql", action="store_true",
                        help="Generate SQL output")
    parser.add_argument("--stamp", metavar="REV",
                        help="Stamp database with revision")
    parser.add_argument("--heads", action="store_true",
                        help="Show current heads")

    args = parser.parse_args()

    # Handle commands
    if args.history:
        show_history()
        return 0

    if args.current:
        show_current()
        return 0

    if args.heads:
        if check_alembic():
            run_command(["alembic", "heads"])
        return 0

    if args.downgrade:
        downgrade(args.downgrade)
        return 0

    if args.stamp:
        stamp(args.stamp)
        return 0

    if args.sql:
        generate_sql()
        return 0

    # Generate migration
    if not args.message:
        parser.print_help()
        print("\nError: Migration message required")
        return 1

    generate_migration(args.message, not args.empty, args.empty)

    if args.upgrade:
        upgrade()

    return 0


if __name__ == "__main__":
    sys.exit(main())
