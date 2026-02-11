#!/usr/bin/env bash
# sf_deploy.sh — Safe metadata deployment wrapper with dry-run defaults
# Usage: ./sf_deploy.sh --org <alias> --source <dir> [--confirm] [--test-level <level>] [--manifest <file>]

set -euo pipefail

# Defaults
ORG=""
SOURCE=""
MANIFEST=""
CONFIRM=false
TEST_LEVEL=""
DRY_RUN="--dry-run"

usage() {
    cat <<EOF
Usage: sf_deploy.sh --org <alias> --source <dir> [options]

Options:
  --org <alias>           Target org alias (required)
  --source <dir>          Source directory (e.g., force-app)
  --manifest <file>       Package.xml manifest path
  --confirm               Actually deploy (without this, runs dry-run only)
  --test-level <level>    Test level: NoTestRun, RunSpecifiedTests, RunLocalTests, RunAllTestsInOrg
  -h, --help              Show this help

Safety:
  - Defaults to --dry-run (validation only)
  - Requires --confirm to actually deploy
  - Blocks NoTestRun for production orgs
  - Blocks destructive changes without explicit flag
  - Requires typed alias confirmation for production deploys
  - Fails safe if org type cannot be detected
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --org) ORG="$2"; shift 2 ;;
        --source) SOURCE="$2"; shift 2 ;;
        --manifest) MANIFEST="$2"; shift 2 ;;
        --confirm) CONFIRM=true; DRY_RUN=""; shift ;;
        --test-level) TEST_LEVEL="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

# Validate required args
if [[ -z "$ORG" ]]; then
    echo "Error: --org is required"
    exit 1
fi

if [[ -z "$SOURCE" && -z "$MANIFEST" ]]; then
    echo "Error: --source or --manifest is required"
    exit 1
fi

# Detect org type — FAIL SAFE if detection fails
ORG_INFO=$(sf org display --target-org "$ORG" --json 2>/dev/null || echo '')
if [[ -z "$ORG_INFO" || "$ORG_INFO" == "{}" ]]; then
    echo "Error: Could not detect org type for '$ORG'."
    echo "Refusing to proceed — org must be authorized and reachable."
    echo "Run: sf org login web --alias $ORG"
    exit 1
fi

IS_SCRATCH=$(echo "$ORG_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('result',{}); print(str(r.get('isScratch', False)).lower())" 2>/dev/null || echo "false")
IS_SANDBOX=$(echo "$ORG_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('result',{}); print(str(r.get('isSandbox', False)).lower())" 2>/dev/null || echo "false")

ORG_TYPE="PRODUCTION"
if [[ "$IS_SCRATCH" == "true" ]]; then
    ORG_TYPE="Scratch"
elif [[ "$IS_SANDBOX" == "true" ]]; then
    ORG_TYPE="Sandbox"
fi

# Check for destructive changes in source directory
HAS_DESTRUCTIVE=false
if [[ -n "$SOURCE" ]]; then
    if find "$SOURCE" -name "destructiveChanges*.xml" -type f 2>/dev/null | grep -q .; then
        HAS_DESTRUCTIVE=true
    fi
fi
if [[ -n "$MANIFEST" ]]; then
    MANIFEST_DIR=$(dirname "$MANIFEST")
    if find "$MANIFEST_DIR" -name "destructiveChanges*.xml" -type f 2>/dev/null | grep -q .; then
        HAS_DESTRUCTIVE=true
    fi
fi

