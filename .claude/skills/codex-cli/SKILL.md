---
name: codex-cli
description: Run OpenAI Codex CLI for coding tasks and second-opinion audits. Use when a user asks to run/ask/use Codex, says "codex prompt", or wants Claude to delegate a logic/code review to OpenAI models. Covers direct `codex` CLI invocation (exec, review, resume, apply, doctor, mcp), the six reasoning-effort levels (none/minimal/low/medium/high/xhigh), sandbox + dangerous flags, background execution, rate-limit safety, and when to defer to the official OpenAI Codex Claude Code plugin (`codex:rescue`) instead. Preflights with `codex doctor` to read the current default model + surface available updates; never hardcodes model/effort, letting Codex pick its own current best default unless the user explicitly names one.
---

# Codex CLI

OpenAI's local agentic coding CLI (`codex`, v0.132+). Runs the GPT-5 family by default (current default: `gpt-5.5`) and supports OSS providers (ollama, lmstudio). Use for second-opinion audits, delegated builds, review of uncommitted diffs, and non-interactive task execution.

## First: prefer the Codex Claude Code plugin when it's installed

If the user has the official `openai-codex` plugin in `~/.claude/plugins/marketplaces/openai-codex/`, the plugin's skills are the **preferred** path for Claude→Codex delegation:

| Plugin skill | Use for |
|--------------|---------|
| `codex:setup` | Check Codex is installed, configured, and ready |
| `codex:rescue` | Delegate a rescue/fix/diagnosis/research task to Codex |
| `codex:codex-result-handling` | Internal — how to present Codex output back to the user |
| `codex:gpt-5-4-prompting` | Internal — prompt drafting for Codex |

The plugin wraps `codex` with a `task` runner that handles background execution, model/effort routing, write-vs-read, and result fetching. Hand-rolling `codex exec` from Bash is fine for **direct** CLI work (e.g. the user explicitly types `codex …` or wants a one-off review), but for "delegate this to Codex" requests, prefer `codex:rescue`. Don't double-invoke.

Detect with: `ls ~/.claude/plugins/marketplaces/openai-codex/ 2>/dev/null`

## Prerequisites

```bash
codex --version                       # Confirm install
codex doctor                          # Diagnose install + auth + config + connectivity
codex login                           # First-time auth (ChatGPT subscription OR API key)
codex update                          # In-place update (DON'T run automatically — surface to user)
```

**Auth modes** (`codex doctor` shows which is active):
- **ChatGPT subscription** (`stored_auth_mode: chatgpt`) — default; uses your ChatGPT plan quota
- **API key** (`stored_auth_mode: apikey`) — billed per token via OpenAI API
- **OSS** (`--oss --local-provider {ollama,lmstudio}`) — local model, no remote quota

## Preflight: check version + current default before invoking

Before the **first** `codex exec`/`codex review` in a session, run a quick preflight. Do NOT repeat for every call — once per session is enough.

```bash
codex doctor 2>&1 | grep -E "(version|model|auth|updates)" | head -20
```

What to look for:

| Doctor line | What to do |
|------|---------|
| `model  <name> · openai` (under Configuration) | This is the **current default** — use it as-is; don't override unless the user names a specific model |
| `↑ updates  X.Y.Z available (current A.B.C)` | Surface to the user: "Codex 0.133.0 is available, you're on 0.132.0 — run `codex update` when convenient." Do NOT auto-update (slow + can break in-flight sessions). |
| `auth  auth is configured` | Good. If `not configured`, tell user to `codex login` first. |
| `network  …  not reachable` | Network/proxy issue — surface to user, don't blind-retry. |

Skip the preflight (and just invoke) if the user explicitly asks for speed or for a one-off trivial query.

## Core execution pattern

```bash
codex exec "Your prompt here"                            # one-shot, default model + effort
echo "context..." | codex exec -                         # read prompt from stdin
codex exec resume --last "Now add tests"                 # resume most recent session
codex exec resume <SESSION_UUID> "Continue"              # resume specific session
```

When the user says "codex prompt", treat it as `codex exec "<user prompt>"`. Pick effort and sandbox based on task shape (see below).

## Model + reasoning effort — leave unset by default

**Don't hardcode a model or effort in invocations.** Codex tracks the current best default in `~/.codex/config.toml` and ships new defaults with each release. Hardcoding `-c 'model="..."'` or `-c 'model_reasoning_effort="..."'` makes calls go stale (this skill itself was pinned to a deprecated `gpt-5.4` for months). Match the official plugin's rule:

