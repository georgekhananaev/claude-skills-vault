#!/usr/bin/env bash
# firebase-cli skill self-test.
#
#   ./self_test.sh                                    # static: syntax + classifier battery (no network)
#   ./self_test.sh --live --project <id>              # + read-only live checks against <id>
#   ./self_test.sh --live-write --project <id> --confirm <id>
#                                                     # + guarded write/cleanup round-trip.
#                                                     #   Writes ONLY namespaced test resources
#                                                     #   (hosting channel `skill-selftest`, RTDB
#                                                     #   path /__skill_selftest__) and deletes them.
#                                                     #   Use a DISPOSABLE project. The project id
#                                                     #   must be repeated via --confirm (guard
#                                                     #   against accidental/templated invocation).
#
# Exit 0 = all PASS (SKIPs allowed). Non-zero = at least one FAIL.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
RISK="$SCRIPT_DIR/firebase_risk.py"
FB_TIMEOUT="${FB_TIMEOUT:-180}"

LIVE=false; LIVE_WRITE=false; PROJECT=""; CONFIRM=""
while [ $# -gt 0 ]; do
  case "$1" in
    --live) LIVE=true ;;
    --live-write) LIVE=true; LIVE_WRITE=true ;;
    --project) PROJECT="${2:-}"; shift ;;
    --confirm) CONFIRM="${2:-}"; shift ;;
    *) echo "unknown arg: $1"; exit 2 ;;
  esac
  shift
done

PASS=0; FAIL=0; SKIP=0
pass() { PASS=$((PASS+1)); echo "  PASS  $1"; }
fail() { FAIL=$((FAIL+1)); echo "  FAIL  $1"; }
skip() { SKIP=$((SKIP+1)); echo "  SKIP  $1"; }
die()  { echo "FATAL: $1"; exit 2; }

# fail fast, before anything runs
if $LIVE; then [ -n "$PROJECT" ] || die "--live/--live-write requires --project <id>"; fi
if $LIVE_WRITE; then
  [ "$CONFIRM" = "$PROJECT" ] || die "--live-write guard: --confirm must repeat the exact project id"
fi

# Run firebase with a hard timeout so nothing can hang an agent session.
fb() { perl -e 'alarm shift @ARGV; exec @ARGV' "$FB_TIMEOUT" firebase "$@" 2>&1; }

# ---------------------------------------------------------------- static ----
echo "=== firebase-cli self-test: static ==="

command -v python3 >/dev/null 2>&1 || die "python3 not found"

