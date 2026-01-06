# GitHub MCP Server

Official GitHub MCP server for AI-powered repository management, issues, PRs, and workflows.

## Source

- **GitHub**: [github/github-mcp-server](https://github.com/github/github-mcp-server)
- **Docker**: `ghcr.io/github/github-mcp-server`
- **Remote API**: `https://api.githubcopilot.com/mcp/`
- **Maintainer**: GitHub

## Quick Install

```bash
# Remote (OAuth - recommended)
claude mcp add github --transport http https://api.githubcopilot.com/mcp/

# Local with Docker
claude mcp add github -s user -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server
```

## Features

- **Repository Management**: Code browsing, file operations, commit analysis
- **Issue & PR Automation**: Create, update, merge PRs and issues
- **CI/CD Intelligence**: GitHub Actions monitoring, build analysis
- **Code Analysis**: Security scanning, Dependabot alerts
- **Team Collaboration**: Discussions, notifications, team activity

## Configuration

### Remote Server (OAuth)

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

### Local with Docker

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    }
  }
}
```

### GitHub Enterprise

```json
{
  "mcpServers": {
    "github-enterprise": {
      "type": "http",
      "url": "https://copilot-api.your-company.ghe.com/mcp"
    }
  }
}
```

## Toolsets

Enable specific toolsets with `GITHUB_TOOLSETS` environment variable:

| Toolset | Description |
|---------|-------------|
| `repos` | Repository operations |
| `issues` | Issue management |
| `pull_requests` | PR operations |
| `actions` | GitHub Actions workflows |
| `code_security` | Code scanning alerts |
| `dependabot` | Dependabot alerts |
| `secret_protection` | Secret scanning |
| `discussions` | Repository discussions |
| `projects` | GitHub Projects |
| `users` | User operations |
| `orgs` | Organization management |
| `notifications` | Notification handling |

Example: `GITHUB_TOOLSETS="repos,issues,pull_requests"`

## Tools (100+)

### Repository Operations

| Tool | Description |
|------|-------------|
| `get_file_contents` | Get file contents |
| `create_or_update_file` | Create or update file |
| `push_files` | Push multiple files |
| `search_repositories` | Search repositories |
| `create_repository` | Create repository |
| `fork_repository` | Fork repository |
| `create_branch` | Create branch |
| `list_commits` | List commits |
| `search_code` | Search code |

### Issues

| Tool | Description |
|------|-------------|
| `create_issue` | Create issue |
| `get_issue` | Get issue details |
| `update_issue` | Update issue |
| `list_issues` | List issues |
| `search_issues` | Search issues |
| `add_issue_comment` | Add comment |

### Pull Requests

| Tool | Description |
|------|-------------|
| `create_pull_request` | Create PR |
| `get_pull_request` | Get PR details |
| `list_pull_requests` | List PRs |
| `merge_pull_request` | Merge PR |
| `create_pull_request_review` | Create review |
| `get_pull_request_files` | Get changed files |
| `get_pull_request_diff` | Get PR diff |

### GitHub Actions

| Tool | Description |
|------|-------------|
| `list_workflows` | List workflows |
| `get_workflow_run` | Get run details |
| `trigger_workflow` | Trigger workflow |
| `download_artifact` | Download artifacts |

### Security

| Tool | Description |
|------|-------------|
| `list_code_scanning_alerts` | Code scanning alerts |
| `list_dependabot_alerts` | Dependabot alerts |
| `list_secret_scanning_alerts` | Secret scanning alerts |

## Special Modes

```bash
# Read-only mode
./github-mcp-server --read-only

# Lockdown mode (filter by push access)
./github-mcp-server --lockdown-mode

# Dynamic tool discovery (beta)
./github-mcp-server --dynamic-toolsets
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | PAT for authentication |
| `GITHUB_TOOLSETS` | Comma-separated toolsets to enable |
| `GITHUB_HOST` | GitHub Enterprise hostname |

## Getting Token

1. Go to [GitHub Tokens](https://github.com/settings/tokens)
2. Generate new token (fine-grained recommended)
3. Required scopes: `repo`, `read:org`, `read:user`

## Usage Examples

```
User: Show my open PRs
Claude: [Uses list_pull_requests tool]

User: Create an issue for the login bug
Claude: [Uses create_issue tool]

User: What's failing in the CI?
Claude: [Uses list_workflows and get_workflow_run tools]

User: Show Dependabot alerts for my repo
Claude: [Uses list_dependabot_alerts tool]

User: Merge PR #42
Claude: [Uses merge_pull_request tool]
```

## Legacy Server

The archived `@modelcontextprotocol/server-github` is superseded by this official GitHub server.

## License

MIT - [GitHub](https://github.com/github/github-mcp-server)
