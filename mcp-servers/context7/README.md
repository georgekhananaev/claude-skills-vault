# Context7 MCP Server

Resolve library IDs and fetch up-to-date documentation for libraries and frameworks.

## Source

- **Official URL**: [mcp.context7.com](https://mcp.context7.com)
- **Documentation**: [Context7 Docs](https://upstash.com/docs/context7)
- **Maintainer**: Upstash

## Quick Install

```bash
claude mcp add context7 --transport http https://mcp.context7.com/mcp
```

## Features

- **Library Documentation**: Fetch up-to-date docs
- **Version Support**: Access versioned documentation
- **Code Examples**: Get implementation examples
- **API References**: Full API documentation

## Configuration

No environment variables required.

## Claude Code Config

```json
{
  "mcpServers": {
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `resolve-library-id` | Resolve library name to Context7 ID |
| `get-library-docs` | Fetch library documentation |

## Usage

```
User: Get the latest React documentation
Claude: [Uses resolve-library-id then get-library-docs]

User: How do I use useState in React 18?
Claude: [Fetches React docs and explains]

User: Show me Next.js App Router docs
Claude: [Resolves Next.js and fetches routing docs]
```

## Supported Libraries

Context7 indexes documentation for popular libraries:
- **Frontend**: React, Vue, Angular, Svelte
- **Frameworks**: Next.js, Nuxt, Remix, Astro
- **Backend**: Express, Fastify, Hono
- **Databases**: Prisma, Drizzle, TypeORM
- And many more...

## Notes

- Documentation fetched in real-time
- Supports versioned documentation
- Great for staying current with latest APIs

## License

Proprietary - Context7
