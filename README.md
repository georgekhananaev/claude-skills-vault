# Claude Skills Vault

![Preview](preview.jpg)

A curated collection of skills, commands, and MCP servers for Claude Code.

## Quick Install

```bash
# Install the CLI globally or use npx
npx claude-skills-vault list                # Browse all available skills
npx claude-skills-vault install brainstorm  # Install a specific skill
npx claude-skills-vault search react        # Search by keyword
npx claude-skills-vault info owasp-security # View skill details
```

```bash
# Install multiple skills at once
npx claude-skills-vault install brainstorm owasp-security github-cli

# Install all skills and commands
npx claude-skills-vault install --all

# Install only skills or only commands
npx claude-skills-vault install --skills
npx claude-skills-vault install --commands

# Preview without installing
npx claude-skills-vault install brainstorm --dry-run

# Overwrite existing skills
npx claude-skills-vault install brainstorm --force
```

Skills are downloaded directly from this repository into your project's `.claude/skills/` directory. No git clone required.

## What's Inside

| Category | Count | Browse the full list |
|----------|-------|----------------------|
| 🛠 **Skills** | 59 | [**SKILLS.md**](SKILLS.md) — dev, security, testing, frontend, backend, mobile, AI, databases, automation, SEO |
| ⌨️ **Commands** | 12 | [**COMMANDS.md**](COMMANDS.md) — git workflow, PR & release, feature planning, DevOps |
| 🔌 **MCP Servers** | 34 configs + 100+ catalog | [**MCP-SERVERS.md**](MCP-SERVERS.md) — databases, cloud, observability, payments, AI & more |

## 📚 Documentation

Jump straight to what you need — no searching required.

### 🛠 Skills → [SKILLS.md](SKILLS.md)

59 installable skills, each with a description and a copy-paste install command.

```bash
npx claude-skills-vault list                 # browse all
npx claude-skills-vault search <keyword>     # find by topic
npx claude-skills-vault install <name>       # install one
```

### ⌨️ Commands → [COMMANDS.md](COMMANDS.md)

12 slash commands — each row lists its `/invocation` and a per-command install command.

### 🔌 MCP Servers → [MCP-SERVERS.md](MCP-SERVERS.md)

How to connect Claude to external tools, plus a source-linked catalog of 100+ servers (official vendors + maintained GitHub projects), each with an exact install command.

**Setup:** [Three ways to add a server](MCP-SERVERS.md#three-ways-to-add-a-server) · [Official plugin marketplace](MCP-SERVERS.md#1-official-plugin-marketplace-recommended) · [Reference servers](MCP-SERVERS.md#4-reference-servers--modelcontextprotocolservers) · [Build your own (SDKs)](MCP-SERVERS.md#6-official-sdks-build-your-own-server) · [Command cheatsheet](MCP-SERVERS.md#command-cheatsheet)

**Browse servers by category:**
[Databases & data](MCP-SERVERS.md#databases--data) ·
[Search & vector](MCP-SERVERS.md#search--vector) ·
[Cloud & deployment](MCP-SERVERS.md#cloud--deployment) ·
[DevOps, CI/CD & IaC](MCP-SERVERS.md#devops-cicd--iac) ·
[Observability & monitoring](MCP-SERVERS.md#observability--monitoring) ·
[Payments & fintech](MCP-SERVERS.md#payments--fintech) ·
[CRM, support & sales](MCP-SERVERS.md#crm-support--sales) ·
[E-commerce & CMS](MCP-SERVERS.md#e-commerce--cms) ·
[Productivity, docs & storage](MCP-SERVERS.md#productivity-docs--storage) ·
[Communication & automation](MCP-SERVERS.md#communication--automation) ·
[Web search & scraping](MCP-SERVERS.md#web-search--scraping) ·
[AI, browser & dev tools](MCP-SERVERS.md#ai-browser--developer-tools)

## Manual Installation

```bash
git clone https://github.com/georgekhananaev/claude-skills-vault.git
cp -r claude-skills-vault/.claude your-project/
```

## Tutorials

- [Commands Tutorial](tutorials/COMMANDS_TUTORIAL.md) - Creating slash commands
- [Skills Tutorial](tutorials/SKILLS_TUTORIAL.md) - Creating and using skills
- [MCP Servers Tutorial](tutorials/MCP_SERVERS_TUTORIAL.md) - Building MCP servers

## Contributing

Contributions are welcome! Feel free to submit pull requests with new skills, commands, or MCP servers.

## Credits

Created by **George Khananaev**

Skills sourced from [ComposioHQ](https://github.com/ComposioHQ): document-skills (xlsx, docx, pptx, pdf), project-change-log, skill-creator, mcp-builder

Skills contributed by [garesuta](https://github.com/garesuta) ([PR #4](https://github.com/georgekhananaev/claude-skills-vault/pull/4), [PR #5](https://github.com/georgekhananaev/claude-skills-vault/pull/5)): react-best-practices, next-cache-components, next-upgrade, senior-backend, multi-agent-patterns, parallel-agents, vercel-react-native-skills

Skills contributed by [palakorn-moonholidays](https://github.com/palakorn-moonholidays) ([PR #6](https://github.com/georgekhananaev/claude-skills-vault/pull/6)): owasp-security, color-accessibility-audit

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## License

[MIT License](LICENSE) - See [NOTICE](NOTICE) for attribution guidelines.
