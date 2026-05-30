#!/usr/bin/env bash
# agy_run.sh — heartbeat-guarded runner for Google's Antigravity CLI (`agy`).
#
# WHY: `agy -p` buffers all output until it finishes and can silently stall
# (an SSE/network stall, or a tool that tries to escape the sandbox and waits
# for a TTY approval that never comes in headless mode). Running it bare means
# Claude blind-waits up to `--print-timeout` (often set to 20-45m) with zero
# feedback. This wrapper watches the agy `--log-file` for liveness and exits
# the instant agy finishes OR the log goes silent for --stall seconds — turning
# a 10-45 min blind wait into <=3 min stall detection.
#
# Designed to be launched from Claude's Bash with run_in_background: true, so the
# harness fires exactly ONE completion notification. Read the printed AGY_STATUS
# block (and AGY_STDOUT) when it lands.
#
# Usage:
#   agy_run.sh [options] "<prompt>"
#
# Options:
#   --stall N         Log-silence threshold in seconds before declaring a stall
#                     (default 180). Healthy runs log every <4s, so 180 is safe.
#   --timeout DUR     Hard ceiling passed to agy --print-timeout AND enforced
#                     locally (e.g. 10m, 30m, 1h, 90s). Default 30m.
#   --check N         Liveness poll interval in seconds (default 10).
#   --label NAME      Used in output filenames (default: timestamp).
#   --outdir DIR      Where to write .log/.out/.status (default /tmp/agy-runs).
#   --add-dir PATH    Workspace dir for agy (repeatable). Default: $PWD.
#   --sandbox         Add --sandbox.
#   --skip-perms      Add --dangerously-skip-permissions (pair with --sandbox).
#   --continue        Add -c (resume most recent conversation).
#   --conversation U  Add --conversation U.
#   --raw "ARGS"      Extra raw agy flags, appended verbatim.
#
# Exit codes: 0 done · 1 stalled · 2 timeout · 3 launch/usage error · 4 auth/quota signal
set -uo pipefail

STALL=180; TIMEOUT="30m"; CHECK=10; LABEL=""; OUTDIR="/tmp/agy-runs"
SANDBOX=0; SKIP=0; CONT=0; CONV=""; RAW=""; PROMPT=""
ADD_DIRS=()

die(){ echo "agy_run: $*" >&2; echo "AGY_STATUS=error"; exit 3; }

while [ $# -gt 0 ]; do
  case "$1" in
    --stall)  STALL="$2"; shift 2;;
    --timeout) TIMEOUT="$2"; shift 2;;
    --check)  CHECK="$2"; shift 2;;
    --label)  LABEL="$2"; shift 2;;
    --outdir) OUTDIR="$2"; shift 2;;
    --add-dir) ADD_DIRS+=("$2"); shift 2;;
    --sandbox) SANDBOX=1; shift;;
    --skip-perms) SKIP=1; shift;;
    --continue) CONT=1; shift;;
    --conversation) CONV="$2"; shift 2;;
    --raw) RAW="$2"; shift 2;;
    --) shift; PROMPT="${1:-}"; shift || true;;
    -*) die "unknown option: $1";;
    *) PROMPT="$1"; shift;;
  esac
done
[ -n "$PROMPT" ] || die "missing prompt (last positional argument)"
command -v agy >/dev/null 2>&1 || die "agy not found in PATH"
[ ${#ADD_DIRS[@]} -gt 0 ] || ADD_DIRS=("$PWD")

# Portable duration -> seconds (e.g. 30m, 1h, 90s, 45 -> seconds).
to_secs(){ local d="$1" n="${1%[smh]}" u="${1: -1}"; case "$u" in
  s) echo "$n";; m) echo $((n*60));; h) echo $((n*3600));; *) echo "$d";; esac; }
CEIL=$(to_secs "$TIMEOUT")

# Portable mtime epoch.
mtime(){ stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null || echo 0; }

# All PIDs in a process tree (root first). Collected BEFORE killing so that
# terminating the parent can't reparent a child out of reach (the race that
# otherwise orphans agy's `sleep`/subprocess children).
descendants(){ local p=$1 c; echo "$p"; for c in $(pgrep -P "$p" 2>/dev/null); do descendants "$c"; done; }

mkdir -p "$OUTDIR" || die "cannot create $OUTDIR"
[ -n "$LABEL" ] || LABEL="$(date +%Y%m%d-%H%M%S)"
LOG="$OUTDIR/agy-$LABEL.log"
OUT="$OUTDIR/agy-$LABEL.out"
: > "$LOG"; : > "$OUT"

