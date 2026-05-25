---
name: agy-cli
description: Run Google's Antigravity CLI (`agy`) — an agentic coding assistant powered by Gemini 3 (with Claude/GPT model access). Use when the user says "run/ask/use agy", "antigravity", wants a second-opinion audit from Gemini's agentic stack, or wants Claude to delegate a build/refactor task with the three effort tiers: default chat (fast), `/grill-me` (interactive planning), or `/goal` (autonomous long-running execution). Knows the real REPL slash commands, the headless `-p` flag, conversation resume, sandboxing, plugins, and the on-disk state layout under `~/.gemini/antigravity-cli/`.
---

# Antigravity CLI (`agy`)

Google's agentic coding CLI. Runs Gemini 3 (Pro/Flash) by default, with internal access to Claude Sonnet/Opus 4.5/4.6 and GPT-OSS models. Pairs a chat REPL with planning, scheduling, and autonomous "goal" workflows that write `implementation_plan.md` + `task.md` to a per-conversation brain directory and emit project files into the workspace.

Use it when the user:
- says "run/ask/use agy" or "antigravity"
- wants a second opinion from Gemini's agentic loop (Claude is the primary, agy is the audit/delegate)
- wants Claude to delegate a multi-step build, refactor, or research task to a different model family
- specifically asks to compare effort tiers (default vs. `/grill-me` vs. `/goal`)

## Prerequisites

Already installed on this user's system at `/Users/george/.local/bin/agy`. For others:

```bash
# Verify install + login
agy changelog                  # prints version notes (no --version flag exists)
agy install                    # configure PATH + shell aliases (idempotent)
```

First-time login is interactive (OAuth via browser). State lives at `~/.gemini/antigravity-cli/`.

## The Three Effort Tiers (the key mental model)

This is what the user means by "difference between efforts." Same prompt, very different behavior:

| Tier | How to invoke | Latency | What it does |
|------|---------------|---------|--------------|
| **Default chat** | `agy -p "<prompt>"` or just type in REPL | seconds | One-shot answer or short tool-use loop. Outline-level depth. Best for Q&A, quick edits. |
| **`/grill-me`** | Type `/grill-me <idea>` in REPL | interactive | Interviews you to extract requirements, resolve design ambiguities, and align on a plan **before** writing code. Use when the idea is vague. |
| **`/goal`** | `/goal <objective>` in REPL or `agy -p "/goal <objective>"` | minutes → hour+ | Autonomous loop: drafts `implementation_plan.md`, writes a `task.md` checklist, spawns research subagents, creates project files, runs tests, iterates until done. Persists to `~/.gemini/antigravity-cli/brain/<convo-id>/`. |

**Verified timing on this machine** (plan a Pomodoro CLI in Python):
- plain `-p`: ~18s → returns a written outline
- `-p "/goal …"`: ~73s → creates `pyproject.toml`, `pomodoro/{config,database,timer,ui,cli}.py`, `tests/test_pomodoro.py`, runs the test suite, writes `task.md` + `walkthrough.md`

Rule of thumb: pick `/goal` only when you actually want files on disk and are OK waiting. Bump `--print-timeout` for headless `/goal` runs (default 5m is often not enough).

## Headless usage (the only safe mode for automation)

`agy` interactive mode requires a real TTY (`bubbletea: could not open TTY` if you try to pipe into it). For Claude-driven invocations always use `-p`.

```bash
# One-shot prompt, prints to stdout
agy -p "Refactor this function for readability: $(cat foo.py)"

# Bump timeout for /goal runs (default --print-timeout is 5m0s)
agy --print-timeout 30m -p "/goal Build a CLI Pomodoro tool in Python with SQLite history"

# Add extra workspace directories the agent may read/edit
agy --add-dir ./api --add-dir ./web -p "Audit cross-package type mismatches"

# Auto-approve every tool/permission prompt (DESTRUCTIVE — see safety)
agy --dangerously-skip-permissions -p "/goal Migrate db schema and update callers"

# Run inside the built-in restricted sandbox (safer auto-approval)
agy --sandbox --dangerously-skip-permissions -p "/goal Try three refactor approaches"

# Initial prompt then drop into interactive (won't work from Claude — no TTY)
agy -i "Start a fastify scaffold"
```

