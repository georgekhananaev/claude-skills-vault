# claude-skills-vault

Install [Claude Code](https://claude.ai/code) skills, commands, and MCP servers from the community vault.

**63 skills** | **12 commands** | **34 MCP servers**

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

## Troubleshooting

**`list`/`search` missing recent items, or `install <name>` says "not found"?**

The CLI fetches the catalog matching its *own installed version*, not always the newest one. If npx is reusing a cached, older copy of this package, it'll see an older, smaller catalog.

- Always run with `@latest`: `npx claude-skills-vault@latest list` — bypasses npx's cache.
- Check the version you're actually running: `npx claude-skills-vault@latest --version`.
- Global install stale? `npm install -g claude-skills-vault@latest`.
- npx still stuck? Clear its cache: `npx clear-npx-cache` (or `rm -rf ~/.npm/_npx`).

See the [main repo README](https://github.com/georgekhananaev/claude-skills-vault#troubleshooting) for full details.

## Requirements

- Node.js >= 18
- A project directory where you want to install skills

## License

MIT — See [GitHub](https://github.com/georgekhananaev/claude-skills-vault) for full details.
