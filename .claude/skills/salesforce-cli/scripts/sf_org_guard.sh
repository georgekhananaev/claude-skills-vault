#!/usr/bin/env bash
# sf_org_guard.sh — Org type detection and safety tier enforcement
# Usage: ./sf_org_guard.sh --org <alias> [--require scratch|sandbox|any] [--json]

set -euo pipefail

# Defaults
ORG=""
REQUIRE=""
JSON_OUT=false

usage() {
    cat <<EOF
Usage: sf_org_guard.sh --org <alias> [options]

Options:
  --org <alias>           Target org alias (required)
  --require <type>        Required org type: scratch, sandbox, non-prod, any (default: any)
  --json                  Output as JSON
  -h, --help              Show this help

Exit codes:
  0 - Org matches requirements
  1 - Error (org not found, auth failed)
  2 - Org does not match requirements (e.g., production when scratch required)

Output:
  Prints org type information and safety tier.
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --org) ORG="$2"; shift 2 ;;
        --require) REQUIRE="$2"; shift 2 ;;
        --json) JSON_OUT=true; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

# Validate required args
if [[ -z "$ORG" ]]; then
    echo "Error: --org is required"
    exit 1
fi

# Get org info
ORG_INFO=$(sf org display --target-org "$ORG" --json 2>/dev/null)
if [[ $? -ne 0 ]]; then
    echo "Error: Could not retrieve org info for '$ORG'. Is the org authorized?"
    exit 1
fi

# Parse org details
IS_SCRATCH=$(echo "$ORG_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d.get('result',{}).get('isScratch', False)).lower())" 2>/dev/null || echo "false")
IS_SANDBOX=$(echo "$ORG_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d.get('result',{}).get('isSandbox', False)).lower())" 2>/dev/null || echo "false")
INSTANCE_URL=$(echo "$ORG_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result',{}).get('instanceUrl', 'unknown'))" 2>/dev/null || echo "unknown")
USERNAME=$(echo "$ORG_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result',{}).get('username', 'unknown'))" 2>/dev/null || echo "unknown")
ORG_ID=$(echo "$ORG_INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result',{}).get('id', 'unknown'))" 2>/dev/null || echo "unknown")

# Determine org type
ORG_TYPE="production"
SAFETY_TIER="high"
if [[ "$IS_SCRATCH" == "true" ]]; then
    ORG_TYPE="scratch"
    SAFETY_TIER="low"
elif [[ "$IS_SANDBOX" == "true" ]]; then
    ORG_TYPE="sandbox"
    SAFETY_TIER="medium"
else
    # Additional check: instance URL
    if echo "$INSTANCE_URL" | grep -qi "test.salesforce.com"; then
        ORG_TYPE="sandbox"
        SAFETY_TIER="medium"
    elif echo "$INSTANCE_URL" | grep -qi "cs[0-9]"; then
        # cs[0-9] instances are sandbox servers, not scratch orgs
        ORG_TYPE="sandbox"
        SAFETY_TIER="medium"
    fi
fi

# Output
if [[ "$JSON_OUT" == true ]]; then
    cat <<EOF
{
  "alias": "$ORG",
  "orgType": "$ORG_TYPE",
  "safetyTier": "$SAFETY_TIER",
  "isScratch": $IS_SCRATCH,
  "isSandbox": $IS_SANDBOX,
  "instanceUrl": "$INSTANCE_URL",
  "username": "$USERNAME",
  "orgId": "$ORG_ID"
}
EOF
else
    echo "Org: $ORG"
    echo "Type: $ORG_TYPE"
    echo "Safety Tier: $SAFETY_TIER"
    echo "Instance: $INSTANCE_URL"
    echo "Username: $USERNAME"
    echo "Org ID: $ORG_ID"

    if [[ "$ORG_TYPE" == "production" ]]; then
        echo ""
        echo "⚠ WARNING: This is a PRODUCTION org."
        echo "All write operations require explicit confirmation."
    fi
fi

# Check requirement
if [[ -n "$REQUIRE" ]]; then
    case "$REQUIRE" in
        scratch)
            if [[ "$ORG_TYPE" != "scratch" ]]; then
                echo ""
                echo "Error: Required org type 'scratch' but got '$ORG_TYPE'."
                exit 2
            fi
            ;;
        sandbox)
            if [[ "$ORG_TYPE" != "sandbox" ]]; then
                echo ""
                echo "Error: Required org type 'sandbox' but got '$ORG_TYPE'."
                exit 2
            fi
            ;;
        non-prod)
            if [[ "$ORG_TYPE" == "production" ]]; then
                echo ""
                echo "Error: Required non-production org but '$ORG' is production."
                exit 2
            fi
            ;;
        any)
            ;; # Always passes
        *)
            echo "Error: Unknown requirement '$REQUIRE'. Use: scratch, sandbox, non-prod, any"
            exit 1
            ;;
    esac
fi

exit 0
