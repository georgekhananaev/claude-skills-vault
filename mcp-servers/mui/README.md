# Material UI (MUI) MCP Server

Access MUI component documentation, API references, and code snippets.

## Source

- **npm**: [@mui/mcp](https://www.npmjs.com/package/@mui/mcp)
- **Documentation**: [MUI Docs](https://mui.com/)
- **Maintainer**: MUI

## Quick Install

```bash
claude mcp add mui-mcp -s user -- npx -y @mui/mcp@latest
```

## Features

- **Component Documentation**: Full API references
- **Code Examples**: Ready-to-use snippets
- **Theming Guidance**: Customization help
- **Best Practices**: Implementation patterns

## Configuration

No environment variables required.

## Claude Code Config

```json
{
  "mcpServers": {
    "mui": {
      "command": "npx",
      "args": ["-y", "@mui/mcp@latest"]
    }
  }
}
```

## Supported Packages

| Package | Version | Description |
|---------|---------|-------------|
| `@mui/material` | 5.x, 6.x, 7.x | Core components |
| `@mui/x-data-grid` | 7.x, 8.x | Data grid |
| `@mui/x-date-pickers` | 7.x, 8.x | Date/time pickers |
| `@mui/x-charts` | 7.x, 8.x | Charts |
| `@mui/x-tree-view` | 7.x, 8.x | Tree view |

## Tools

| Tool | Description |
|------|-------------|
| `useMuiDocs` | Fetch MUI documentation index |
| `fetchDocs` | Get specific documentation pages |

## Usage

```
User: How do I use the DataGrid component?
Claude: [Uses useMuiDocs to fetch DataGrid documentation]

User: Show me how to customize the Button theme
Claude: [Fetches theming docs and provides examples]

User: What props does TextField accept?
Claude: [Fetches TextField API documentation]
```

## Notes

- Supports multiple MUI package versions
- Documentation is fetched in real-time
- Provides accurate, up-to-date API info

## License

MIT - MUI
