---
name: codex-cli
description: Run OpenAI Codex CLI for coding tasks and second-opinion audits. Use when a user asks to run/ask/use Codex, says "codex prompt", or wants Claude to delegate a logic/code review to OpenAI models.
---

# Codex CLI

Run OpenAI Codex CLI locally for second-opinion audits, code review, and non-interactive task execution.

## Prerequisites

Codex CLI must be installed and authenticated:

1. **Install:** `npm install -g @openai/codex`
2. **Auth:** `codex login`
3. **Verify:** `codex --version`

## Core Execution Pattern

Use `codex exec` for delegated prompts (non-interactive):

```bash
codex exec "Your prompt here"
```

When the user says "codex prompt", treat it as:

```bash
codex exec "<user prompt>"
```

## Model Guidance

Prefer `gpt-5.4` unless the user asks for a different model.

Default reasoning effort is **medium**. Only escalate when explicitly needed:
- Use `medium` for most coding, reviews, refactors, second-opinion audits, and one-off tasks
- Use `high` only for: repeated/failing tasks that need deeper analysis, complex multi-step planning, or when the user explicitly asks for deeper reasoning

```bash
codex exec -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"' "Your prompt"
```

Fallback note:
- If `gpt-5.4` is unavailable, fall back to the newest available GPT-5 or Codex model
- Keep reasoning effort explicit for reproducible behavior

## Critical: Argument Compatibility Rules

These rules prevent CLI errors. Follow them exactly.

### `codex exec`

- `-m` flag works: `codex exec -m gpt-5.4 "prompt"`
- `-c` config overrides work: `codex exec -c 'model="gpt-5.4"' "prompt"`
- Stdin with `-` replaces the prompt — do NOT pass both `-` and a quoted prompt string
- Correct stdin: `cat file.txt | codex exec -s read-only -c 'model="gpt-5.4"' -`
- WRONG: `cat file.txt | codex exec -s read-only - "Some extra prompt"` (two positional args)

### `codex review`

- `-m` flag does NOT work with `codex review` — use `-c 'model="gpt-5.4"'` instead
- `--commit <SHA>` and `[PROMPT]` are MUTUALLY EXCLUSIVE — cannot combine them
- `--base <BRANCH>` and `[PROMPT]` CAN be combined
- `--uncommitted` and `[PROMPT]` CAN be combined
- WRONG: `codex review --commit abc123 "Review for security"` (will error)
- Correct: `codex review --commit abc123 -c 'model="gpt-5.4"'`
- Correct: `codex review --base main "Focus on security"`

### Workaround for reviewing commits with custom instructions

Since `--commit` cannot take a prompt, pipe the diff to `codex exec` instead:

```bash
git diff <SHA>~1..<SHA> > /tmp/diff.txt && cat /tmp/diff.txt | codex exec -s read-only -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"' -
```

This is the recommended pattern for reviewing specific commits with custom review instructions.

## Commands

### Non-Interactive Execution

```bash
# Basic task (default model + medium effort)
codex exec -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"' "Audit this logic for edge cases"

# Full-auto mode (sandboxed, lower friction)
codex exec --full-auto -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"' "Implement the requested refactor"

# Read-only sandbox (analysis only)
codex exec -s read-only -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"' "Find bugs in this code path"

# Workspace-write sandbox
codex exec -s workspace-write -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"' "Apply the fix and update tests"

# Custom working directory
codex exec -C /path/to/project -c 'model="gpt-5.4"' "Evaluate this repository"

# Save final output to file
codex exec -o output.txt -c 'model="gpt-5.4"' "Summarize key risks"

# Pipe context from stdin (no additional prompt argument!)
cat context.txt | codex exec -s read-only -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"' -

# Pipe diff for commit review with custom instructions
git diff HEAD~1..HEAD > /tmp/diff.txt && cat /tmp/diff.txt | codex exec -s read-only -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"' -
```

### Code Review

Use `codex review` for repository diffs. Model must be set via `-c`, not `-m`.

```bash
# Review uncommitted changes
codex review --uncommitted -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"'

# Review against a base branch
codex review --base main -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"'

# Review a specific commit (NO prompt allowed with --commit)
codex review --commit abc123 -c 'model="gpt-5.4"' -c 'model_reasoning_effort="medium"'

# Custom review instructions (only with --base or --uncommitted, NOT --commit)
codex review --uncommitted -c 'model="gpt-5.4"' "Focus on security issues"
codex review --base main -c 'model="gpt-5.4"' "Check for performance regressions"
```

## Important Flag Placement

`--search` and `-a/--ask-for-approval` are top-level flags. Put them before `exec` or `review`.

Correct:

```bash
codex --search -a on-request exec "Your prompt"
codex --search -a on-request review --uncommitted
```

WRONG:

```bash
codex exec --search "Your prompt"
codex exec -a on-request "Your prompt"
```

## Useful Flags

| Flag | Description |
|------|-------------|
| `-c 'model="gpt-5.4"'` | Set model (works everywhere, preferred over `-m`) |
| `-m` | Model shorthand (works with `exec` only, NOT `review`) |
| `-s` | Sandbox: `read-only`, `workspace-write`, `danger-full-access` |
| `-a` | Approval policy (top-level flag, before subcommand) |
| `-C` | Working directory |
| `-o` | Write last message to file |
| `--full-auto` | Sandboxed auto-execution (`-a on-request -s workspace-write`) |
| `--json` | JSONL event output |
| `--search` | Enable web search tool (top-level flag) |
| `--add-dir` | Additional writable directories |
| `-c key=value` | Override any config value |

## Best Practices

- Default to `medium` reasoning effort — it covers most use cases well
- Only escalate to `high` for repeated failures, complex planning, or explicit user request
- Prefer `codex exec` for delegated prompts instead of interactive `codex`
- Start with `-s read-only` for audits and second opinions
- Use `--full-auto` only when you expect autonomous edits
- Always use `-c 'model="gpt-5.4"'` (not `-m`) for `codex review` commands
- For commit reviews with custom instructions, pipe `git diff` to `codex exec -`
- Keep prompts explicit about expected output format
- Add `-o` when another tool or agent must consume the result
- Run `codex review --uncommitted` before committing as a quick extra pass
- Run background tasks with `run_in_background` and check output via file path