#!/usr/bin/env bash
# Firebase CLI preflight — run once per session BEFORE any firebase operation.
# Reports: CLI + Node versions, authorized account(s), active project, and
# (optionally) verifies a target project ID exists and is accessible.
# Read-only: only `--version`, `login:list`, `use`, `projects:list`.
#
# Usage: ./firebase_preflight.sh [target-project-id]

set -u

TARGET="${1:-}"

echo "=== Firebase CLI Preflight ==="

if ! command -v firebase >/dev/null 2>&1; then
  echo "FAIL: firebase not installed."
  echo "      → npm install -g firebase-tools   (or: curl -sL https://firebase.tools | bash)"
  exit 1
fi
echo "version : firebase-tools $(firebase --version 2>/dev/null | tail -1)"
command -v node >/dev/null 2>&1 && echo "node    : $(node --version 2>/dev/null)"

ACCOUNTS="$(firebase login:list 2>/dev/null)"
if echo "$ACCOUNTS" | grep -qi "no authorized accounts\|not logged in"; then
  echo "account : NONE — run \`firebase login\` (browser flow; user must do this themselves)"
  [ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ] || exit 1
else
  echo "account : $(echo "$ACCOUNTS" | grep -Eo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+' | tr '\n' ' ')"
fi
[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ] && \
  echo "sa-creds: GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS (service account may OVERRIDE the login above)"
[ -n "${FIREBASE_TOKEN:-}" ] && \
  echo "token   : FIREBASE_TOKEN is set (deprecated) — it takes precedence over login"

ACTIVE="$(firebase use 2>/dev/null | tail -1)"
case "$ACTIVE" in
  *"No project"*|*"no active project"*|*"firebase init"*|*"firebase use --add"*|"")
    echo "active  : NO active project in this directory — pass -P <project-id> explicitly" ;;
  *)
    echo "active  : $ACTIVE  (from .firebaserc — overridable w/ -P)" ;;
esac

if [ -n "$TARGET" ]; then
  LIST="$(firebase projects:list --json 2>/dev/null)"
  if echo "$LIST" | python3 -c '
import json, sys
target = sys.argv[1]
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(2)
ids = [p.get("projectId") for p in (data.get("result") or [])]
sys.exit(0 if target in ids else 1)
' "$TARGET"; then
    echo "target  : $TARGET — EXISTS and is accessible"
  else
    echo "target  : $TARGET — NOT FOUND in your accessible projects"
    echo "          → check the ID (display name ≠ project ID) via \`firebase projects:list\`"
    exit 1
  fi
fi

echo "OK: confirm account+project above match the intended target before ANY write."