> *Leave model unset by default. Add `-m`/`-c model="…"` only when the user explicitly asks for a specific model. Leave reasoning effort unset unless the user explicitly requests a level.*

**To see what the current default actually is**: `codex doctor` reports it as `model  <name> · openai` under the Configuration section. Don't bake that value into the invocation — it's just for your awareness.

**Model names you may see in 2026** (snapshot, may shift): `gpt-5.5` (current default), `gpt-5.4`, `gpt-5.3-codex-spark` (the "spark" alias in the plugin), `o3`. Set via `-m <name>` (works on `exec`, **not** on `review`) or `-c 'model="<name>"'` (works everywhere).

**Reasoning effort levels** (six, set via `-c 'model_reasoning_effort="<level>"'` — but normally leave unset):

| Level | When to override the default to this |
|-------|---------------------------------------|
| `none` | Pure pass-through, no reasoning |
| `minimal` | Trivial transformations. May 400 on some models — fall back to `low` if it errors |
| `low` | Simple Q&A, short generations, format conversions. ~half the tokens of `medium` |
| `medium` | Code review of a file, second-opinion audit, one-shot refactor |
| `high` | Repeated/failing tasks needing deeper analysis, complex multi-step planning, explicit user request |
| `xhigh` | Last-resort heavy reasoning. Only when `high` has failed |

Escalate only when a default-effort run failed or produced surface-level output. Don't default to `high` "to be safe" — it burns 5–10× the tokens.

```bash
# Default invocation — let Codex pick model + effort
codex exec "Audit this for race conditions"

# User explicitly asks for a cheap quick lookup
codex exec -c 'model_reasoning_effort="low"' "What does ETIMEDOUT mean in posix?"

# User explicitly asks for deep analysis
codex exec -c 'model_reasoning_effort="high"' "Diagnose why this test flakes 1-in-20 runs"

# User explicitly asks for a specific model
codex exec -m gpt-5.4 "Compare against gpt-5.4's answer"
```

## Sandbox + approval policy

`-s, --sandbox` selects the filesystem policy:

| Mode | Behavior |
|------|----------|
| `read-only` | Agent can read but not write. **Use for audits, second opinions, diagnostics.** |
| `workspace-write` | Agent can write inside the workspace (and `--add-dir` paths). Use for refactors/implementations you expect to land. |
| `danger-full-access` | No filesystem restrictions. Only with explicit user OK + trusted prompt. |

`-a, --ask-for-approval` (**top-level flag, before subcommand**) selects when Codex asks before running shell commands: `untrusted`, `on-request` (default for interactive), `never` (default for non-interactive). `on-failure` is **deprecated**.

**The three "dangerous" flags — know the difference:**

| Flag | What it actually skips |
|------|------------------------|
| `--dangerously-bypass-approvals-and-sandbox` | Bypasses *both* approval prompts *and* sandbox. Intended only for externally-sandboxed environments (containers, VMs). |
| `--dangerously-bypass-hook-trust` | Runs configured hooks without requiring persisted trust. Use only in automation that already vets hook sources. |
| `--full-auto` | **Deprecated.** Codex itself now tells you: "use `--sandbox workspace-write` instead". |

## Critical argument compatibility rules

These prevent CLI errors. Confirmed against v0.132.

### `codex exec`

- `[PROMPT]` is the **only** positional arg. Passing both `-` (stdin) and a quoted prompt errors with `unexpected argument '-' found` — pick one.
- Correct stdin: `cat file.txt | codex exec -s read-only -`
- Correct prompt arg: `codex exec -s read-only "your prompt"`
- WRONG: `cat file.txt | codex exec -s read-only - "your prompt"` (two positional args)
- When the user names a specific model: `codex exec -m <name> "…"` (or `-c 'model="<name>"'`).

### `codex review`

- `-m` does **not** work on `codex review` — if the user names a model, use `-c 'model="<name>"'`. (If you literally need the string `-m` in a prompt, the error tip says `use '-- -m'`.)
- `--commit <SHA>` and `[PROMPT]` are **mutually exclusive** — cannot combine.
- `--base <BRANCH>` and `[PROMPT]` **can** be combined.
- `--uncommitted` and `[PROMPT]` **can** be combined.
- WRONG: `codex review --commit abc123 "Review for security"`
- Correct: `codex review --commit abc123`
- Correct: `codex review --base main "Focus on security"`

