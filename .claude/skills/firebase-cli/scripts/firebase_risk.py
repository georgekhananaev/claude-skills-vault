#!/usr/bin/env python3
"""Classify a Firebase CLI command by risk tier: safe | write | destructive | forbidden.

Usage:
    python3 firebase_risk.py "firebase firestore:delete --all-collections"
    python3 firebase_risk.py --json "firebase deploy --only hosting -P my-proj"

Exit codes: 0=safe, 10=write, 20=destructive, 30=forbidden, 2=parse error.

Deterministic pre-check before running any firebase command. Primary source of
truth is an exact-command table covering the full firebase-tools v15 surface;
unknown commands fall back to token inference and default to `write`
(fail-closed). Escalation-only: nothing lowers a table tier. Compound shell
commands (&&, ;, |, $()) are split and EVERY firebase invocation is classified
— the highest tier wins. xargs/for/while feeding a mutating firebase op
escalates (bulk = multiplied blast radius). The classifier is advisory — the
model must still apply judgment for context (prod vs test project).
"""

from __future__ import annotations

import json
import shlex
import sys

TIERS = ["safe", "write", "destructive", "forbidden"]
EXIT_CODE = {"safe": 0, "write": 10, "destructive": 20, "forbidden": 30}

SHELL_OPS = set("();<>|&")

# Global/common options that consume a value (skipped when locating the
# command token and positional args).
VALUE_FLAGS = {
    "-P", "--project", "--account", "--token", "-c", "--config",
    "-m", "--message", "--only", "--except", "--instance", "--database",
    "-d", "--data", "-s", "--site", "--region", "--format", "-o", "--output",
    "-e", "--expires", "-l", "--location", "--data-file", "-v", "--version-number",
    "--app", "--testers", "--testers-file", "--groups", "--groups-file",
    "--release-notes", "--release-notes-file", "--collection-ids", "--hash-algo",
    "--hash-key", "--salt-separator", "--rounds", "--mem-cost", "--parallelization",
    "--block-size", "--dk-len", "--hash-input-order", "-p", "--public",
    "--import", "--export-on-exit", "--log-verbosity", "--inspect-functions",
    "--order-by", "--limit-to-first", "--limit-to-last", "--start-at",
    "--end-at", "--equal-to", "--shallow-depth", "--backup", "--edition",
    "--delete-protection", "--point-in-time-recovery", "-k", "--kms-key-name",
}

# Alias → canonical command.
ALIASES = {
    "experimental:mcp": "mcp",
    "appdistribution:group:list": "appdistribution:groups:list",
    "appdistribution:group:create": "appdistribution:groups:create",
    "appdistribution:group:delete": "appdistribution:groups:delete",
    "functions:secrets:describe": "functions:secrets:get",
}

# Commands whose output contains secrets/PII — never echo into logs or chat.
SENSITIVE = {
    "functions:secrets:access": "prints a SECRET value — redirect to file/env, never display",
    "apphosting:secrets:access": "prints a SECRET value — redirect to file/env, never display",
    "functions:config:get": "config may contain API keys — don't echo into logs",
    "auth:export": "exports user PII (emails, phone numbers, password hashes)",
    "login:ci": "mints a long-lived auth token (deprecated) — treat as a credential",
}

# Commands that prompt, open a browser, or run forever — hang risk for agents.
INTERACTIVE = {
    "init": "interactive wizard — run yourself or answer prompts in a terminal",
    "login": "opens a browser for OAuth — needs a human",
    "functions:shell": "interactive REPL (and Admin SDK inside talks to PROD services)",
    "dataconnect:sql:shell": "interactive SQL shell against prod CloudSQL",
    "emulators:start": "runs until killed — use emulators:exec or run_in_background",
    "serve": "runs until killed — use run_in_background",
    "open": "opens a browser",
    "mcp": "long-running MCP server process",
    "apps:init": "prompts when platform/appId args are omitted",
    "use --add": "interactive project picker",
}

