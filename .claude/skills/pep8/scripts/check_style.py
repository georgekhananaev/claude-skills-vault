#!/usr/bin/env python3
"""Check Python files for PEP 8 compliance and type hints.

Usage:
    python check_style.py <file_or_dir> [--fix] [--strict]

Requirements:
    pip install ruff pycodestyle mypy

Examples:
    python check_style.py src/
    python check_style.py script.py --fix
    python check_style.py . --strict
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], capture: bool = True) -> tuple[int, str]:
    """Run command and return exit code + output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
        )
        output = result.stdout + result.stderr if capture else ""
        return result.returncode, output
    except FileNotFoundError:
        return -1, f"Command not found: {cmd[0]}"


def check_ruff(path: str, fix: bool = False) -> tuple[int, str]:
    """Run ruff linter."""
    cmd = ["ruff", "check", path]
    if fix:
        cmd.append("--fix")
    return run_command(cmd)


def check_ruff_format(path: str, fix: bool = False) -> tuple[int, str]:
    """Run ruff formatter."""
    cmd = ["ruff", "format", path]
    if not fix:
        cmd.append("--check")
    return run_command(cmd)


def check_pycodestyle(path: str) -> tuple[int, str]:
    """Run pycodestyle (PEP 8 checker)."""
    cmd = ["pycodestyle", "--max-line-length=88", path]
    return run_command(cmd)


def check_mypy(path: str, strict: bool = False) -> tuple[int, str]:
    """Run mypy type checker."""
    cmd = ["mypy", path]
    if strict:
        cmd.append("--strict")
    return run_command(cmd)


def print_section(title: str, code: int, output: str) -> None:
    """Print formatted section output."""
    status = "PASS" if code == 0 else "FAIL" if code > 0 else "SKIP"
    color = "\033[92m" if code == 0 else "\033[91m" if code > 0 else "\033[93m"
    reset = "\033[0m"

    print(f"\n{color}=== {title} [{status}] ==={reset}")
    if output.strip():
        print(output.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Python code style")
    parser.add_argument("path", help="File or directory to check")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues where possible")
    parser.add_argument("--strict", action="store_true", help="Enable strict type checking")
    parser.add_argument("--ruff-only", action="store_true", help="Only run ruff")
    parser.add_argument("--types-only", action="store_true", help="Only run mypy")
    args = parser.parse_args()

    path = args.path
    if not Path(path).exists():
        print(f"Error: Path not found: {path}")
        return 1

    results: list[tuple[str, int]] = []

    if not args.types_only:
        # Ruff linting
        code, output = check_ruff(path, args.fix)
        print_section("Ruff Linter", code, output)
        results.append(("ruff", code))

        # Ruff formatting
        code, output = check_ruff_format(path, args.fix)
        print_section("Ruff Format", code, output)
        results.append(("ruff-format", code))

        if not args.ruff_only:
            # Pycodestyle (fallback PEP 8)
            code, output = check_pycodestyle(path)
            print_section("Pycodestyle (PEP 8)", code, output)
            results.append(("pycodestyle", code))

    if not args.ruff_only:
        # Mypy type checking
        code, output = check_mypy(path, args.strict)
        print_section("Mypy Type Check", code, output)
        results.append(("mypy", code))

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    failed = []
    skipped = []
    for name, code in results:
        if code == 0:
            print(f"  {name}: PASS")
        elif code < 0:
            print(f"  {name}: SKIPPED (tool not installed)")
            skipped.append(name)
        else:
            print(f"  {name}: FAIL")
            failed.append(name)

    if skipped:
        print(f"\nInstall missing tools: pip install {' '.join(skipped)}")

    if failed:
        print(f"\nFailed checks: {', '.join(failed)}")
        return 1

    print("\nAll checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())