# Figma MCP Server

Access and inspect Figma designs directly from Claude.

## Source

- **Official URL**: [mcp.figma.com](https://mcp.figma.com)
- **Documentation**: [Figma MCP Docs](https://developers.figma.com/docs/figma-mcp-server/)
- **Maintainer**: Figma

## Quick Install

```bash
# Remote (recommended)
claude mcp add figma --transport http https://mcp.figma.com/mcp

# Local (Figma desktop app)
claude mcp add figma --transport sse http://127.0.0.1:3845/sse
```

## Features

- **Inspect Designs**: Access file structure and properties
- **Extract Components**: Get component details
- **Style Information**: Colors, typography, effects
- **Layer Hierarchy**: Navigate design structure

## Configuration

No environment variables required - authenticates via Figma's OAuth flow on first use.

## Claude Code Config

```json
{
  "mcpServers": {
    "figma": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `get_file` | Get file structure and metadata |
| `get_node` | Get specific node details |
| `get_styles` | List file styles |
| `get_components` | List components |
| `get_images` | Export images/assets |

## Usage

```
User: What's the structure of my Figma design?
Claude: [Uses get_file tool]

User: What colors are used in the header component?
Claude: [Uses get_node and get_styles tools]

User: Export the logo as PNG
Claude: [Uses get_images tool]
```

## Authentication

Uses OAuth to connect to your Figma account. On first use, you'll be prompted to authorize access.

## Notes

- Requires Figma account
- Read-only access to designs
- File must be accessible to authenticated user

## License

Proprietary - Figma