# command → (tier, reason). Complete firebase-tools v15 surface.
COMMANDS = {
    # --- session / meta ---
    "login": ("write", "starts a local auth session"),
    "login:add": ("write", "adds another authorized account"),
    "login:use": ("write", "switches the default account"),
    "login:list": ("safe", "lists authorized accounts"),
    "login:ci": ("write", "mints a long-lived CI token (deprecated)"),
    "logout": ("destructive", "ends the CLI session — breaks authenticated automation until re-login"),
    "help": ("safe", "help output"),
    "open": ("safe", "opens a console page in the browser"),
    "use": ("write", "changes the active project for this directory (.firebaserc)"),
    "target": ("safe", "lists deploy targets"),
    "target:apply": ("write", "maps a deploy target in .firebaserc (local)"),
    "target:clear": ("write", "clears a deploy target mapping (local)"),
    "target:remove": ("write", "removes a resource from a deploy target (local)"),
    "init": ("write", "writes firebase.json/.firebaserc in the current directory"),
    "experiments:list": ("safe", "lists CLI experiments"),
    "experiments:describe": ("safe", "describes a CLI experiment"),
    "experiments:enable": ("write", "enables a CLI experiment on this machine"),
    "experiments:disable": ("write", "disables a CLI experiment on this machine"),
    "mcp": ("safe", "runs the Firebase MCP server (local process)"),
    "studio:export": ("safe", "local export of a Firebase Studio app"),
    # --- projects / apps ---
    "projects:list": ("safe", "lists accessible projects"),
    "projects:create": ("destructive", "creates a GCP project — project ID is consumed FOREVER, new billable container"),
    "projects:addfirebase": ("write", "adds Firebase services to an existing GCP project"),
    "apps:list": ("safe", "lists registered apps"),
    "apps:create": ("write", "registers a new app in the project"),
    "apps:init": ("write", "downloads app config into the local project"),
    "apps:sdkconfig": ("safe", "prints client SDK config (public identifiers, not secrets)"),
    "apps:android:sha:list": ("safe", "lists SHA certificate hashes"),
    "apps:android:sha:create": ("write", "adds a SHA certificate hash"),
    "apps:android:sha:delete": ("destructive", "removes a SHA hash — can break Google Sign-In/dynamic links for released builds"),
    # --- deploy / hosting ---
    "deploy": ("write", "deploys code/rules/config to the project — replaces what is live"),
    "hosting:clone": ("write", "copies a hosting version between sites/channels"),
    "hosting:disable": ("destructive", "STOPS serving web traffic on the site"),
    "hosting:channel:create": ("write", "creates a preview channel"),
    "hosting:channel:deploy": ("write", "deploys to a preview channel (auto-expires)"),
    "hosting:channel:list": ("safe", "lists channels"),
    "hosting:channel:open": ("safe", "opens a channel URL"),
    "hosting:channel:delete": ("destructive", "deletes a channel and its deployed content"),
    "hosting:sites:create": ("write", "creates an additional hosting site"),
    "hosting:sites:get": ("safe", "prints site info"),
    "hosting:sites:list": ("safe", "lists sites"),
    "hosting:sites:delete": ("forbidden", "PERMANENTLY deletes the site, all versions and its URLs"),
    "serve": ("safe", "local static-assets server"),
    # --- functions ---
    "functions:list": ("safe", "lists deployed functions"),
    "functions:log": ("safe", "reads function logs"),
    "functions:shell": ("write", "local shell — but Admin SDK inside hits PROD services"),
    "functions:delete": ("destructive", "deletes deployed Cloud Functions"),
    "functions:config:get": ("safe", "reads env config (LEGACY — Runtime Config API shut down Dec 2025)"),
    "functions:config:set": ("write", "sets legacy env config — API shut down Dec 2025, use dotenv/secrets instead"),
    "functions:config:unset": ("destructive", "removes legacy env config values — lost unless exported first"),
    "functions:config:clone": ("destructive", "overwrites this project's legacy env config with another project's"),
    "functions:config:export": ("write", "exports legacy config to local dotenv files (the sanctioned migration)"),
    "functions:secrets:get": ("safe", "secret metadata only (no values)"),
    "functions:secrets:access": ("safe", "reads a secret VALUE"),
    "functions:secrets:set": ("write", "creates a new secret version (old versions kept)"),
    "functions:secrets:destroy": ("forbidden", "destroys a secret version — value UNRECOVERABLE, running functions may break"),
    "functions:secrets:prune": ("destructive", "destroys all unused secret versions — irreversible"),
    "functions:lifecycle:list": ("safe", "lists lifecycle hooks"),
    "functions:lifecycle:run": ("write", "runs a lifecycle hook"),
    "functions:artifacts:setpolicy": ("write", "sets auto-cleanup policy for old function container images"),
    # --- firestore ---
    "firestore:indexes": ("safe", "lists indexes"),
    "firestore:locations": ("safe", "lists available locations"),
    "firestore:delete": ("destructive", "deletes Firestore documents/collections — NO undo"),
    "firestore:bulkdelete": ("destructive", "bulk-deletes entire collection groups — NO undo"),
    "firestore:operations:list": ("safe", "lists admin operations"),
    "firestore:operations:describe": ("safe", "describes an admin operation"),
    "firestore:operations:cancel": ("destructive", "cancels an in-flight admin op — may leave partial state"),
    "firestore:databases:list": ("safe", "lists databases"),
    "firestore:databases:get": ("safe", "prints database info"),
    "firestore:databases:create": ("destructive", "creates an additional BILLABLE Firestore database"),
    "firestore:databases:update": ("destructive", "changes live database settings (delete-protection, PITR)"),
    "firestore:databases:delete": ("forbidden", "deletes an ENTIRE Firestore database and all its data"),
    "firestore:databases:restore": ("destructive", "restores a backup into a NEW billable database"),
    "firestore:databases:clone": ("destructive", "clones into a NEW billable database"),
    "firestore:backups:list": ("safe", "lists backups"),
    "firestore:backups:get": ("safe", "prints backup info"),
    "firestore:backups:delete": ("forbidden", "deletes a BACKUP — removes the safety net"),
    "firestore:backups:schedules:list": ("safe", "lists backup schedules"),
    "firestore:backups:schedules:create": ("write", "creates a backup schedule (protective)"),
    "firestore:backups:schedules:update": ("write", "updates a backup schedule"),
    "firestore:backups:schedules:delete": ("destructive", "stops scheduled backups"),
    # --- realtime database ---
    "database:get": ("safe", "reads data at a path"),
    "database:profile": ("safe", "usage profiling report"),
    "database:push": ("write", "appends a new child node (additive)"),
    "database:update": ("write", "merges given keys at a path (other keys untouched)"),
    "database:import": ("write", "imports JSON children at a path — conflicting keys are overwritten"),
    "database:set": ("destructive", "REPLACES all data at the path — children not in payload are deleted"),
    "database:remove": ("destructive", "deletes all data at the path"),
    "database:instances:list": ("safe", "lists RTDB instances"),
    "database:instances:create": ("destructive", "creates an RTDB instance — the name is reserved FOREVER, billable on Blaze"),
    "database:settings:get": ("safe", "reads a database setting"),
    "database:settings:set": ("write", "changes a live database setting"),
    # --- auth ---
    "auth:export": ("safe", "exports user accounts to a local file"),
    "auth:import": ("destructive", "bulk-imports users — matching UIDs silently REPLACE existing accounts, and the CLI never prompts"),
    # --- remote config ---
    "remoteconfig:get": ("safe", "fetches the RC template"),
    "remoteconfig:rollback": ("destructive", "changes the LIVE config served to every app instance"),
    "remoteconfig:versions:list": ("safe", "lists template versions"),
    "remoteconfig:rollouts:get": ("safe", "prints a rollout"),
    "remoteconfig:rollouts:list": ("safe", "lists rollouts"),
    "remoteconfig:rollouts:delete": ("destructive", "deletes a live rollout"),
    "remoteconfig:experiments:get": ("safe", "prints an experiment"),
    "remoteconfig:experiments:list": ("safe", "lists experiments"),
    "remoteconfig:experiments:delete": ("destructive", "deletes an experiment and its results"),
    # --- emulators (local-only) ---
    "emulators:start": ("safe", "local emulators"),
    "emulators:exec": ("safe", "local emulators + script, auto-shutdown"),
    "emulators:export": ("safe", "exports local emulator data"),
    "setup:emulators:database": ("safe", "downloads emulator binary"),
    "setup:emulators:firestore": ("safe", "downloads emulator binary"),
    "setup:emulators:pubsub": ("safe", "downloads emulator binary"),
    "setup:emulators:storage": ("safe", "downloads emulator binary"),
    "setup:emulators:ui": ("safe", "downloads emulator binary"),
    "setup:emulators:dataconnect": ("safe", "downloads emulator binary"),
    # --- app distribution ---
    "appdistribution:distribute": ("write", "uploads a release binary"),
    "appdistribution:testers:list": ("safe", "lists testers"),
    "appdistribution:testers:add": ("write", "adds testers"),
    "appdistribution:testers:remove": ("destructive", "removes testers from the project"),
    "appdistribution:groups:list": ("safe", "lists groups"),
    "appdistribution:groups:create": ("write", "creates a tester group"),
    "appdistribution:groups:delete": ("destructive", "deletes a tester group"),
    "appdistribution:testcases:export": ("safe", "exports test cases to local YAML"),
    "appdistribution:testcases:import": ("write", "imports test cases"),
    "apptesting:execute": ("write", "runs automated tests on a binary (billable device time)"),
    # --- app hosting ---
    "apphosting:backends:list": ("safe", "lists backends"),
    "apphosting:backends:get": ("safe", "prints backend info"),
    "apphosting:backends:create": ("destructive", "creates a BILLABLE App Hosting backend (Cloud Run + builds)"),
    "apphosting:backends:delete": ("destructive", "deletes a backend — live serving stops, rollout history gone"),
    "apphosting:secrets:set": ("write", "creates a new secret version"),
    "apphosting:secrets:describe": ("safe", "secret metadata only"),
    "apphosting:secrets:access": ("safe", "reads a secret VALUE"),
    "apphosting:secrets:grantaccess": ("destructive", "grants principals access to secrets (IAM expansion)"),
    "apphosting:secrets:revokeaccess": ("destructive", "revokes secret access — running backends may break"),
    "apphosting:rollouts:create": ("destructive", "rolls a build out to LIVE traffic"),
    # --- crashlytics ---
    "crashlytics:symbols:upload": ("write", "uploads native symbols"),
    "crashlytics:mappingfile:upload": ("write", "uploads a ProGuard/R8 mapping file"),
    "crashlytics:mappingfile:generateid": ("safe", "writes a mapping ID into a local resource file"),
    # --- data connect ---
    "dataconnect:services:list": ("safe", "lists deployed services"),
    "dataconnect:compile": ("safe", "local schema/connector compile"),
    "dataconnect:sdk:generate": ("safe", "generates typed SDKs locally"),
    "dataconnect:sql:diff": ("safe", "diffs local schema vs CloudSQL (read-only)"),
    "dataconnect:sql:setup": ("destructive", "provisions/configures CloudSQL — significant ongoing cost"),
    "dataconnect:sql:migrate": ("destructive", "migrates the CloudSQL schema — column drops LOSE data"),
    "dataconnect:sql:grant": ("destructive", "grants a SQL role (security change)"),
    "dataconnect:sql:shell": ("destructive", "arbitrary SQL against prod CloudSQL"),
    "dataconnect:execute": ("destructive", "executes an arbitrary query/MUTATION against prod (emulator only if FIREBASE_DATA_CONNECT_EMULATOR_HOST set)"),
    # --- extensions ---
    "ext": ("safe", "extensions help/info"),
    "ext:list": ("safe", "lists installed extensions"),
    "ext:info": ("safe", "prints extension info"),
    "ext:export": ("safe", "exports extension manifests to local firebase.json"),
    "ext:install": ("write", "adds an extension to firebase.json (deploys billable resources on `firebase deploy`)"),
    "ext:update": ("write", "updates an extension version — review CHANGELOG for breaking changes"),
    "ext:configure": ("write", "reconfigures an extension instance"),
    "ext:uninstall": ("destructive", "uninstalls an extension — its resources and data may be deleted"),
    "ext:sdk:install": ("safe", "generates a local SDK for an extension"),
    "ext:dev:init": ("safe", "local extension scaffold"),
    "ext:dev:list": ("safe", "lists your published extensions"),
    "ext:dev:usage": ("safe", "extension usage stats"),
    "ext:dev:register": ("write", "registers a publisher ID"),
    "ext:dev:upload": ("destructive", "publishes an extension version to the PUBLIC registry"),
    "ext:dev:deprecate": ("destructive", "deprecates published versions — affects all consumers"),
    "ext:dev:undeprecate": ("write", "un-deprecates published versions"),
}

