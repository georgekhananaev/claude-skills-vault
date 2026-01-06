# Linear MCP Server

Issue tracking and project management integration with Linear.

## Source

- **Official URL**: [mcp.linear.app](https://mcp.linear.app)
- **Documentation**: [Linear MCP Docs](https://linear.app/docs/mcp)
- **Maintainer**: Linear

## Quick Install

```bash
claude mcp add linear --transport sse https://mcp.linear.app/sse
```

## Features

- **Issue Management**: Create, update, close issues
- **Project Tracking**: View projects and milestones
- **Sprint Management**: Access cycles and sprints
- **Team Workspaces**: Navigate team structures

## Configuration

No environment variables required - authenticates via Linear's OAuth flow on first use.

## Claude Code Config

```json
{
  "mcpServers": {
    "linear": {
      "type": "sse",
      "url": "https://mcp.linear.app/sse"
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `list_issues` | List issues with filters |
| `create_issue` | Create new issue |
| `update_issue` | Update issue details |
| `get_issue` | Get issue by ID |
| `search` | Search across workspace |
| `list_projects` | List projects |
| `list_teams` | List teams |

## Usage

```
User: Show my open issues in Linear
Claude: [Uses list_issues tool with filter]

User: Create a bug ticket for the API timeout
Claude: [Uses create_issue tool]

User: Move LIN-123 to In Progress
Claude: [Uses update_issue tool]

User: What's in the current sprint?
Claude: [Uses list_issues with cycle filter]
```

## Authentication

Uses OAuth to connect to your Linear account. On first use, you'll be prompted to authorize access.

## Notes

- Real-time sync with Linear
- Supports all Linear issue types
- Works with team workspaces

## License

Proprietary - Linear
