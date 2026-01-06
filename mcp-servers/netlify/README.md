# Netlify MCP Server

Site deployment and management for Netlify platform.

## Source

- **Official URL**: [netlify-mcp.netlify.app](https://netlify-mcp.netlify.app)
- **Documentation**: [Netlify Docs](https://docs.netlify.com/)
- **Maintainer**: Netlify

## Quick Install

```bash
claude mcp add netlify --transport http https://netlify-mcp.netlify.app/mcp
```

## Features

- **Site Deployment**: Deploy builds to Netlify
- **Site Management**: Manage site settings and configuration
- **Build Triggers**: Trigger new builds
- **Environment Variables**: Manage env vars

## Configuration

```json
{
  "mcpServers": {
    "netlify": {
      "type": "http",
      "url": "https://netlify-mcp.netlify.app/mcp"
    }
  }
}
```

## Usage Examples

```
User: Deploy my site to Netlify
Claude: [Uses Netlify MCP to deploy]

User: Show my Netlify sites
Claude: [Uses Netlify MCP to list sites]

User: Trigger a rebuild for my-site
Claude: [Uses Netlify MCP to trigger build]

User: Update environment variables
Claude: [Uses Netlify MCP to update env vars]
```

## Authentication

Authenticates via Netlify's OAuth flow on first use.

## License

Proprietary - Netlify
