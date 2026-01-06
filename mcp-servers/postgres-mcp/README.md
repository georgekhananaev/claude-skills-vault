# PostgreSQL MCP Server

A Model Context Protocol (MCP) server that provides Claude with direct access to PostgreSQL databases for querying, schema exploration, and data analysis.

## Features

- **Query Execution**: Run SELECT queries safely
- **Schema Exploration**: List tables, columns, indexes
- **Data Analysis**: Get table statistics and row counts
- **Query Explanation**: EXPLAIN ANALYZE for performance
- **Safe Operations**: Read-only by default, configurable write access

## Installation

```bash
cd mcp-servers/postgres-mcp
npm install
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=your_database
POSTGRES_SSL=false

# Optional settings
MAX_ROWS=1000
QUERY_TIMEOUT=30000
ALLOW_WRITES=false
```

### Claude Code Configuration

Add to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "node",
      "args": ["/path/to/postgres-mcp/dist/index.js"],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "password",
        "POSTGRES_DATABASE": "mydb"
      }
    }
  }
}
```

## Available Tools

### `query`
Execute a SELECT query against the database.

```typescript
{
  name: "query",
  description: "Execute a SELECT query",
  inputSchema: {
    type: "object",
    properties: {
      sql: { type: "string", description: "SQL SELECT query" },
      params: { type: "array", description: "Query parameters" }
    },
    required: ["sql"]
  }
}
```

### `list_tables`
List all tables in the database or schema.

```typescript
{
  name: "list_tables",
  description: "List all tables",
  inputSchema: {
    type: "object",
    properties: {
      schema: { type: "string", default: "public" }
    }
  }
}
```

### `describe_table`
Get detailed information about a table.

```typescript
{
  name: "describe_table",
  description: "Get table schema, columns, and constraints",
  inputSchema: {
    type: "object",
    properties: {
      table: { type: "string" },
      schema: { type: "string", default: "public" }
    },
    required: ["table"]
  }
}
```

### `table_stats`
Get statistics about a table.

```typescript
{
  name: "table_stats",
  description: "Get row count, size, and index info",
  inputSchema: {
    type: "object",
    properties: {
      table: { type: "string" },
      schema: { type: "string", default: "public" }
    },
    required: ["table"]
  }
}
```

### `explain_query`
Get query execution plan.

```typescript
{
  name: "explain_query",
  description: "Run EXPLAIN ANALYZE on a query",
  inputSchema: {
    type: "object",
    properties: {
      sql: { type: "string" },
      analyze: { type: "boolean", default: false }
    },
    required: ["sql"]
  }
}
```

### `list_indexes`
List indexes for a table or schema.

```typescript
{
  name: "list_indexes",
  description: "List indexes with definitions",
  inputSchema: {
    type: "object",
    properties: {
      table: { type: "string" },
      schema: { type: "string", default: "public" }
    }
  }
}
```

## Usage Examples

### With Claude Code

```
User: What tables are in the database?
Claude: [Uses list_tables tool]

User: Show me the structure of the users table
Claude: [Uses describe_table tool]

User: How many active users do we have?
Claude: [Uses query tool with: SELECT COUNT(*) FROM users WHERE active = true]

User: Why is this query slow? SELECT * FROM orders WHERE...
Claude: [Uses explain_query tool to analyze]
```

## Security Considerations

1. **Read-Only by Default**: Set `ALLOW_WRITES=false` (default)
2. **Query Timeout**: Configurable timeout prevents long-running queries
3. **Row Limit**: Maximum rows returned prevents memory issues
4. **Parameterized Queries**: Prevents SQL injection
5. **Connection Pooling**: Efficient connection management
6. **SSL Support**: Enable for production

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Run locally
npm start

# Run with inspector
npx @anthropic/mcp-inspector node dist/index.js
```

## License

MIT
