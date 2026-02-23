#!/usr/bin/env bash
# sf_safe_query.sh — Safe SOQL/SOSL query wrapper with mandatory LIMIT enforcement
# Usage: ./sf_safe_query.sh --org <alias> --query "SELECT ..." [--format csv|json|human] [--output <file>] [--tooling]

set -euo pipefail

# Defaults
ORG=""
QUERY=""
FORMAT="human"
OUTPUT=""
TOOLING=""
DEFAULT_LIMIT=200

# PII fields to warn about
PII_FIELDS="Email|Phone|MobilePhone|Fax|PersonEmail|PersonMobilePhone|Birthdate|SSN|Social_Security|TaxId|MailingStreet|OtherStreet|HomePhone"

usage() {
    cat <<EOF
Usage: sf_safe_query.sh --org <alias> --query "SELECT ..." [options]

Options:
  --org <alias>       Target org alias (required)
  --query <soql>      SOQL/SOSL query string (required)
  --format <fmt>      Output format: csv, json, human (default: human)
  --output <file>     Output file path (optional)
  --tooling           Use Tooling API
  --limit <n>         Override default LIMIT (default: 200)
  -h, --help          Show this help

Safety:
  - Automatically adds LIMIT if missing
  - Blocks SELECT * queries
  - Warns about production org queries
  - Requires WHERE clause for production queries
  - Warns about PII fields in query results
  - Fails safe if org type cannot be detected
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --org) ORG="$2"; shift 2 ;;
        --query) QUERY="$2"; shift 2 ;;
        --format) FORMAT="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --tooling) TOOLING="--use-tooling-api"; shift ;;
        --limit) DEFAULT_LIMIT="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

# Validate required args
if [[ -z "$ORG" ]]; then
    echo "Error: --org is required"
    exit 1
fi

if [[ -z "$QUERY" ]]; then
    echo "Error: --query is required"
    exit 1
fi

# Safety: Block SELECT *
if echo "$QUERY" | grep -qi 'SELECT \*'; then
    echo "Error: SELECT * is not allowed. Specify fields explicitly."
    echo "Tip: Use 'sf schema generate sobject --sobject <name> --target-org $ORG' to see available fields."
    exit 1
fi

# Safety: Check for LIMIT clause
if ! echo "$QUERY" | grep -qi 'LIMIT'; then
    echo "Warning: No LIMIT clause found. Adding LIMIT $DEFAULT_LIMIT."
    QUERY="$QUERY LIMIT $DEFAULT_LIMIT"
fi

# Safety: Detect org type — FAIL SAFE if detection fails
ORG_INFO=$(sf org display --target-org "$ORG" --json 2>/dev/null || echo '')
if [[ -z "$ORG_INFO" ]]; then
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

# Safety: Production queries require WHERE clause
if [[ "$ORG_TYPE" == "PRODUCTION" ]]; then
    echo "⚠ Warning: Target org '$ORG' is PRODUCTION."

    # Check for WHERE clause (skip for aggregate/COUNT queries)
    if ! echo "$QUERY" | grep -qi 'WHERE' && ! echo "$QUERY" | grep -qi 'GROUP BY' && ! echo "$QUERY" | grep -qi 'COUNT('; then
        echo "Error: Production queries require a WHERE clause to prevent full-table scans."
        echo "Add a WHERE clause or use --limit to restrict results."
        echo ""
        echo "Aborting."
        exit 1
    fi
    echo ""
fi

# Safety: PII field warning
if echo "$QUERY" | grep -qiE "$PII_FIELDS"; then
    echo "⚠ PII WARNING: Query includes potentially sensitive fields (Email, Phone, Birthdate, etc.)."
    echo "Ensure you have authorization to access this data."
    if [[ -n "$OUTPUT" ]]; then
        echo "Output file '$OUTPUT' will contain PII — handle securely."
    fi
    echo ""
fi

# Build command using arrays (no eval)
CMD_ARGS=("sf" "data" "query" "--target-org" "$ORG" "--query" "$QUERY" "--result-format" "$FORMAT")

if [[ -n "$TOOLING" ]]; then
    CMD_ARGS+=("$TOOLING")
fi

if [[ -n "$OUTPUT" ]]; then
    CMD_ARGS+=("--output-file" "$OUTPUT")
fi

# Display query info
echo "Org: $ORG ($ORG_TYPE)"
echo "Query: $QUERY"
echo "Format: $FORMAT"
if [[ -n "$OUTPUT" ]]; then
    echo "Output: $OUTPUT"
fi
echo "---"

# Execute
"${CMD_ARGS[@]}"

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && -n "$OUTPUT" ]]; then
    SIZE=$(wc -c < "$OUTPUT" 2>/dev/null || echo "unknown")
    echo "---"
    echo "Output written to: $OUTPUT ($SIZE bytes)"
fi

exit $EXIT_CODE
