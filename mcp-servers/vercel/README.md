# Vercel MCP Server

Deployment platform integration for managing Vercel projects and deployments.

## Source

- **Official URL**: [mcp.vercel.com](https://mcp.vercel.com)
- **Documentation**: [Vercel Docs](https://vercel.com/docs)
- **Maintainer**: Vercel

## Quick Install

```bash
claude mcp add vercel --transport http https://mcp.vercel.com/
```

## Features

- **Deployment Management**: Review deployment logs and status
- **Project Management**: Manage Vercel projects
- **Environment Variables**: Configure env vars
- **Domain Management**: Manage custom domains

## Configuration

```json
{
  "mcpServers": {
    "vercel": {
      "type": "http",
      "url": "https://mcp.vercel.com/"
    }
  }
}
```

## Usage Examples

```
User: Show my Vercel deployments
Claude: [Uses Vercel MCP to list deployments]

User: What's the status of the latest deployment?
Claude: [Uses Vercel MCP to check status]

User: Show deployment logs for my-app
Claude: [Uses Vercel MCP to fetch logs]

User: List my Vercel projects
Claude: [Uses Vercel MCP to list projects]
```

## Authentication

Authenticates via Vercel's OAuth flow on first use.

## License

Proprietary - Vercel