### Workaround for `--commit` with custom instructions

```bash
git diff <SHA>~1..<SHA> | codex exec -s read-only -
```

## Subcommands worth knowing

| Subcommand | Use for |
|-----------|---------|
| `codex exec [PROMPT]` | Headless one-shot |
| `codex exec resume [ID\|--last] [PROMPT]` | Continue a prior session non-interactively |
| `codex review {--uncommitted\|--base BRANCH\|--commit SHA}` | Review a diff in the repo |
| `codex resume [ID\|--last]` | Resume an interactive session (picker if no ID) |
| `codex fork [ID]` | Fork a prior session into a new branch |
| `codex archive <id>` / `unarchive` | Archive sessions (archived = protected from `resume`/`fork`) |
| `codex apply <TASK_ID>` | `git apply` the latest diff Codex produced for `<TASK_ID>` |
| `codex doctor` | Diagnose install, auth, config, connectivity, sandbox — first stop when anything's broken |
| `codex mcp {list,get,add,remove,login,logout}` | Manage MCP servers Codex calls into |
| `codex sandbox [CMD]` | Run an arbitrary command inside Codex's sandbox |
| `codex features {list,enable,disable}` | Toggle feature flags (`hooks`, `multi_agent`, `image_generation`, etc.) |
| `codex update` | Upgrade Codex to latest |
| `codex login` / `codex logout` | Auth management |

## Useful flags reference (most useful in headless / Claude-driven runs)

| Flag | Description |
|------|-------------|
| `-c 'key="value"'` | Override any config (works everywhere; preferred over `-m` for review) |
| `-m` | Model shorthand (works with `exec`, **not** with `review`) |
| `-s` | Sandbox: `read-only` / `workspace-write` / `danger-full-access` |
| `-a` | Approval policy (top-level, **before** subcommand): `untrusted` / `on-request` / `never` |
| `-C` | Working directory root |
| `--add-dir <DIR>` | Additional writable directories beyond workspace |
| `-o, --output-last-message <FILE>` | Write final assistant message to a file |
| `--json` | Stream events as JSONL on stdout — for piping into other tools |
| `--output-schema <FILE>` | Path to JSON Schema describing the final response shape (structured output) |
| `--ephemeral` | Don't persist a session file to disk (one-shot, no resume) |
| `--ignore-user-config` | Don't load `~/.codex/config.toml` — for reproducible CI behavior |
| `--ignore-rules` | Don't load `.rules` files |
| `--skip-git-repo-check` | Allow running outside a Git repo |
| `--search` | Enable native `web_search` tool (top-level flag) |
| `-i, --image <FILE>` | Attach images to the initial prompt (multimodal) |
| `--oss --local-provider {ollama,lmstudio}` | Use a local OSS model instead of OpenAI |
| `--no-alt-screen` | Inline TUI mode (preserves scrollback) |

## Top-level vs. subcommand flag placement

`--search` and `-a/--ask-for-approval` are **top-level** flags. Put them **before** `exec` or `review`.

Correct:

```bash
codex --search -a on-request exec "Your prompt"
codex -a never exec "Your prompt"
```

WRONG:

```bash
codex exec --search "Your prompt"
codex exec -a on-request "Your prompt"
```

## Efficient execution from Claude (don't idle-wait)

Long `codex exec` runs (especially with `high`/`xhigh` effort or autonomous refactors) can take minutes. **Always invoke with `run_in_background: true`** so the harness wakes Claude on actual exit — don't poll the output file in a sleep loop.

```text
# RIGHT — Claude is notified the moment codex exits, whether 30s or 30m
Bash(command="codex exec -s read-only -c 'model=\"gpt-5.5\"' \"audit...\" -o /tmp/codex.out",
     run_in_background=true)
# → wait for completion notification, then Read /tmp/codex.out

# WRONG — burns wall clock and prompt cache
Bash(command="codex exec ...")          # foreground blocks Claude
sleep 300 && cat /tmp/codex.out         # polling = idle waste
```

For very long runs also pass `--json` to a log file and tail-inspect progress without re-invoking:

```bash
codex exec --json -c 'model_reasoning_effort="high"' "..." 2> /tmp/codex.events.jsonl
```

## Rate limits and abuse heuristics