for f in "$SCRIPT_DIR"/*.sh; do
  if bash -n "$f" 2>/dev/null; then pass "bash syntax: $(basename "$f")"
  else fail "bash syntax: $(basename "$f")"; fi
done
for f in "$SCRIPT_DIR"/*.py; do
  if python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$f" 2>/dev/null; then
    pass "python syntax: $(basename "$f")"
  else fail "python syntax: $(basename "$f")"; fi
done

if [ -f "$SKILL_DIR/SKILL.md" ] \
   && head -1 "$SKILL_DIR/SKILL.md" | grep -q '^---$' \
   && grep -q '^name: firebase-cli$' "$SKILL_DIR/SKILL.md" \
   && grep -q '^description:' "$SKILL_DIR/SKILL.md"; then
  pass "SKILL.md frontmatter (name + description)"
else
  fail "SKILL.md frontmatter (name + description)"
fi
for ref in safety-rules.md commands.md patterns.md; do
  if [ -s "$SKILL_DIR/references/$ref" ]; then pass "reference present: $ref"
  else fail "reference present: $ref"; fi
done

# --- classifier battery: expected exit code (0 safe, 10 write, 20 destructive,
# --- 30 forbidden, 2 error) vs actual ---
t() {
  local want="$1"; shift
  python3 "$RISK" "$1" >/dev/null 2>&1
  local got=$?
  if [ "$got" -eq "$want" ]; then pass "risk=$want  $1"
  else fail "risk: want $want, got $got  — $1"; fi
}

echo "--- classifier battery ---"
# safe
t 0 "firebase projects:list"
t 0 "firebase apps:list -P demo"
t 0 "firebase firestore:databases:list --json"
t 0 "firebase database:get /users --limit-to-first 5"
t 0 "firebase deploy --dry-run"
t 0 "firebase functions:log"
t 0 "firebase login:list"
t 0 "firebase emulators:exec 'npm test' --only firestore"
t 0 "firebase hosting:channel:list"
t 0 "firebase use"
t 0 "firebase --version"
t 0 "firebase remoteconfig:get -o rc.json"
t 0 "firebase auth:export users.json --format json"
t 0 "firebase functions:secrets:access MY_KEY"
t 0 "firebase emulators:start --only auth"
# write
t 10 "firebase deploy --only hosting"
t 10 "firebase apps:create WEB myapp"
t 10 "firebase database:push /logs -d '{\"a\":1}'"
t 10 "firebase database:update /cfg -d '{\"a\":1}'"
t 10 "firebase functions:secrets:set API_KEY"
t 10 "firebase hosting:channel:deploy preview-1"
t 10 "firebase use staging"
t 10 "firebase appdistribution:distribute app.apk"
t 10 "npx firebase-tools deploy --only hosting"
t 10 "firebase init hosting"
t 10 "firebase somefuture:newthing"
# destructive
t 20 "firebase firestore:delete /users/u1 -r"
t 20 "firebase firestore:bulkdelete --collection-ids users,orders"
t 20 "firebase database:remove /old-data"
t 20 "firebase database:set /config -d '{}'"
t 20 "firebase functions:delete myFunc --region us-central1"
t 20 "firebase hosting:disable"
t 20 "firebase remoteconfig:rollback -v 3"
t 20 "firebase auth:import users.json --hash-algo SCRYPT"
t 20 "firebase deploy --force"
t 20 "firebase ext:uninstall my-ext"
t 20 "firebase hosting:channel:delete pr-42"
t 20 "firebase appdistribution:distribute app.apk --groups qa"
t 20 "firebase hosting:clone site-a:live site-b:live"
t 20 "firebase -P prod firestore:delete /orders/x"
t 20 "firebase projects:create newproj"
t 20 "firebase dataconnect:execute mutation.gql"
t 20 "firebase logout"
t 20 "firebase somefuture:delete x"
t 20 "firebase projects:list && firebase database:remove /tmp"
# forbidden
t 30 "firebase firestore:delete --all-collections"
t 30 "firebase firestore:databases:delete mydb"
t 30 "firebase firestore:backups:delete some-backup"
t 30 "firebase hosting:sites:delete old-site"
t 30 "firebase functions:secrets:destroy API_KEY"
t 30 "firebase database:set / -d '{}'"
t 30 "firebase database:remove /"
t 30 "firebase functions:delete"
t 30 "echo hi && firebase firestore:delete --all-collections"
t 30 "cat ids.txt | xargs firebase functions:delete"
t 30 "for f in a b; do firebase functions:delete \$f; done"
# not-firebase / empty → parse error
t 2 "ls -la"
t 2 ""

# metadata fields
if python3 "$RISK" --json "firebase functions:secrets:access K" 2>/dev/null | grep -q '"sensitive": true'; then
  pass "sensitive flag on secrets:access"
else fail "sensitive flag on secrets:access"; fi
if python3 "$RISK" --json "firebase -P demo firestore:delete /x" 2>/dev/null | grep -q '"project": "demo"'; then
  pass "project extraction (-P before command)"
else fail "project extraction (-P before command)"; fi
if python3 "$RISK" --json "firebase emulators:start" 2>/dev/null | grep -q '"interactive": true'; then
  pass "interactive flag on emulators:start"
else fail "interactive flag on emulators:start"; fi

# ------------------------------------------------------------------ live ----
if $LIVE; then
  echo "=== live (read-only) against project: $PROJECT ==="
  command -v firebase >/dev/null 2>&1 || die "firebase CLI not installed"

  if bash "$SCRIPT_DIR/firebase_preflight.sh" "$PROJECT" >/dev/null 2>&1; then
    pass "preflight (auth + project '$PROJECT' accessible)"
  else
    fail "preflight — not authenticated or project '$PROJECT' not accessible"
  fi

  # universally-available reads — must succeed on any project
  for cmd in "apps:list" "hosting:sites:list"; do
    if fb $cmd -P "$PROJECT" --non-interactive --json | grep -q '"status": *"success"'; then
      pass "read: firebase $cmd"
    else fail "read: firebase $cmd"; fi
  done
  # feature reads — SKIP when the product/API isn't provisioned on the project
  for cmd in "firestore:databases:list" "functions:list" "database:instances:list" "remoteconfig:get"; do
    OUT="$(fb $cmd -P "$PROJECT" --non-interactive --json)"
    if echo "$OUT" | grep -q '"status": *"success"'; then pass "read: firebase $cmd"
    else skip "read: firebase $cmd (feature/API not provisioned)"; fi
  done
fi

# ------------------------------------------------------------ live-write ----
if $LIVE_WRITE; then
  echo "=== live-write against DISPOSABLE project: $PROJECT ==="
  CHANNEL="skill-selftest"
  CHANNEL_CREATED=false
  SITE=""

  # channel cmds need a firebase.json context — build a throwaway one
  WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/fb-selftest.XXXXXX")"
  printf '{"hosting":{"public":"."}}' > "$WORKDIR/firebase.json"
  cleanup() {
    if $CHANNEL_CREATED; then
      (cd "$WORKDIR" && fb hosting:channel:delete "$CHANNEL" --site "$SITE" -P "$PROJECT" --force --non-interactive >/dev/null)
    fi
    rm -rf "$WORKDIR"
  }
  trap cleanup EXIT
  cd "$WORKDIR" || die "cannot enter workdir"

  # every mutation is pre-classified — the same gate the skill mandates
  python3 "$RISK" "firebase hosting:channel:create $CHANNEL" >/dev/null 2>&1
  [ $? -eq 10 ] && pass "gate: channel:create classifies write(10)" || fail "gate: channel:create tier"
  python3 "$RISK" "firebase hosting:channel:delete $CHANNEL" >/dev/null 2>&1
  [ $? -eq 20 ] && pass "gate: channel:delete classifies destructive(20)" || fail "gate: channel:delete tier"

  # hosting channel round-trip on the project's default site
  SITE="$(fb hosting:sites:list -P "$PROJECT" --non-interactive --json | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
sites = (d.get("result") or {}).get("sites") or []
default = [s for s in sites if s.get("type") == "DEFAULT_SITE"] or sites
if default:
    print(default[0]["name"].rsplit("/", 1)[-1])
')"
  if [ -z "$SITE" ]; then
    skip "hosting round (project has no hosting site)"
  else
    OUT="$(fb hosting:channel:create "$CHANNEL" --site "$SITE" -P "$PROJECT" --expires 1h --non-interactive --json)"
    if echo "$OUT" | grep -q '"status": *"success"'; then
      CHANNEL_CREATED=true
      pass "write: hosting:channel:create $CHANNEL (site $SITE)"
      if fb hosting:channel:list --site "$SITE" -P "$PROJECT" --non-interactive --json | grep -q "channels/$CHANNEL\""; then
        pass "verify: channel visible in list"
      else fail "verify: channel visible in list"; fi
      if fb hosting:channel:delete "$CHANNEL" --site "$SITE" -P "$PROJECT" --force --non-interactive | grep -qi "deleted\|success"; then
        CHANNEL_CREATED=false
        pass "cleanup: hosting:channel:delete $CHANNEL"
        if fb hosting:channel:list --site "$SITE" -P "$PROJECT" --non-interactive --json | grep -q "channels/$CHANNEL\""; then
          fail "verify: channel gone after delete"
        else pass "verify: channel gone after delete"; fi
      else fail "cleanup: hosting:channel:delete $CHANNEL"; fi
    else
      fail "write: hosting:channel:create — $(echo "$OUT" | tr '\n' ' ' | head -c 200)"
    fi
  fi

  # RTDB round-trip (only if an instance already exists — NEVER auto-create:
  # instance names are reserved forever)
  INST="$(fb database:instances:list -P "$PROJECT" --non-interactive --json | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
res = d.get("result") or []
if isinstance(res, dict):
    res = res.get("instances") or []
for it in res:
    name = it.get("name") if isinstance(it, dict) else it
    if name:
        print(str(name).rsplit("/", 1)[-1]); break
')"
  if [ -n "$INST" ]; then
    P="/__skill_selftest__"
    if fb database:set "$P" -d '{"ping":true}' --instance "$INST" -P "$PROJECT" --force --non-interactive | grep -qi "data persisted\|success"; then
      pass "write: database:set $P (instance $INST)"
    else fail "write: database:set $P (instance $INST)"; fi
    if fb database:get "$P" --instance "$INST" -P "$PROJECT" --non-interactive | grep -q '"ping"'; then
      pass "verify: database:get returns written data"
    else fail "verify: database:get returns written data"; fi
    if fb database:remove "$P" --instance "$INST" -P "$PROJECT" --force --non-interactive | grep -qi "data removed\|success"; then
      pass "cleanup: database:remove $P"
    else fail "cleanup: database:remove $P"; fi
    if [ "$(fb database:get "$P" --instance "$INST" -P "$PROJECT" --non-interactive | tr -d '[:space:]')" = "null" ]; then
      pass "verify: path empty after remove"
    else fail "verify: path empty after remove"; fi
  else
    skip "RTDB round (no database instance on project — creating one is permanent, refusing)"
  fi
fi

# --------------------------------------------------------------- summary ----
echo "=== summary: $PASS passed, $FAIL failed, $SKIP skipped ==="
[ "$FAIL" -eq 0 ]
