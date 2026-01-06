# Sentry MCP Server

Error tracking and performance monitoring integration.

## Source

- **Official URL**: [mcp.sentry.dev](https://mcp.sentry.dev)
- **Documentation**: [Sentry Docs](https://docs.sentry.io/)
- **Maintainer**: Sentry

## Quick Install

```bash
claude mcp add sentry --transport sse https://mcp.sentry.dev/mcp
```

## Features

- **Error Tracking**: Analyze stack traces and error patterns
- **Performance Monitoring**: Track application performance
- **Issue Management**: Manage and resolve issues
- **Release Tracking**: Monitor release health

## Configuration

```json
{
  "mcpServers": {
    "sentry": {
      "type": "sse",
      "url": "https://mcp.sentry.dev/mcp"
    }
  }
}
```

## Usage Examples

```
User: Show recent errors in my project
Claude: [Uses Sentry MCP to list errors]

User: What's causing the most issues this week?
Claude: [Uses Sentry MCP to analyze error patterns]

User: Show the stack trace for issue PROJ-123
Claude: [Uses Sentry MCP to fetch issue details]

User: How is the latest release performing?
Claude: [Uses Sentry MCP to check release health]
```

## Authentication

Authenticates via Sentry's OAuth flow on first use.

## License

Proprietary - Sentry
