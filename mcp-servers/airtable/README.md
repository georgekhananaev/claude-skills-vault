# Airtable MCP Server

Spreadsheet and database platform integration.

## Source

- **npm**: [@domdomegg/airtable-mcp-server](https://www.npmjs.com/package/@domdomegg/airtable-mcp-server)
- **GitHub**: [domdomegg/airtable-mcp-server](https://github.com/domdomegg/airtable-mcp-server)
- **Maintainer**: Community

## Quick Install

```bash
claude mcp add airtable -e AIRTABLE_API_KEY=your-token -s user -- npx -y @domdomegg/airtable-mcp-server
```

## Features

- **Base Access**: Read and write to Airtable bases
- **Record Management**: Create, update, delete records
- **Views**: Access different views
- **Filtering**: Query records with filters

## Configuration

```json
{
  "mcpServers": {
    "airtable": {
      "command": "npx",
      "args": ["-y", "@domdomegg/airtable-mcp-server"],
      "env": {
        "AIRTABLE_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AIRTABLE_API_KEY` | Airtable API key or PAT | Yes |

## Getting API Key

1. Go to [Airtable Account](https://airtable.com/account)
2. Generate a Personal Access Token
3. Grant access to needed bases

## Usage Examples

```
User: Show records from my Tasks base
Claude: [Uses Airtable MCP to list records]

User: Add a new task "Review PR"
Claude: [Uses Airtable MCP to create record]

User: Update the status of task 123 to Done
Claude: [Uses Airtable MCP to update record]

User: Show all tasks assigned to me
Claude: [Uses Airtable MCP with filter]
```

## Prerequisites

- Node.js v18+
- Airtable account with API access

## License

MIT - Community