## Efficient execution (do not idle-wait)

`--print-timeout` is a **ceiling**, not a sleep. `agy -p` exits the instant the model finishes — a `30m` timeout on a job that completes in 45s exits in 45s. The only way Claude can waste those 29 idle minutes is by **polling** the output file in a sleep loop instead of letting the harness notify on process exit.

**Always run `agy -p` with `run_in_background: true` and let the task-completion notification wake Claude.** The harness streams the exit event the moment the process ends; no polling, no sleeps, no extra cost.

```text
# RIGHT — fires Claude exactly when agy exits, whether that's 30s or 30m
Bash(command="agy --add-dir \"$(pwd)\" --print-timeout 30m -p \"/goal ...\"",
     run_in_background=true)
# → wait for the task-completion notification, then Read the output file

# WRONG — burns wall-clock time and prompt cache
Bash(command="agy ... -p \"/goal ...\"")            # foreground blocks Claude
sleep 600 && cat /tmp/agy.out                       # polling = idle waste
```

Sizing the timeout:

| Task shape | Suggested `--print-timeout` |
|------------|------------------------------|
| Q&A, short generation, code review of a file or two | omit (default 5m is plenty) |
| Multi-file audit, small refactor | `10m` |
| `/goal` for a feature in an existing codebase | `20m` |
| `/goal` for a from-scratch project or large migration | `45m`–`1h` |

Pick generously — early exit is free, late exit kills the run mid-thought.

For very long `/goal` runs also pass `--log-file /tmp/agy-<task>.log` so progress is inspectable while it works, without re-running the prompt.

### Resuming conversations

agy persists every conversation as a `.pb` proto file in `~/.gemini/antigravity-cli/conversations/` and a matching brain dir at `~/.gemini/antigravity-cli/brain/<uuid>/`.

```bash
agy -c -p "Continue from where we left off"          # resume most recent
agy --conversation <uuid> -p "Add tests for X"        # resume a specific one
ls ~/.gemini/antigravity-cli/conversations/           # find UUIDs
```

## REPL slash commands (verified from changelog + live test)

These only work **inside the interactive REPL** (or as the first token of a `-p` prompt for `/goal`, `/grill-me`, `/schedule`):

| Command | Purpose |
|---------|---------|
| `/help` | Tabbed help: Commands + Shortcuts (sorted by keybinding) |
| `/goal <objective>` | Autonomous long-running build/refactor (see effort tiers above) |
| `/grill-me <idea>` | Interactive interview to align on a plan before coding |
| `/schedule <spec>` | One-shot timer or cron-style recurring background task |
| `/diff` | Interactive commit selection tree (supports 7- to 40-char git short hashes) |
| `/resume` | Pick a prior session to resume (use `ctrl+delete` to remove sessions) |
| `/usage` | Real-time quota + spending across models |
| `/quota` | Remaining quota for each model |
| `/config` | Open the in-app configuration UI |
| `/settings` | Theme + tool permission modes (`request-review`, `auto-approve`, `proceed-in-sandbox`) |
| `/statusline <help\|enable\|on\|disable\|off\|delete\|reset>` | Manage custom status line |

> Do **not** trust any other slash command list a model claims `agy` has — many are commonly hallucinated (e.g. `/model`, `/effort`, `/thinking`, `/agents`, `/keybindings`, `/export`, `/permissions`, `/switch`, `/rewind`, `/undo`). They are not in the changelog. If unsure, run `/help` interactively.

There is **no CLI flag** for model selection or reasoning effort (`--model`, `--effort`, `--reasoning`, `--thinking` all error with `flags provided but not defined`). Model + effort are set inside `/settings` and `/config`.

## Subcommands