# RTDB data commands: (tier at root path "/"). Root = whole-database blast radius.
RTDB_ROOT_ESCALATION = {
    "database:set": ("forbidden", "REPLACES the ENTIRE database contents"),
    "database:remove": ("forbidden", "DELETES the ENTIRE database contents"),
    "database:update": ("destructive", "overwrites top-level keys of the entire database"),
    "database:import": ("destructive", "bulk-overwrites top-level keys of the entire database"),
}

DESTRUCTIVE_HINTS = ("delete", "remove", "destroy", "rollback", "uninstall",
                     "prune", "disable", "deprecate", "cancel", "revoke")
SAFE_HINTS = ("list", "get", "describe", "log", "info", "export", "open",
              "locations", "diff", "profile", "sdkconfig", "usage")


def _tier_max(a: str, b: str) -> str:
    return a if TIERS.index(a) >= TIERS.index(b) else b


def split_segments(command: str) -> list[list[str]]:
    """Split a shell command line into simple-command token segments.

    shlex with punctuation_chars keeps quoted values (JSON payloads, paths)
    intact while &&, ||, ;, |, (), <> split segments.
    """
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    try:
        tokens = list(lex)
    except ValueError as e:
        raise ValueError(f"unparseable command: {e}") from None
    segments: list[list[str]] = []
    current: list[str] = []
    for t in tokens:
        if t and all(c in SHELL_OPS for c in t):
            if current:
                segments.append(current)
                current = []
        else:
            current.append(t)
    if current:
        segments.append(current)
    return segments


