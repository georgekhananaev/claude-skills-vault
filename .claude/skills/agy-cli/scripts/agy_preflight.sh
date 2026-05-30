#!/usr/bin/env bash
# agy_preflight.sh — run ONCE at the start of an agy delegation session.
#
# Does the cheap, safe checks that prevent the common failure modes:
#   1. Ensures `agy` is installed + on PATH.
#   2. Checks for / applies CLI updates so you're on the newest build
#      (the user wants "always latest"). Skips the network call with --no-update.
#   3. Repairs a 0-byte/invalid ~/.gemini/config/mcp_config.json, which throws
#      `unexpected end of JSON input` on EVERY startup (only with --fix).
#   4. Reports the model selected for the most recent run, parsed from logs, so
#      Claude can warn if it's a low tier when max capability was wanted. There
#      is no headless model flag — selection persists from the REPL `/settings`.
#
# Usage: agy_preflight.sh [--no-update] [--fix]
# Exit:  0 ok · 1 agy missing
set -uo pipefail
DO_UPDATE=1; FIX=0
for a in "$@"; do case "$a" in --no-update) DO_UPDATE=0;; --fix) FIX=1;; esac; done

if ! command -v agy >/dev/null 2>&1; then
  echo "PREFLIGHT=fail  agy not found in PATH (install: see https://antigravity.google / 'agy install')"
  exit 1
fi
echo "PREFLIGHT agy=$(command -v agy)"

# 1. Version + update.
VER="$(agy changelog 2>/dev/null | grep -oiE 'v?[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
echo "PREFLIGHT version=${VER:-unknown}"
if [ "$DO_UPDATE" = 1 ]; then
  UP="$(agy update 2>&1 | tail -3 | tr '\n' ' ')"
  echo "PREFLIGHT update=${UP:-'(no output — already current)'}"
else
  echo "PREFLIGHT update=skipped"
fi

# 2. Repair empty/invalid mcp_config.json (startup error on every run).
MCP="$HOME/.gemini/config/mcp_config.json"
if [ -f "$MCP" ]; then
  if ! python3 -c "import json,sys; json.load(open('$MCP'))" >/dev/null 2>&1; then
    if [ "$FIX" = 1 ]; then
      cp "$MCP" "$MCP.bak.$(date +%s)" 2>/dev/null
      printf '{}\n' > "$MCP"
      echo "PREFLIGHT mcp_config=REPAIRED (was invalid; backed up, wrote '{}')"
    else
      echo "PREFLIGHT mcp_config=INVALID ($MCP throws on startup — re-run with --fix to reset to '{}')"
    fi
  else
    echo "PREFLIGHT mcp_config=ok"
  fi
else
  echo "PREFLIGHT mcp_config=absent(ok)"
fi

# 3. Report the model from the most recent run log (no headless way to read it
#    otherwise). Empty if agy hasn't run yet this install.
LOGDIR="$HOME/.gemini/antigravity-cli/log"
LASTLOG="$(ls -t "$LOGDIR"/cli-*.log 2>/dev/null | head -1)"
if [ -n "${LASTLOG:-}" ]; then
  MODEL="$(grep -oE 'label="[^"]+"' "$LASTLOG" 2>/dev/null | tail -1 | sed 's/label="//;s/"$//')"
  echo "PREFLIGHT model=${MODEL:-unknown}  (set the top tier once via REPL /settings; it persists)"
  case "$MODEL" in
    *Flash*|*Lite*|*Mini*) echo "PREFLIGHT model_warn=Selected model is a fast/low tier — switch to the Pro/Max tier in /settings for hard tasks.";;
  esac
else
  echo "PREFLIGHT model=unknown (no prior run log)"
fi
echo "PREFLIGHT=ok"