Codex shares quota across all your invocations on the same auth (whether ChatGPT subscription or API key). Bot-like patterns trigger throttling and, on repeated 429s, account-level slow-downs.

- **Never run two `codex exec` processes in parallel.** Serialize. If Claude has three things to ask, send three sequential prompts or combine into one.
- **Reuse sessions** with `codex exec resume --last` instead of cold-starting every time.
- **On 429 / `rate limit` / `quota exceeded` in output: stop and report, do not retry.** No `while ! codex …; do …; done` loops.
- **Don't loop on failure.** Fix the prompt before re-running; if `medium` failed, try `high` *once*, not five times.
- **Be explicit about output length** ("answer in ≤5 bullets", "code only, no commentary") — every turn costs tokens.
- **Pair `--ephemeral`** with one-off scripted calls so you don't accumulate junk sessions in `~/.codex/`.
- **Use `--oss`** when developing/debugging Codex CLI usage itself so you don't burn paid quota on plumbing tests.

## Comparison workflow with Claude

When the user wants a second opinion:

1. State Claude's answer/recommendation first.
2. Run the same question via `codex exec -s read-only "<same prompt>"`.
3. Present both side-by-side. Highlight where they agree/disagree.

Pick a higher sandbox (or use `codex review`) only if the user wants both agents to *implement*, not just opine.

## Recommended invocation patterns

All examples use Codex's default model + effort. Only add `-m`/`-c 'model_reasoning_effort=...'` if the user explicitly asks.

```bash
# Second-opinion audit (read-only)
codex exec -s read-only --ephemeral \
  "Audit src/auth/ for OWASP issues. Report only — do not modify files."

# Headless build / refactor (writes to workspace)
codex exec -s workspace-write -C "$(pwd)" --add-dir ./packages/api \
  -o /tmp/codex.out \
  "Implement the /healthz endpoint with a unit test."

# Review uncommitted changes
codex review --uncommitted "Focus on security and error-handling."

# Review against base branch
codex review --base main "Check for performance regressions."

# Review a specific commit (NO custom prompt allowed with --commit)
codex review --commit abc1234

# Pipe a specific diff for review with custom instructions
git diff HEAD~1..HEAD | codex exec -s read-only --ephemeral -

# Structured output (JSON Schema)
codex exec --output-schema /tmp/schema.json \
  "Extract all TODO comments as {file, line, text} objects."

# Resume the last session with follow-up
codex exec resume --last "Now add error handling to that route."

# User explicitly wants high reasoning effort
codex exec -c 'model_reasoning_effort="high"' "Diagnose why this race appears 1-in-50 runs"

# User explicitly names a model
codex exec -m gpt-5.4 "Compare gpt-5.4 vs current default on this prompt"

# Local OSS model (no remote quota)
codex exec --oss --local-provider ollama -m llama3.1 "Quick sanity check on this regex"
```

## Best practices (quick checklist)

- **Preflight once per session** with `codex doctor` — note the current default model, surface any available update to the user, never auto-update.
- **Leave model + effort unset by default.** Codex picks the current best default; hardcoding makes invocations go stale. Add `-m` / `-c 'model="…"'` / `-c 'model_reasoning_effort="…"'` only when the user explicitly asks.
- **Prefer `codex:rescue` plugin** for "delegate to Codex" requests when the plugin is installed. Use direct `codex exec` for explicit CLI tasks the user typed.
- **Default sandbox: `read-only`.** Escalate to `workspace-write` only when you expect file changes; `danger-full-access` requires explicit user OK.
- **Always `run_in_background: true`** and let the harness fire the completion notification — no polling.
- **For commit reviews with custom instructions**, pipe `git diff` to `codex exec -` (since `--commit` and `[PROMPT]` are mutually exclusive).
- Add `-o <file>` when another tool or agent must consume the result.
- Use `--ephemeral` for one-shot scripted calls so you don't accumulate junk sessions in `~/.codex/`.
- Use `--ignore-user-config` in CI for reproducibility independent of `~/.codex/config.toml`.
- Serialize `codex` calls — never two in parallel. On 429: stop, report, don't retry.
- Pair `--dangerously-bypass-approvals-and-sandbox` only with an externally-sandboxed environment (container, VM). Never on a bare developer machine.
- Run `codex doctor` first whenever anything misbehaves — it surfaces auth, config, sandbox, and connectivity issues in one pass.
- `--full-auto` is deprecated; use `--sandbox workspace-write` instead.