def _is_firebase_token(t: str) -> bool:
    base = t.split("@", 1)[0]
    return base in ("firebase", "firebase-tools") or base.endswith("/firebase")


def _find_firebase(seg: list[str]) -> int:
    """Index of the firebase binary token; handles `npx [flags] firebase[-tools]`."""
    for i, t in enumerate(seg):
        if _is_firebase_token(t):
            return i
    return -1


def _flag_value(tokens: list[str], *flags: str) -> str | None:
    for i, t in enumerate(tokens):
        for flag in flags:
            if t == flag and i + 1 < len(tokens):
                return tokens[i + 1]
            if t.startswith(flag + "="):
                return t.split("=", 1)[1]
    return None


def _command_and_args(tokens: list[str]) -> tuple[str, list[str]]:
    """Return (command, positional_args) from tokens after the binary.

    Global flags may precede the command (`firebase -P x deploy`); value flags
    consume the next token.
    """
    positional: list[str] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in VALUE_FLAGS:
            i += 2
            continue
        if t.startswith("-"):
            if "=" not in t and t.lstrip("-") == "":
                pass  # bare "-"/"--" separator
            i += 1
            continue
        positional.append(t)
        i += 1
    if not positional:
        raise ValueError("no firebase command found")
    cmd = positional[0].lower()
    cmd = ALIASES.get(cmd, cmd)
    return cmd, positional[1:]


