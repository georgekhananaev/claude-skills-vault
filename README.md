# Claude Skills Vault

![Preview](preview.jpg)

A curated collection of skills, commands, and MCP servers for Claude Code.

## Skills

### Core Skills

| Skill | Description |
|-------|-------------|
| **code-reviewer** | Code review checklist and best practices |
| **system-architect** | System architecture patterns and design guidance |
| **pydantic-model** | Pydantic v2 model patterns for validation and MongoDB |
| **skill-creator** | Guide for creating Claude Code skills |
| **token-formatter** | Token compression and formatting utilities |
| **mcp-builder** | Guide for creating high-quality MCP servers (Python/Node) |
| **project-change-log** | Automatic CHANGELOG.md maintenance |

### Document Skills

| Skill | Description |
|-------|-------------|
| **docx** | Word document handling with OOXML schemas |
| **pdf** | PDF form filling, extraction, and validation |
| **pptx** | PowerPoint manipulation and HTML-to-PPTX |
| **xlsx** | Excel spreadsheet handling and formula recalculation |
| **md** | Markdown validation and processing |

## Commands

| Command | Description |
|---------|-------------|
| `/commit` | Safe git commit with conventional commits format |

## MCP Servers

| Server | Description |
|--------|-------------|
| **postgres-mcp** | PostgreSQL queries and schema exploration |
| **jira-bridge** | Jira issues, JQL search, and sprint management |

## Tutorials

- [Commands Tutorial](tutorials/COMMANDS_TUTORIAL.md) - Creating slash commands
- [Skills Tutorial](tutorials/SKILLS_TUTORIAL.md) - Creating and using skills
- [MCP Servers Tutorial](tutorials/MCP_SERVERS_TUTORIAL.md) - Building MCP servers

## Installation

```bash
git clone https://github.com/georgekhananaev/claude-skills-vault.git

# Copy skills to your project
cp -r claude-skills-vault/.claude your-project/
```

## Credits

Created by **George Khananaev**

Skills sourced from [ComposioHQ](https://github.com/ComposioHQ): document-skills (xlsx, docx, xlsx, pdf), project-change-log, skill-creator, mcp-builder

## License

[MIT License](LICENSE) - See [NOTICE](NOTICE) for attribution guidelines.
