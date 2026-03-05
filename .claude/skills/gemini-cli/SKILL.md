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

# YOLO mode (auto-approve tool use)
gemini -y -p "prompt"

# File analysis
cat file.txt | gemini -p "Analyze this"
```

## Models (Gemini 3+ only)

| Model | Use case |
|-------|----------|
| `gemini-3-pro` | Default, best all-round |
| `gemini-3-flash` | Fast, lightweight tasks |

Omit `-m` to use the CLI default (latest stable).

## CLI Options

| Flag | Desc |
|------|------|
| `-p` | **Required for headless.** Non-interactive prompt |
| `-m` | Model selection |
| `-o` | Output: text/json/stream-json |
| `-y` | Auto-approve all actions (YOLO) |
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
