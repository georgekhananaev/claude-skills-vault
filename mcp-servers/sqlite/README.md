# SQLite MCP Server

Local SQLite database file access with schema inspection.

## Source

- **npm**: [@modelcontextprotocol/server-sqlite](https://www.npmjs.com/package/@modelcontextprotocol/server-sqlite)
- **GitHub**: [modelcontextprotocol/servers-archived/src/sqlite](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sqlite)
- **Status**: Archived (still functional, no longer actively maintained)

## Quick Install

```bash
claude mcp add sqlite -s user -- npx -y @modelcontextprotocol/server-sqlite --db-path ./database.db
```

## Features

- **Query Execution**: Run SQL queries
- **Schema Inspection**: List tables and columns
- **Read-only by Default**: Safe database access

## Configuration

| Argument | Description | Required |
|----------|-------------|----------|
| `--db-path` | Path to SQLite database | Yes |

## Claude Code Config

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sqlite",
        "--db-path",
        "/path/to/database.db"
      ]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `read_query` | Execute SELECT query |
| `write_query` | Execute INSERT/UPDATE/DELETE |
| `create_table` | Create new table |
| `list_tables` | List all tables |
| `describe_table` | Get table schema |
| `append_insight` | Store analysis insights |

## Resources

The server exposes a `memo://insights` resource for storing analysis insights.

## Usage

```
User: What tables are in the database?
Claude: [Uses list_tables tool]

User: Show all active users
Claude: [Uses read_query with SELECT * FROM users WHERE active = 1]

User: Describe the orders table
Claude: [Uses describe_table tool]
```

## Notes

- Creates database if it doesn't exist
- Use absolute paths for reliability
- Business intelligence memo feature for storing insights

## License

MIT - [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
