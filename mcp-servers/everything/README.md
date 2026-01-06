# Everything MCP Server

Reference/test server demonstrating MCP capabilities with prompts, resources, and tools.

## Source

- **npm**: [@modelcontextprotocol/server-everything](https://www.npmjs.com/package/@modelcontextprotocol/server-everything)
- **GitHub**: [modelcontextprotocol/servers/src/everything](https://github.com/modelcontextprotocol/servers/tree/main/src/everything)
- **Maintainer**: Anthropic (MCP Steering Group)

## Quick Install

```bash
claude mcp add everything -s user -- npx -y @modelcontextprotocol/server-everything
```

## Features

- **Reference Implementation**: Example of all MCP features
- **Prompts**: Sample prompt templates
- **Resources**: Example resources
- **Tools**: Demonstration tools
- **Testing**: Useful for testing MCP clients

## Configuration

No environment variables required.

## Claude Code Config

```json
{
  "mcpServers": {
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
```

## Capabilities

| Feature | Description |
|---------|-------------|
| Prompts | Sample prompt templates |
| Resources | Static and dynamic resources |
| Tools | Echo, add numbers, long running |
| Sampling | Request LLM completions |

## Use Cases

- Learning MCP protocol
- Testing Claude Code MCP integration
- Debugging MCP client issues
- Reference for building custom servers

## License

MIT - [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
