# Atlassian MCP Server

Jira and Confluence integration for project management and documentation.

## Source

- **Official URL**: [mcp.atlassian.com](https://mcp.atlassian.com)
- **Documentation**: [Atlassian Developer](https://developer.atlassian.com/)
- **Maintainer**: Atlassian

## Quick Install

```bash
claude mcp add atlassian --transport sse https://mcp.atlassian.com/v1/sse
```

## Features

- **Jira Integration**: Manage issues, sprints, and projects
- **Confluence Integration**: Access and edit documentation
- **Search**: Search across Jira and Confluence
- **Automation**: Trigger workflows and transitions

## Configuration

```json
{
  "mcpServers": {
    "atlassian": {
      "type": "sse",
      "url": "https://mcp.atlassian.com/v1/sse"
    }
  }
}
```

## Usage Examples

```
User: Show my Jira tickets
Claude: [Uses Atlassian MCP to list issues]

User: Create a bug ticket for the login issue
Claude: [Uses Atlassian MCP to create issue]

User: Move PROJ-123 to In Progress
Claude: [Uses Atlassian MCP to transition issue]

User: Search Confluence for API documentation
Claude: [Uses Atlassian MCP to search docs]

User: What's in the current sprint?
Claude: [Uses Atlassian MCP to list sprint items]
```

## Authentication

Authenticates via Atlassian's OAuth flow on first use.

## Notes

- Supports both Jira Cloud and Confluence Cloud
- Requires appropriate Atlassian account permissions

## License

Proprietary - Atlassian
