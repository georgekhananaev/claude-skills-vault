# Memory MCP Server

Knowledge graph-based persistent memory system for LLMs.

## Source

- **npm**: [@modelcontextprotocol/server-memory](https://www.npmjs.com/package/@modelcontextprotocol/server-memory)
- **GitHub**: [modelcontextprotocol/servers/src/memory](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)
- **Maintainer**: Anthropic (MCP Steering Group)

## Quick Install

```bash
claude mcp add memory -s user -- npx -y @modelcontextprotocol/server-memory
```

## Features

- **Knowledge Graph**: Store entities and relations
- **Persistent**: Data survives across sessions
- **Semantic**: Natural language queries
- **Contextual**: Retrieve relevant memories

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MEMORY_FILE_PATH` | Path to memory store | memory.json (cwd) |

## Claude Code Config

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "/path/to/memory.json"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `create_entities` | Create new entities in the knowledge graph |
| `create_relations` | Create relations between entities |
| `add_observations` | Add observations to entities |
| `delete_entities` | Remove entities |
| `delete_observations` | Remove observations |
| `delete_relations` | Remove relations |
| `read_graph` | Read the entire knowledge graph |
| `search_nodes` | Search for nodes |
| `open_nodes` | Open specific nodes by name |

## Usage

```
User: Remember that John works at Acme Corp
Claude: [Creates entities for John and Acme Corp, creates "works_at" relation]

User: Where does John work?
Claude: [Searches memory and finds the relation]

User: What do you know about our project?
Claude: [Searches for all project-related entities]
```

## Data Model

```
Entity: { name, entityType, observations[] }
Relation: { from, to, relationType }
```

## Use Cases

- Remember user preferences
- Track project context
- Store research findings
- Maintain conversation history

## License

MIT - [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
