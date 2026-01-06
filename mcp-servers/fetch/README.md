# Fetch MCP Server

Web content fetching and conversion optimized for LLM consumption.

## Source

- **npm**: [@modelcontextprotocol/server-fetch](https://www.npmjs.com/package/@modelcontextprotocol/server-fetch)
- **GitHub**: [modelcontextprotocol/servers/src/fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)
- **Maintainer**: Anthropic (MCP Steering Group)

## Quick Install

```bash
claude mcp add fetch -s user -- npx -y @modelcontextprotocol/server-fetch
```

## Features

- **Web Fetching**: Retrieve content from URLs
- **HTML to Markdown**: Convert pages for LLM processing
- **Content Extraction**: Clean text extraction
- **Efficient**: Optimized for token efficiency

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `USER_AGENT` | Custom user agent | MCP Fetch |

## Claude Code Config

```json
{
  "mcpServers": {
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `fetch` | Fetch URL and convert to markdown |

## Usage

```
User: Fetch the React documentation page
Claude: [Uses fetch tool to get and convert the page]

User: What does this article say? https://example.com/article
Claude: [Uses fetch to retrieve and summarize content]
```

## Notes

- Respects robots.txt
- Handles redirects
- Converts HTML tables to markdown
- Extracts main content, removes ads/navigation

## License

MIT - [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
