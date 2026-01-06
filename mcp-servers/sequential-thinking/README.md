# Sequential Thinking MCP Server

Dynamic and reflective problem-solving through thought sequences.

## Source

- **npm**: [@modelcontextprotocol/server-sequentialthinking](https://www.npmjs.com/package/@modelcontextprotocol/server-sequentialthinking)
- **GitHub**: [modelcontextprotocol/servers/src/sequentialthinking](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking)
- **Maintainer**: Anthropic (MCP Steering Group)

## Quick Install

```bash
claude mcp add sequential-thinking -s user -- npx -y @modelcontextprotocol/server-sequentialthinking
```

## Features

- **Step-by-Step**: Break down complex problems
- **Reflective**: Review and revise thinking
- **Dynamic**: Adjust approach as needed
- **Branching**: Explore alternative paths
- **Transparent**: Show reasoning process

## Configuration

No environment variables required.

## Claude Code Config

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequentialthinking"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `sequentialthinking` | Record a thought with metadata |

### Tool Parameters

| Parameter | Description |
|-----------|-------------|
| `thought` | The current thinking step |
| `nextThoughtNeeded` | Whether more thinking is needed |
| `thoughtNumber` | Current thought number |
| `totalThoughts` | Estimated total thoughts needed |
| `isRevision` | Whether this revises a previous thought |
| `revisesThought` | Which thought is being revised |
| `branchFromThought` | Starting point for new branch |
| `branchId` | Identifier for the branch |
| `needsMoreThoughts` | If more thoughts needed than estimated |

## Usage

```
User: Help me design a caching strategy
Claude: [Uses sequentialthinking to break down the problem]
        Thought 1: Identify what needs caching
        Thought 2: Consider cache invalidation strategies
        Thought 3: Choose storage mechanism
        [Revises thought 2 with new insights]
        [Concludes with final recommendation]
```

## Use Cases

- Complex problem solving
- System design decisions
- Debugging strategies
- Planning implementations
- Research analysis

## Benefits

- Makes reasoning visible
- Allows course correction
- Supports branching exploration
- Documents thought process

## License

MIT - [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
