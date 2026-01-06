# Cloudflare MCP Server

Managed remote MCP servers for Cloudflare services.

## Source

- **Documentation**: [Cloudflare Agents - MCP Servers](https://developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/)
- **Blog**: [Hi Claude, build an MCP server on Cloudflare Workers](https://blog.cloudflare.com/model-context-protocol/)
- **Maintainer**: Cloudflare

## Quick Install

```bash
# Workers AI bindings
claude mcp add cloudflare-ai --transport http https://ai.mcp.cloudflare.com/mcp

# KV namespace bindings
claude mcp add cloudflare-kv --transport http https://kv.mcp.cloudflare.com/mcp

# R2 bucket bindings
claude mcp add cloudflare-r2 --transport http https://r2.mcp.cloudflare.com/mcp

# D1 database bindings
claude mcp add cloudflare-d1 --transport http https://d1.mcp.cloudflare.com/mcp
```

## Features

- **Managed Servers**: Cloudflare runs and maintains these MCP servers
- **OAuth Authentication**: Connect using OAuth on clients
- **Multiple Services**: AI, KV, R2, D1, and more

## Available Servers

| Server | URL | Description |
|--------|-----|-------------|
| Workers AI | `https://ai.mcp.cloudflare.com/mcp` | AI model inference |
| KV | `https://kv.mcp.cloudflare.com/mcp` | Key-value storage |
| R2 | `https://r2.mcp.cloudflare.com/mcp` | Object storage |
| D1 | `https://d1.mcp.cloudflare.com/mcp` | SQL database |
| Workers | `https://workers.mcp.cloudflare.com/mcp` | Worker management |
| Analytics | `https://analytics.mcp.cloudflare.com/mcp` | Analytics data |

## Claude Code Config

```json
{
  "mcpServers": {
    "cloudflare-ai": {
      "type": "http",
      "url": "https://ai.mcp.cloudflare.com/mcp"
    },
    "cloudflare-d1": {
      "type": "http",
      "url": "https://d1.mcp.cloudflare.com/mcp"
    }
  }
}
```

## Capabilities

- Read configurations from your account
- Process information and make suggestions
- Execute changes (with authorization)
- Supports streamable-http and SSE transports

## Authentication

Uses OAuth to connect to your Cloudflare account. On first use, you'll be prompted to authorize access.

## Usage

```
User: List my Cloudflare Workers
Claude: [Uses Workers MCP to list workers]

User: Query my D1 database
Claude: [Uses D1 MCP to execute query]

User: Store this in KV
Claude: [Uses KV MCP to write data]
```

## Notes

- Requires Cloudflare account
- OAuth authorization required on first use
- SSE transport (`/sse`) is deprecated, use HTTP (`/mcp`)

## License

Proprietary - Cloudflare