def _fallback_tier(cmd: str) -> tuple[str, str]:
    parts = cmd.replace(":", "-").split("-")
    if any(p in DESTRUCTIVE_HINTS for p in parts):
        return "destructive", f"unknown command `{cmd}` w/ destructive-looking token — verify in docs"
    if any(p in SAFE_HINTS for p in parts):
        return "write", f"unknown command `{cmd}` looks read-only but is not in the audited table — treat as write"
    return "write", f"unknown command `{cmd}` — not in the audited v15 table, verify in docs"


def _classify_tokens(tokens: list[str]) -> dict:
    if not tokens or any(t in ("--help", "-h", "--version", "-V") for t in tokens):
        return {"command": "help", "tier": "safe",
                "reason": "help/version — nothing executes"}
    cmd, args = _command_and_args(tokens)
    base = {
        "command": cmd,
        "project": _flag_value(tokens, "-P", "--project"),
        "instance": _flag_value(tokens, "--instance"),
        "database": _flag_value(tokens, "--database"),
        "site": _flag_value(tokens, "-s", "--site"),
    }
    notes: list[str] = []

    if cmd == "deploy" and "--dry-run" in tokens:
        return {**base, "tier": "safe", "reason": "deploy --dry-run — validates and builds, deploys nothing"}
    if cmd == "use" and not args and "--clear" not in tokens and "--add" not in tokens:
        return {**base, "tier": "safe", "reason": "shows the active project (no change)"}

    if cmd in COMMANDS:
        tier, reason = COMMANDS[cmd]
    else:
        tier, reason = _fallback_tier(cmd)

    # --- per-command escalations (escalation-only) ---
    if cmd == "firestore:delete":
        if "--all-collections" in tokens:
            tier, reason = "forbidden", "wipes EVERY collection in the Firestore database"
        elif "-r" in tokens or "--recursive" in tokens:
            notes.append("recursive — everything under the path is deleted")
    if cmd == "functions:delete" and not args:
        tier, reason = "forbidden", "functions:delete with NO filter — could target every function"
    if cmd in RTDB_ROOT_ESCALATION and args and args[0].strip() in ("/", "/."):
        esc_tier, esc_reason = RTDB_ROOT_ESCALATION[cmd]
        if TIERS.index(esc_tier) > TIERS.index(tier):
            tier, reason = esc_tier, f"root path `/` — {esc_reason}"
    if cmd == "hosting:clone" and any(a.endswith(":live") for a in args):
        tier = _tier_max(tier, "destructive")
        reason = "clone target is a LIVE channel — replaces prod content instantly"
    if cmd == "appdistribution:distribute" and any(
        f in tokens or _flag_value(tokens, f) for f in
        ("--testers", "--testers-file", "--groups", "--groups-file")
    ):
        tier = _tier_max(tier, "destructive")
        reason = "distributes the build to REAL testers (sends notifications)"
    if cmd == "functions:secrets:set" and ("-f" in tokens or "--force" in tokens):
        notes.append("--force auto-REDEPLOYS every function that uses this secret")
    if cmd == "deploy":
        only = _flag_value(tokens, "--only") or ""
        if "-f" in tokens or "--force" in tokens:
            tier = _tier_max(tier, "destructive")
            reason = "deploy --force DELETES functions missing from the local source"
        if any(t in only for t in ("firestore", "database", "storage")) or (not only and "--except" not in " ".join(tokens)):
            notes.append("deploy replaces LIVE security rules for included targets")
        if not only:
            notes.append("no --only — deploys ALL configured targets")
    elif ("-f" in tokens or "--force" in tokens) and tier in ("destructive", "forbidden"):
        notes.append("--force bypasses the CLI's own confirmation prompt")

    if cmd in SENSITIVE:
        base["sensitive"] = True
        notes.append(f"SENSITIVE: {SENSITIVE[cmd]}")
    interactive_key = "use --add" if (cmd == "use" and "--add" in tokens) else cmd
    if interactive_key in INTERACTIVE:
        base["interactive"] = True
        notes.append(f"INTERACTIVE/LONG-RUNNING: {INTERACTIVE[interactive_key]}")
    if _flag_value(tokens, "--token"):
        notes.append("--token is deprecated and puts a credential on the command line")

    if notes:
        reason += " · " + " · ".join(notes)
    return {**base, "tier": tier, "reason": reason}


