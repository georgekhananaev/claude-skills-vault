#!/bin/bash
# Auto-fix Python style issues using ruff
#
# Usage:
#   ./fix_style.sh <file_or_dir>
#
# Install: pip install ruff
#
# What it fixes:
#   - Import sorting (isort)
#   - Unused imports removal
#   - PEP 8 violations
#   - Code formatting

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <file_or_dir>"
    exit 1
fi

TARGET="$1"

if ! command -v ruff &> /dev/null; then
    echo "ruff not found. Install with: pip install ruff"
    exit 1
fi

echo "=== Fixing: $TARGET ==="

echo ""
echo "1. Running ruff check --fix..."
ruff check --fix "$TARGET" || true

echo ""
echo "2. Running ruff format..."
ruff format "$TARGET"

echo ""
echo "Done! Re-run check_style.py to verify."