# MongoDB MCP Server

Custom MCP server for MongoDB with advanced query, aggregation, and schema analysis tools.

## Features

- **Find & Query**: Full MongoDB query syntax support
- **Aggregation Pipelines**: Run complex aggregation operations
- **Schema Analysis**: Infer schema from sample documents
- **Collection Stats**: Document count, size, index info
- **Index Management**: List and create indexes
- **Explain Plans**: Query execution analysis
- **Write Operations**: Insert, update, delete (configurable)

## Installation

```bash
cd mcp-servers/mongodb
npm install
npm run build
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_CONNECTION_STRING` | Connection URI | mongodb://localhost:27017 |
| `MONGODB_DATABASE` | Database name | test |
| `MAX_DOCUMENTS` | Max docs returned | 100 |
| `QUERY_TIMEOUT` | Query timeout (ms) | 30000 |
| `ALLOW_WRITES` | Enable write ops | false |

### Claude Code Config

```json
{
  "mcpServers": {
    "mongodb": {
      "command": "node",
      "args": ["/path/to/mongodb/dist/index.js"],
      "env": {
        "MONGODB_CONNECTION_STRING": "mongodb://localhost:27017",
        "MONGODB_DATABASE": "mydb",
        "ALLOW_WRITES": "false"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `find` | Find documents with filter, projection, sort, limit |
| `aggregate` | Run aggregation pipeline |
| `list_collections` | List all collections with doc counts |
| `collection_stats` | Get collection statistics |
| `analyze_schema` | Infer schema from sample documents |
| `list_indexes` | List indexes on a collection |
| `create_index` | Create new index (requires ALLOW_WRITES) |
| `explain` | Get query execution plan |
| `count` | Count documents matching filter |
| `distinct` | Get distinct values for a field |
| `insert` | Insert documents (requires ALLOW_WRITES) |
| `update` | Update documents (requires ALLOW_WRITES) |
| `delete` | Delete documents (requires ALLOW_WRITES) |

## Usage Examples

```
User: Show all collections in the database
Claude: [Uses list_collections tool]

User: Find users older than 30, sorted by name
Claude: [Uses find with filter: { age: { $gt: 30 } }, sort: { name: 1 }]

User: What's the schema of the orders collection?
Claude: [Uses analyze_schema tool]

User: Count orders by status
Claude: [Uses aggregate with $group pipeline]

User: Why is this query slow?
Claude: [Uses explain tool]
```

## Security

- Read-only by default (`ALLOW_WRITES=false`)
- Configurable query timeout
- Document limit prevents memory issues
- Use credentials with minimal permissions

## License

MIT
