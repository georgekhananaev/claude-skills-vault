#!/bin/bash
# Type hint validation using mypy
#
# Usage:
#   ./check_types.sh <file_or_dir>
#   ./check_types.sh src/ --strict
#
# Install: pip install mypy

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <file_or_dir> [--strict]"
    exit 1
fi

TARGET="$1"
STRICT=""

if [ "$2" = "--strict" ]; then
    STRICT="--strict"
fi

if ! command -v mypy &> /dev/null; then
    echo "mypy not found. Install with: pip install mypy"
    exit 1
fi

echo "=== Type Check: $TARGET ==="
mypy $STRICT --python-version 3.11 "$TARGET"

echo ""
echo "Type check passed!"
