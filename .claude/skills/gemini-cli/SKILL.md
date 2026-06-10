---
name: gemini-cli
description: Run Gemini CLI for AI queries. Use when user asks to "run/ask/use gemini", compare Claude vs Gemini, or delegate tasks to Gemini.
---

# Gemini CLI

Interact w/ Google's Gemini CLI locally. Run queries, get responses, compare outputs.

## Prerequisites

Gemini CLI must be installed & configured:

1. **Install:** https://github.com/google-gemini/gemini-cli
2. **Auth:** Run `gemini` & sign in w/ Google account
3. **Verify:** `gemini --version`

## When to Use

- User asks to "run/ask/use gemini"
- Compare Claude vs Gemini responses
- Get second AI opinion
- Delegate task to Gemini

## Usage

**IMPORTANT:** Use `-p` flag for non-interactive (headless) one-shot queries. Without `-p`, gemini opens interactive mode which hangs in automation.

```bash
# One-shot query (MUST use -p for non-interactive)
gemini -p "Your prompt"

# Specific model
gemini -p "prompt" -m gemini-3-pro

# JSON output
gemini -p "prompt" -o json

# Auto-approve tool use (-y is deprecated)
gemini --approval-mode=yolo -p "prompt"

# File analysis
cat file.txt | gemini -p "Analyze this"
```

## Models

| Alias | Use case |
|-------|----------|
| `auto` | DEFAULT — routes per prompt (simple → Flash, complex → 3 Pro) |
| `pro` | Force Gemini 3 Pro (best all-round) |
| `flash` / `flash-lite` | Fast, lightweight tasks (3.5 Flash GA rolling out as auto default) |

Omit `-m` to use `auto` routing. Aliases beat pinned model ids — they track
upstream model swaps. Pin a full id (e.g. `gemini-3-pro`) only when the user
names one.

## CLI Options

| Flag | Desc |
|------|------|
| `-p` | **Required for headless.** Non-interactive prompt |
| `-m` | Model selection |
| `-o` | Output: text/json/stream-json |
| `--approval-mode=yolo` | Auto-approve all actions (`-y` is deprecated) |
| `-d` | Debug mode |
| `-s` | Sandbox mode |
| `-r` | Resume session |
| `-i` | Execute prompt then continue interactive |

## Comparison Workflow

1. Provide Claude's response first
2. Run same query via `gemini -p "prompt"`
3. Present both for comparison

## Best Practices

- Always use `-p` for automation/one-shot queries
- Quote prompts w/ double quotes
- Use `-o json` for parsing
- Pipe files for context
