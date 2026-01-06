# Notion MCP Server

Read, search, and update Notion pages and databases.

## Source

- **GitHub**: [makenotion/notion-mcp-server](https://github.com/makenotion/notion-mcp-server) (Official by Notion)
- **npm**: [@notionhq/notion-mcp-server](https://www.npmjs.com/package/@notionhq/notion-mcp-server)
- **Maintainer**: Notion

## Quick Install

```bash
claude mcp add notion -s user -- npx -y @notionhq/notion-mcp-server
```

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAPI_MCP_HEADERS` | JSON with Authorization header | Yes |

### Getting API Key

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create new integration
3. Copy the Internal Integration Token
4. Share pages/databases with the integration

## Claude Code Config

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "OPENAPI_MCP_HEADERS": "{\"Authorization\": \"Bearer secret_...\"}"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `notion_search` | Search pages and databases |
| `notion_get_page` | Get page content |
| `notion_create_page` | Create new page |
| `notion_update_page` | Update page properties |
| `notion_query_database` | Query database entries |
| `notion_create_database` | Create new database |
| `notion_get_block_children` | Get block content |
| `notion_append_block_children` | Add blocks to page |

## Usage

```
User: Find my project notes in Notion
Claude: [Uses notion_search tool]

User: Add a new entry to my tasks database
Claude: [Uses notion_create_page tool]

User: What's in my meeting notes?
Claude: [Uses notion_get_page and notion_get_block_children]
```

## Notes

- Integration must be shared with pages to access them
- Supports both pages and databases
- Full CRUD operations available

## License

MIT - [makenotion/notion-mcp-server](https://github.com/makenotion/notion-mcp-server)
