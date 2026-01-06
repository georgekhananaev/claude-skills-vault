# Codex MCP Server

Integration with OpenAI's advanced Codex models for enhanced coding capabilities.

## Quick Install

```bash
claude mcp add codex -s user -- codex -m gpt-5.1-codex-max -c model_reasoning_effort="high" mcp-server
```

## Prerequisites

- Codex CLI installed (`npm i -g codex-cli` or similar)
- OpenAI API key configured

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-m` | Model to use | gpt-5.1-codex-max |
| `-c model_reasoning_effort` | Reasoning depth | high |

## Claude Code Config

```json
{
  "mcpServers": {
    "codex": {
      "command": "codex",
      "args": [
        "-m", "gpt-5.1-codex-max",
        "-c", "model_reasoning_effort=high",
        "mcp-server"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

## Tools Available

| Tool | Description |
|------|-------------|
| `codex` | Run Codex session |
| `codex-reply` | Continue conversation |

## Usage

```
User: Use Codex to help refactor this complex function
Claude: [Invokes Codex for advanced reasoning]
```

## Notes

- Requires separate OpenAI API billing
- Best for complex reasoning tasks
- Higher latency than local processing

## Links

- [OpenAI API](https://platform.openai.com/)