# Block destructive changes in production without explicit confirmation
if [[ "$HAS_DESTRUCTIVE" == true ]]; then
    echo "⚠ DESTRUCTIVE CHANGES DETECTED (destructiveChanges.xml found)"
    echo ""
    if [[ "$ORG_TYPE" == "PRODUCTION" ]]; then
        echo "ERROR: Destructive metadata changes to PRODUCTION are FORBIDDEN via this script."
        echo "Destructive changes permanently delete metadata (fields, objects, classes, etc.)."
        echo "This requires manual triple-confirmation through the AI assistant."
        echo ""
        echo "Aborting."
        exit 1
    else
        echo "WARNING: Destructive changes will permanently remove metadata from $ORG_TYPE org '$ORG'."
        if [[ "$CONFIRM" != true ]]; then
            echo "Run with --confirm to proceed."
            exit 1
        fi
        echo "Proceeding with destructive changes in $ORG_TYPE org..."
        echo ""
    fi
fi

# Production safety — require typed alias confirmation and enforce test level
if [[ "$ORG_TYPE" == "PRODUCTION" ]]; then
    if [[ "$CONFIRM" == true ]]; then
        echo "============================================"
        echo "⚠ PRODUCTION DEPLOYMENT to '$ORG'"
        echo "============================================"
        echo ""

        # Block NoTestRun for production — NEVER allow skipping tests
        if [[ "$TEST_LEVEL" == "NoTestRun" ]]; then
            echo "ERROR: --test-level NoTestRun is BLOCKED for production deployments."
            echo "Production requires at minimum RunLocalTests."
            echo ""
            echo "Aborting."
            exit 1
        fi

        # Enforce minimum test level for production
        if [[ -z "$TEST_LEVEL" || "$TEST_LEVEL" == "RunSpecifiedTests" ]]; then
            TEST_LEVEL="RunLocalTests"
            echo "Enforcing --test-level RunLocalTests for production."
        fi

        echo "This will modify your PRODUCTION environment."
        echo ""

        # Require typed alias confirmation
        read -r -p "Type the org alias '$ORG' to confirm: " TYPED_ALIAS
        if [[ "$TYPED_ALIAS" != "$ORG" ]]; then
            echo ""
            echo "Alias mismatch. Expected '$ORG', got '$TYPED_ALIAS'."
            echo "Aborting production deployment."
            exit 1
        fi
        echo ""
        echo "Confirmed. Proceeding with production deployment..."
        echo ""
    fi
fi

# Step 1: Preview
echo "=== Deployment Preview ==="
echo "Org: $ORG ($ORG_TYPE)"
echo "Mode: $(if [[ -n "$DRY_RUN" ]]; then echo 'Validation only (dry-run)'; else echo 'ACTUAL DEPLOYMENT'; fi)"
if [[ -n "$SOURCE" ]]; then
    echo "Source: $SOURCE"
fi
if [[ -n "$MANIFEST" ]]; then
    echo "Manifest: $MANIFEST"
fi
if [[ -n "$TEST_LEVEL" ]]; then
    echo "Test Level: $TEST_LEVEL"
fi
if [[ "$HAS_DESTRUCTIVE" == true ]]; then
    echo "⚠ Destructive Changes: YES"
fi
echo "=========================="
echo ""

# Build command using arrays (no eval)
CMD_ARGS=("sf" "project" "deploy" "start" "--target-org" "$ORG")

if [[ -n "$SOURCE" ]]; then
    CMD_ARGS+=("--source-dir" "$SOURCE")
fi

if [[ -n "$MANIFEST" ]]; then
    CMD_ARGS+=("--manifest" "$MANIFEST")
fi

if [[ -n "$DRY_RUN" ]]; then
    CMD_ARGS+=("$DRY_RUN")
fi

if [[ -n "$TEST_LEVEL" ]]; then
    CMD_ARGS+=("--test-level" "$TEST_LEVEL")
fi

# Execute
echo "Running: ${CMD_ARGS[*]}"
echo ""
"${CMD_ARGS[@]}"

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    if [[ -n "$DRY_RUN" ]]; then
        echo ""
        echo "Validation successful. Run with --confirm to deploy."
    else
        echo ""
        echo "Deployment completed successfully."
    fi
else
    echo ""
    echo "Deployment failed. Check errors above."
fi

exit $EXIT_CODE
