# Canva MCP Server

Design platform integration for Canva.

## Source

- **Official URL**: [mcp.canva.com](https://mcp.canva.com)
- **Documentation**: [Canva Developers](https://www.canva.dev/)
- **Maintainer**: Canva

## Quick Install

```bash
claude mcp add canva --transport http https://mcp.canva.com/mcp
```

## Features

- **Design Access**: Access Canva designs
- **Asset Management**: Manage design assets
- **Template Operations**: Work with templates
- **Export Options**: Export designs in various formats

## Configuration

```json
{
  "mcpServers": {
    "canva": {
      "type": "http",
      "url": "https://mcp.canva.com/mcp"
    }
  }
}
```

## Usage Examples

```
User: Show my Canva designs
Claude: [Uses Canva MCP to list designs]

User: Export the banner design as PNG
Claude: [Uses Canva MCP to export]

User: List available templates
Claude: [Uses Canva MCP to list templates]
```

## Authentication

Authenticates via Canva's OAuth flow on first use.

## License

Proprietary - Canva
