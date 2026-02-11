#!/bin/bash
#
# Schema Drift Checker
# Detects differences between local migrations and remote database schema.
#
# Usage:
#   bash check_drift.sh [--local | --remote]
#
# Exit codes:
#   0 - No drift detected
#   1 - Drift detected or error
#

set -e

# Parse arguments
TARGET="local"
VERBOSE=false

for arg in "$@"; do
  case $arg in
    --local)
      TARGET="local"
      shift
      ;;
    --remote)
      TARGET="remote"
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      echo "Usage: bash check_drift.sh [--local | --remote] [--verbose]"
      echo ""
      echo "Options:"
      echo "  --local    Check local database (default)"
      echo "  --remote   Check remote/linked database"
      echo "  --verbose  Show detailed output"
      echo ""
      echo "Exit codes:"
      echo "  0 - No drift detected"
      echo "  1 - Drift detected or error"
      exit 0
      ;;
  esac
done

echo "============================================================"
echo " SCHEMA DRIFT CHECKER [$TARGET]"
echo "============================================================"
echo ""

# Check if supabase CLI is available
if ! command -v supabase &> /dev/null; then
    echo "Error: supabase CLI not found"
    echo "Install with: brew install supabase/tap/supabase"
    exit 1
fi

# Check if in a supabase project
if [ ! -d "supabase" ]; then
    echo "Error: Not in a Supabase project directory"
    echo "Expected to find 'supabase/' directory"
    exit 1
fi

echo "Running schema diff..."
echo ""

# Run diff and capture output
DIFF_OUTPUT=""
DIFF_EXIT=0

if [ "$TARGET" = "remote" ]; then
    DIFF_OUTPUT=$(supabase db diff --linked 2>&1) || DIFF_EXIT=$?
else
    DIFF_OUTPUT=$(supabase db diff 2>&1) || DIFF_EXIT=$?
fi

# Check for errors
if [ $DIFF_EXIT -ne 0 ] && [[ "$DIFF_OUTPUT" == *"error"* ]]; then
    echo "Error running diff:"
    echo "$DIFF_OUTPUT"
    exit 1
fi

# Check if there's drift
if [ -z "$DIFF_OUTPUT" ] || [[ "$DIFF_OUTPUT" == *"No changes found"* ]]; then
    echo "============================================================"
    echo "✓ NO DRIFT DETECTED"
    echo "============================================================"
    echo ""
    echo "Local migrations are in sync with $TARGET database."
    exit 0
else
    echo "============================================================"
    echo "⚠️  DRIFT DETECTED"
    echo "============================================================"
    echo ""
    echo "The $TARGET database schema differs from migrations."
    echo ""
    echo "------------------------------------------------------------"
    echo "DIFFERENCES:"
    echo "------------------------------------------------------------"
    echo "$DIFF_OUTPUT"
    echo ""
    echo "------------------------------------------------------------"
    echo ""
    echo "Options to resolve:"
    echo "  1. Generate migration from diff:"
    echo "     supabase db diff --use-migra -f fix_drift"
    echo ""
    echo "  2. Reset local to match migrations:"
    echo "     supabase db reset"
    echo ""
    echo "  3. Manually review and fix differences"
    echo ""
    exit 1
fi
