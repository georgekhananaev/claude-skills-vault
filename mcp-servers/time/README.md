# Time MCP Server

Time and timezone conversion capabilities.

## Source

- **npm**: [@modelcontextprotocol/server-time](https://www.npmjs.com/package/@modelcontextprotocol/server-time)
- **GitHub**: [modelcontextprotocol/servers/src/time](https://github.com/modelcontextprotocol/servers/tree/main/src/time)
- **Maintainer**: Anthropic (MCP Steering Group)

## Quick Install

```bash
claude mcp add time -s user -- npx -y @modelcontextprotocol/server-time
```

## Features

- **Current Time**: Get time in any timezone
- **Conversion**: Convert between timezones
- **IANA Timezones**: Full timezone database support

## Configuration

No environment variables required.

## Claude Code Config

```json
{
  "mcpServers": {
    "time": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-time"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `get_current_time` | Get current time in a specific timezone |
| `convert_time` | Convert time between timezones |

## Usage

```
User: What time is it in Tokyo?
Claude: [Uses get_current_time with timezone: Asia/Tokyo]

User: Convert 3pm EST to London time
Claude: [Uses convert_time tool]

User: Schedule a meeting that works for NYC and Berlin
Claude: [Uses get_current_time for both zones to find overlap]
```

## Timezone Format

Uses IANA timezone names:
- `America/New_York`
- `Europe/London`
- `Asia/Tokyo`
- `Pacific/Auckland`
- `UTC`

## License

MIT - [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
