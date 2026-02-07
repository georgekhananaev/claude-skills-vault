#!/usr/bin/env bash
# Monday.com GraphQL API helper - direct API calls w/o MCP dependency.
# Usage:
#   monday_api.sh query '{ boards(limit:5) { id name } }'
#   monday_api.sh mutation 'mutation { create_item(...) { id } }'
#
# Requires: MONDAY_API_TOKEN env var
# API endpoint: https://api.monday.com/v2

set -euo pipefail

API_URL="https://api.monday.com/v2"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# Load MONDAY_API_TOKEN from .env.local or .env if not already set
if [[ -z "${MONDAY_API_TOKEN:-}" ]]; then
    for envfile in "$PROJECT_ROOT/.env.local" "$PROJECT_ROOT/.env"; do
        if [[ -f "$envfile" ]]; then
            token=$(grep -E '^MONDAY_API_TOKEN=' "$envfile" | head -1 | cut -d'=' -f2-)
            if [[ -n "$token" ]]; then
                export MONDAY_API_TOKEN="$token"
                break
            fi
        fi
    done
fi

if [[ -z "${MONDAY_API_TOKEN:-}" ]]; then
    echo "MISSING: MONDAY_API_TOKEN"
    echo "ASK_USER: Please provide your Monday.com API token."
    echo "LOCATION: Monday.com > Avatar (bottom-left) > Developers > My access tokens"
    echo "SET: Add MONDAY_API_TOKEN=<token> to .env or .env.local in project root"
    exit 1
fi

if [[ $# -lt 2 ]]; then
    echo "Usage: monday_api.sh <query|mutation> '<graphql_string>'"
    echo ""
    echo "Examples:"
    echo "  monday_api.sh query '{ boards(limit:5) { id name } }'"
    echo "  monday_api.sh mutation 'mutation { create_item(board_id: 123, item_name: \"Task\") { id } }'"
    exit 1
fi

OP_TYPE="$1"
GRAPHQL="$2"

# Escape the GraphQL string for JSON
JSON_BODY=$(printf '{"query": %s}' "$(echo "$GRAPHQL" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))')")

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: $MONDAY_API_TOKEN" \
    -H "API-Version: 2024-10" \
    -d "$JSON_BODY")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" == "401" ]]; then
    echo "ERROR: Authentication failed (401)"
    echo "CAUSE: Invalid or expired API token"
    echo "FIX: Regenerate token at Monday.com > Avatar > Developers > My access tokens"
    exit 1
elif [[ "$HTTP_CODE" == "429" ]]; then
    echo "ERROR: Rate limit exceeded (429)"
    echo "CAUSE: Too many requests - complexity budget exceeded"
    echo "FIX: Wait 60 seconds before retrying"
    exit 1
elif [[ "$HTTP_CODE" -ge 400 ]]; then
    echo "ERROR: API returned HTTP $HTTP_CODE"
    echo "$BODY"
    exit 1
fi

# Pretty-print JSON if python3 available
if command -v python3 &>/dev/null; then
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo "$BODY"
fi