# Build the agy command.
CMD=(agy --log-file "$LOG" --print-timeout "$TIMEOUT")
for d in "${ADD_DIRS[@]}"; do CMD+=(--add-dir "$d"); done
[ "$SANDBOX" = 1 ] && CMD+=(--sandbox)
[ "$SKIP" = 1 ] && CMD+=(--dangerously-skip-permissions)
[ "$CONT" = 1 ] && CMD+=(-c)
[ -n "$CONV" ] && CMD+=(--conversation "$CONV")
# shellcheck disable=SC2206
[ -n "$RAW" ] && CMD+=($RAW)
CMD+=(-p "$PROMPT")

START=$(date +%s)
# Launch agy directly so $AGY_PID is the real process (not a wrapper subshell),
# then disown immediately so bash never prints an async "Terminated" notice when
# we kill a stalled run.
"${CMD[@]}" >"$OUT" 2>&1 &
AGY_PID=$!
disown "$AGY_PID" 2>/dev/null || true

STATUS="done"
while :; do
  sleep "$CHECK"
  NOW=$(date +%s); ELAPSED=$((NOW-START))
  if ! kill -0 "$AGY_PID" 2>/dev/null; then STATUS="done"; break; fi
  # Hard ceiling (belt-and-suspenders; agy --print-timeout should fire first).
  if [ "$ELAPSED" -gt $((CEIL+30)) ]; then STATUS="timeout"; break; fi
  # Stall: log file untouched for >= STALL seconds while process still alive.
  AGE=$(( NOW - $(mtime "$LOG") ))
  if [ "$AGE" -ge "$STALL" ]; then STATUS="stalled"; break; fi
done

if [ "$STATUS" != "done" ]; then
  # Stopping a live run. Snapshot the whole tree first, then signal all at once
  # so no child gets reparented out of reach.
  TREE=$(descendants "$AGY_PID")
  # shellcheck disable=SC2086
  kill -TERM $TREE 2>/dev/null
  for _ in 1 2 3 4 5; do kill -0 "$AGY_PID" 2>/dev/null || break; sleep 1; done
  # shellcheck disable=SC2086
  kill -KILL $TREE 2>/dev/null
fi
END=$(date +%s)

# A "done" status only means agy exited — not that it succeeded. Scan agy's
# STDOUT (not the noisy internal log, which mentions "quota" routinely and emits
# transient self-healing OAuth errors) for fatal auth/quota signatures. Patterns
# are qualified ("exceeded"/"unauthorized"/RESOURCE_EXHAUSTED) so they don't fire
# on a normal answer that merely discusses rate limiting.
ERR=$(grep -ioE 'RESOURCE_EXHAUSTED|quota exceeded|rate.?limit(ed|.{0,3}exceeded)|not logged in(to)?|unauthenticated|401 unauthorized|403 forbidden|token (has )?expired|invalid (api )?token' "$OUT" 2>/dev/null | head -1)

# Extract liveness/diagnostic signals from the log.
MODEL=$(grep -oE 'label="[^"]+"' "$LOG" 2>/dev/null | tail -1 | sed 's/label="//;s/"$//')
CONV_ID=$(grep -oE 'conversation [0-9a-f-]{36}' "$LOG" 2>/dev/null | tail -1 | awk '{print $2}')
LAST=$(grep -vE 'http_helpers|streamGenerate' "$LOG" 2>/dev/null | tail -1 | cut -c1-160)
BRAIN=""; [ -n "$CONV_ID" ] && BRAIN="$HOME/.gemini/antigravity-cli/brain/$CONV_ID"

echo "AGY_STATUS=$STATUS"
echo "AGY_LABEL=$LABEL"
echo "AGY_DURATION=$((END-START))s"
echo "AGY_MODEL=${MODEL:-unknown}"
echo "AGY_STDOUT=$OUT"
echo "AGY_LOG=$LOG"
[ -n "$BRAIN" ] && echo "AGY_BRAIN=$BRAIN"
echo "AGY_LAST_LOG=${LAST:-<none>}"
if [ -n "$ERR" ]; then
  echo "AGY_ERROR_SIGNAL=$ERR  (auth/quota/rate-limit detected — STOP, do not retry; back off >=60s)"
  exit 4
fi
case "$STATUS" in
  done) exit 0;;
  stalled) echo "AGY_HINT=Log silent >=${STALL}s. Likely a sandbox-escape approval prompt (needs --skip-perms), an SSE/network stall, or quota throttle. Inspect AGY_LOG tail before retrying."; exit 1;;
  timeout) echo "AGY_HINT=Hit the ${TIMEOUT} ceiling while still active. Raise --timeout or narrow the task."; exit 2;;
esac