```bash
agy changelog                # release notes (also the only way to see version)
agy update                   # in-place updater
agy install [--skip-aliases] [--skip-path] [--dir <path>]
agy plugin list
agy plugin import [gemini|claude]
agy plugin install <name[@marketplace]>
agy plugin uninstall <name>
agy plugin enable|disable <name>
agy plugin validate [path]
agy plugin link <marketplace> <target>
```

Plugins install into `~/.gemini/config/` (shared with Gemini CLI) since v1.0.2.

## Flag reference

| Flag | Description |
|------|-------------|
| `-p`, `--print`, `--prompt` | **Required for headless.** Run one prompt, print the response, exit |
| `-i`, `--prompt-interactive` | Run an initial prompt then continue interactively (needs TTY) |
| `-c`, `--continue` | Resume the most recent conversation |
| `--conversation <uuid>` | Resume a specific conversation by ID |
| `--add-dir <path>` | Add a directory to the workspace (repeatable) |
| `--sandbox` | Run with terminal sandbox restrictions enabled |
| `--dangerously-skip-permissions` | Auto-approve all tool permission requests |
| `--print-timeout <duration>` | Timeout for `-p` (default `5m0s`; bump for `/goal`) |
| `--log-file <path>` | Override CLI log file path |

## Environment variables

| Var | Effect |
|-----|--------|
| `AGY_CLI_HIDE_ACCOUNT_INFO=T` | Hide email + plan tier from header |
| `AGY_CLI_DISABLE_AUTO_UPDATE=F` | Disable nightly auto-update check |
| `AGY_BROWSER_WS_URL` / `AGY_BROWSER_ACTIVE_PORT_FILE` | Point browser-automation tool at a specific Chrome DevTools endpoint |

## On-disk layout (useful for debugging + recovery)

```
~/.gemini/antigravity-cli/
├── conversations/<uuid>.pb       # full chat history (protobuf)
├── brain/<uuid>/                 # per-conversation planning state
│   ├── implementation_plan.md    # written by /goal
│   ├── task.md                   # live checklist
│   └── walkthrough.md            # post-run summary
├── scratch/                      # default workspace when none specified
├── log/cli-YYYYMMDD_HHMMSS.log   # CLI logs (current also at cli.log symlink)
├── settings.json                 # theme + trustedWorkspaces
├── keybindings.json
├── history.jsonl                 # prompt history
└── installation_id
```

When a `/goal` run finishes, **read its `walkthrough.md` and `task.md`** from the matching brain dir to summarize what it actually did — the final stdout often only lists files.

## Critical gotchas

1. **No TTY = no REPL.** Anything other than `agy -p …` will fail with `bubbletea: could not open TTY` when invoked from Claude's Bash. Always use `-p`.
2. **Print timeout kills `/goal`.** Default 5 minutes is short for autonomous builds — pass `--print-timeout 20m` or longer. (Long timeout ≠ long wait; see "Efficient execution" above.)
3. **`/help` in `-p` mode is just a prompt.** The model will hallucinate slash commands it doesn't have. The list above is the verified one.
4. **`--dangerously-skip-permissions` lets agy run any shell command and edit any file in the workspace without asking.** Pair with `--sandbox` and a narrowly scoped `--add-dir` when delegating from Claude.
5. **No `--model` / `--effort` flag exists.** Effort = which slash command you prefix. Model = `/settings` inside the REPL.
6. **Workspace defaults to `~/.gemini/antigravity-cli/scratch`** if not invoked from a trusted directory. Use `--add-dir $(pwd)` when running headless so the agent operates on your actual project.
7. **`agy` drops `.antigravitycli/` into the workspace root** the first time it's run there — a symlink folder pointing to `~/.gemini/config/projects/<uuid>.json`. Add `.antigravitycli/` to `.gitignore` (already done in this repo).

## Staying under quota and not tripping abuse heuristics

Antigravity rides on a single OAuth session against Google's Gemini/Antigravity backend. Behaviour that looks bot-like or abusive can throttle or temporarily lock the account. Follow these rules whenever Claude is the one invoking `agy`:

**Concurrency**
- **Never run two `agy -p` processes in parallel.** They share the same OAuth quota and trigger rate-limit responses (and the abuse heuristics that follow them). Serialize calls — if Claude has three things to ask, send them as three sequential prompts or, better, one combined prompt.
- Use `-c` / `--conversation <uuid>` to extend an existing chat instead of spawning fresh sessions; fewer cold starts means fewer auth refreshes and fewer "new session" signals.

**Prompt shape**
- Be explicit about expected output length ("answer in ≤5 bullets", "code-only, no commentary"). `/goal` charges per tool-use turn — vague goals mean more turns.
- Reserve `/goal` for work that genuinely needs file-writing autonomy. Default-chat answers a code question for a fraction of the quota.
- Don't loop `/goal` calls without backoff. If a `/goal` failed, fix the prompt before re-running — don't re-fire it three times in a row.

**Monitoring**
- Before a big delegated run, the user can check headroom interactively with `/usage` and `/quota`. There is no headless equivalent today; if Claude sees `429`, `quota`, `rate limit`, or `RESOURCE_EXHAUSTED` in agy's output, **stop and report — do not retry**.
- On 429, back off at least 60s before any subsequent call, and prefer a smaller default-chat prompt to confirm the account is live before resuming `/goal` work.

**Environment**
- Set `AGY_CLI_DISABLE_AUTO_UPDATE=T` in CI/scripted contexts so each invocation doesn't ping the update endpoint.
- Set `AGY_CLI_HIDE_ACCOUNT_INFO=T` if streaming agy output anywhere shareable, to keep the user's email and plan tier out of logs.
- Do **not** wrap `agy` in retry-on-failure loops (`while ! agy …; do …; done`). Failed auth or quota errors must surface, not auto-retry.

**Sandboxing**
- `--dangerously-skip-permissions` without `--sandbox` is both a security risk **and** a quota risk — an unconstrained agent can spiral into long tool-use chains. Always pair the two for delegated `/goal` runs, plus a narrow `--add-dir`.

## Recommended invocation patterns

```bash
# Second-opinion code audit (read-only intent)
agy --add-dir "$(pwd)" -p "Audit src/auth/ for OWASP issues. Report only — do not modify files."

# Quick Q&A / one-shot generation
agy -p "Write a regex that matches RFC 5322 email addresses, with one-line explanation."

# Delegated build (autonomous, expect minutes)
agy --add-dir "$(pwd)" --print-timeout 30m \
    -p "/goal Add a /healthz endpoint to the Fastify server in src/api with a unit test."

# Interview-first design alignment (must be interactive — tell the user to run it themselves)
# In REPL: /grill-me Build a Slack bot that summarizes our standup channel daily

# Recurring background task (interactive only)
# In REPL: /schedule every weekday at 09:00 run "Summarize yesterday's git log and post to #eng"

# Resume the last conversation with new instructions
agy -c --add-dir "$(pwd)" -p "Now add error handling to the route we built"
```

## Best practices (quick checklist)

- Default to `-p` + a precise prompt. Don't escalate to `/goal` for things a short prompt can answer.
- Use `/goal` only when you want files on disk; pair with `--print-timeout` ≥ `20m`, `--add-dir "$(pwd)"`, and `run_in_background: true`.
- `--print-timeout` is a ceiling, not a sleep — make it generous, let exit-notification wake Claude (see "Efficient execution").
- `/grill-me` is interactive-only — instruct the user to run it themselves; Claude cannot drive it through Bash.
- For risky delegated work: `--sandbox` + `--dangerously-skip-permissions` + narrow `--add-dir`. Never the middle two without the first.
- Serialize agy calls. Never run two in parallel. On `429` / quota errors: stop, report, do not retry.
- Reuse conversations with `-c` instead of starting fresh sessions when continuing the same thread.
- After a `/goal` run, read `~/.gemini/antigravity-cli/brain/<latest-uuid>/walkthrough.md` for a faithful summary of what changed.
- Don't trust any slash command the model invents — only the verified list above is real.
- Comparison workflow: state Claude's answer first, then run the same prompt via `agy -p`. Pick `/goal` mode only when the user wants both agents to *implement*, not just opine.
