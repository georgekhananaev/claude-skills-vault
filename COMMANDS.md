# Commands

Slash commands available in Claude Code. Install all commands with:

```bash
npx claude-skills-vault install --commands
```

## Available Commands

| Command | Description | Invocation |
|---------|-------------|------------|
| **git-commit** | Safe git commit with conventional commits, changelog update | `/git-commit` |
| **git-push** | Git push with uncommitted changes check and changelog versioning | `/git-push` |
| **git-npm-release** | Version bump, manifest regen, tag, push → auto npm publish | `/git-npm-release` |
| **git-review-pr** | Review PR for skills/commands/MCP — validates docs, quality, formatting | `/git-review-pr` |
| **create-pr** | Prepare GitHub pull request with essential details | `/create-pr` |
| **create-skill** | Create new skills from templates with validation and testing | `/create-skill` |
| **plan-feature** | Production-grade feature planning with dual-AI validation | `/plan-feature` |

## Usage

Commands are loaded automatically from `.claude/commands/`. Invoke them in Claude Code by typing the slash command.

```
/git-commit          # Commit with conventional format
/git-push            # Push to remote
/git-npm-release     # Version + tag + npm publish
/plan-feature        # Plan a new feature
```
