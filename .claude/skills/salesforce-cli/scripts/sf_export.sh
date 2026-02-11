#!/usr/bin/env bash
# sf_export.sh — Safe data export wrapper with format selection and row limits
# Usage: ./sf_export.sh --org <alias> --query "SELECT ..." [--format csv|json|tree] [--output <file|dir>] [--bulk]

set -euo pipefail

# Defaults
ORG=""
QUERY=""
FORMAT="csv"
OUTPUT=""
BULK=false
DEFAULT_LIMIT=200

# PII fields to warn about
PII_FIELDS="Email|Phone|MobilePhone|Fax|PersonEmail|PersonMobilePhone|Birthdate|SSN|Social_Security|TaxId|MailingStreet|OtherStreet|HomePhone"

usage() {
    cat <<EOF
Usage: sf_export.sh --org <alias> --query "SELECT ..." [options]

Options:
  --org <alias>       Target org alias (required)
  --query <soql>      SOQL query string (required)
  --format <fmt>      Export format: csv, json, tree (default: csv)
  --output <path>     Output file or directory (required for tree)
  --bulk              Use Bulk API for large datasets
  --limit <n>         Override default LIMIT for non-bulk (default: 200)
  -h, --help          Show this help

Safety:
  - Blocks SELECT * queries
  - Adds LIMIT for non-bulk queries
  - Requires WHERE clause for production bulk exports
  - Warns about PII fields
  - Checks governor limits before bulk operations
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
        --bulk) BULK=true; shift ;;
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
    echo "This prevents exporting unnecessary data and reduces PII exposure."
    exit 1
fi

# Safety: Add LIMIT for non-bulk queries
if [[ "$BULK" != true ]]; then
    if ! echo "$QUERY" | grep -qi 'LIMIT'; then
        echo "Warning: No LIMIT clause found. Adding LIMIT $DEFAULT_LIMIT."
        QUERY="$QUERY LIMIT $DEFAULT_LIMIT"
    fi
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

# Safety: Production bulk exports require WHERE clause
if [[ "$ORG_TYPE" == "PRODUCTION" ]]; then
    echo "⚠ Warning: Exporting from PRODUCTION org '$ORG'."

    if [[ "$BULK" == true ]]; then
        if ! echo "$QUERY" | grep -qi 'WHERE'; then
            echo "Error: Bulk exports from production require a WHERE clause."
            echo "This prevents accidental full-table exports of sensitive data."
            echo ""
            echo "Aborting."
            exit 1
        fi
    fi
    echo ""
fi

# Safety: PII field warning
if echo "$QUERY" | grep -qiE "$PII_FIELDS"; then
    echo "⚠ PII WARNING: Query includes potentially sensitive fields (Email, Phone, Birthdate, etc.)."
    echo "Ensure you have authorization to export this data."
    if [[ -n "$OUTPUT" ]]; then
        echo "Output file will contain PII — handle securely and delete when done."
    fi
    echo ""
fi

# Safety: Check governor limits before bulk operations
if [[ "$BULK" == true ]]; then
    echo "Checking API limits..."
    LIMITS_JSON=$(sf limits api display --target-org "$ORG" --json 2>/dev/null || echo '')
    if [[ -n "$LIMITS_JSON" ]]; then
        # Check DailyBulkV2QueryJobs remaining
        BULK_REMAINING=$(echo "$LIMITS_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for limit in d.get('result', []):
    if limit.get('name') == 'DailyBulkV2QueryJobs':
        remaining = limit.get('remaining', 'unknown')
        max_val = limit.get('max', 'unknown')
        print(f'{remaining}/{max_val}')
        break
else:
    print('unknown')
" 2>/dev/null || echo "unknown")

        if [[ "$BULK_REMAINING" != "unknown" ]]; then
            REMAINING_COUNT=$(echo "$BULK_REMAINING" | cut -d'/' -f1)
            if [[ "$REMAINING_COUNT" =~ ^[0-9]+$ ]] && [[ "$REMAINING_COUNT" -lt 10 ]]; then
                echo "⚠ WARNING: Only $BULK_REMAINING bulk query jobs remaining today."
                echo "Consider using non-bulk export or waiting until limits reset."
                echo ""
            else
                echo "Bulk query jobs remaining: $BULK_REMAINING"
            fi
        fi
    fi
    echo ""
fi

# Display export info
echo "=== Data Export ==="
echo "Org: $ORG ($ORG_TYPE)"
echo "Query: $QUERY"
echo "Format: $FORMAT"
echo "Mode: $(if [[ "$BULK" == true ]]; then echo 'Bulk API'; else echo 'Standard'; fi)"
if [[ -n "$OUTPUT" ]]; then
    echo "Output: $OUTPUT"
fi
echo "==================="
echo ""

# Execute based on format
case "$FORMAT" in
    csv)
        if [[ "$BULK" == true ]]; then
            if [[ -z "$OUTPUT" ]]; then
                OUTPUT="export_$(date +%Y%m%d_%H%M%S).csv"
            fi
            sf data export bulk --target-org "$ORG" \
                --query "$QUERY" \
                --output-file "$OUTPUT"
        else
            if [[ -n "$OUTPUT" ]]; then
                sf data query --target-org "$ORG" \
                    --query "$QUERY" \
                    --result-format csv --output-file "$OUTPUT"
            else
                sf data query --target-org "$ORG" \
                    --query "$QUERY" \
                    --result-format csv
            fi
        fi
        ;;
    json)
        if [[ -n "$OUTPUT" ]]; then
            sf data query --target-org "$ORG" \
                --query "$QUERY" \
                --json > "$OUTPUT"
        else
            sf data query --target-org "$ORG" \
                --query "$QUERY" \
                --json
        fi
        ;;
    tree)
        if [[ -z "$OUTPUT" ]]; then
            OUTPUT="./export_$(date +%Y%m%d_%H%M%S)"
        fi
        mkdir -p "$OUTPUT"
        sf data export tree --target-org "$ORG" \
            --query "$QUERY" \
            --plan --output-dir "$OUTPUT"
        ;;
    *)
        echo "Error: Unknown format '$FORMAT'. Use csv, json, or tree."
        exit 1
        ;;
esac

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 && -n "$OUTPUT" ]]; then
    if [[ -f "$OUTPUT" ]]; then
        SIZE=$(wc -c < "$OUTPUT" 2>/dev/null || echo "unknown")
        echo ""
        echo "Export complete: $OUTPUT ($SIZE bytes)"
    elif [[ -d "$OUTPUT" ]]; then
        COUNT=$(ls -1 "$OUTPUT" | wc -l | tr -d ' ')
        echo ""
        echo "Export complete: $OUTPUT ($COUNT files)"
    fi
fi

exit $EXIT_CODE
