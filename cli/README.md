# claude-skills-vault

Install [Claude Code](https://claude.ai/code) skills, commands, and MCP servers from the community vault.

**52 skills** | **7 commands** | **38 MCP servers**

## Quick Start

```bash
# List all available skills
npx claude-skills-vault list

# Install a specific skill
npx claude-skills-vault install brainstorm

# Install multiple skills
npx claude-skills-vault install brainstorm owasp-security github-cli

# Install all skills
npx claude-skills-vault install --all
```

## Commands

| Command | Description |
|---------|-------------|
| `list` | List all available skills, commands, and MCP servers |
| `install <name> [names...]` | Install skills/commands by name |
| `search <query>` | Search by keyword |
| `info <name>` | Show details about a skill (author, source, category) |

## Install Options

| Flag | Description |
|------|-------------|
| `--all` | Install all skills and commands |
| `--skills` | Install all skills only |
| `--commands` | Install all commands only |
| `--force` | Overwrite existing files |
| `--dry-run` | Show what would be installed |

## How It Works

Skills are downloaded directly from the [claude-skills-vault](https://github.com/georgekhananaev/claude-skills-vault) GitHub repository and placed into your project's `.claude/skills/` directory. No git clone required.

## Requirements

- Node.js >= 18
- A project directory where you want to install skills

## License

MIT — See [GitHub](https://github.com/georgekhananaev/claude-skills-vault) for full details.
