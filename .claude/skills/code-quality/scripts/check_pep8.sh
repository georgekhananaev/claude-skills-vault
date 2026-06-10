#!/bin/bash
# Quick PEP 8 check using pycodestyle
#
# Usage:
#   ./check_pep8.sh <file_or_dir>
#   ./check_pep8.sh src/
#   ./check_pep8.sh script.py
#
# Install: pip install pycodestyle

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <file_or_dir>"
    exit 1
fi

TARGET="$1"

if ! command -v pycodestyle &> /dev/null; then
    echo "pycodestyle not found. Install with: pip install pycodestyle"
    exit 1
fi

echo "=== PEP 8 Check: $TARGET ==="
pycodestyle --max-line-length=88 --statistics "$TARGET"

echo ""
echo "PEP 8 check passed!"