def classify(command: str) -> dict:
    """Classify a full command line; compound commands → highest tier wins."""
    segments = split_segments(command)
    loop_ctx = any(s and s[0] in ("for", "while", "until") for s in segments)
    results = []
    for seg in segments:
        idx = _find_firebase(seg)
        if idx < 0:
            continue
        r = _classify_tokens(seg[idx + 1:])
        if "xargs" in seg[:idx] or loop_ctx:
            if r["tier"] in ("destructive", "forbidden"):
                r["tier"] = "forbidden"
                r["reason"] = f"BULK loop over a destructive op ({r['reason']}) — multiplied blast radius"
            elif r["tier"] == "write":
                r["tier"] = "destructive"
                r["reason"] = f"bulk mutation via xargs/loop ({r['reason']})"
        results.append(r)
    if not results:
        raise ValueError("not a `firebase` command")
    worst = max(results, key=lambda r: TIERS.index(r["tier"]))
    if len(results) > 1:
        worst = dict(worst)
        worst["segments"] = len(results)
        worst["reason"] += f" · compound command: {len(results)} firebase invocations, highest tier shown"
    return worst


def main() -> int:
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    if not args:
        print("usage: firebase_risk.py [--json] '<firebase command>'", file=sys.stderr)
        return 2
    try:
        result = classify(" ".join(args))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if as_json:
        print(json.dumps(result))
    else:
        ctx = "".join(
            f" {k}={result[k]}" for k in ("project", "instance", "database", "site")
            if result.get(k)
        )
        print(f"{result['tier'].upper()}: {result['reason']} [{result['command']}{ctx}]")
    return EXIT_CODE[result["tier"]]


if __name__ == "__main__":
    sys.exit(main())
