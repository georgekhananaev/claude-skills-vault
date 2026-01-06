# Next.js MCP Server

Real-time integration with Next.js development server for AI-powered debugging, error detection, and application insights.

## Source

- **npm**: [next-devtools-mcp](https://www.npmjs.com/package/next-devtools-mcp)
- **Documentation**: [Next.js MCP Guide](https://nextjs.org/docs/app/guides/mcp)
- **Maintainer**: Vercel

## Quick Install

```bash
claude mcp add next-devtools -s user -- npx -y next-devtools-mcp@latest
```

## Requirements

- **Next.js 16+** (includes built-in MCP endpoint at `/_next/mcp`)
- Running development server (`npm run dev`)

## How It Works

1. Next.js 16+ includes a built-in MCP endpoint at `/_next/mcp`
2. `next-devtools-mcp` automatically discovers and connects to running Next.js instances
3. AI agents communicate with this endpoint to access application internals
4. Supports multiple Next.js instances on different ports

## Features

- **Real-time Error Detection**: Build, runtime, and type errors from dev server
- **Live State Queries**: Access runtime application information
- **Server Actions Inspection**: Look up Server Actions by ID
- **Development Logs**: Access console and server output
- **Project Structure Analysis**: Query routes, components, rendering details

## Configuration

No environment variables required.

## Claude Code Config

Add to `.mcp.json` at your project root:

```json
{
  "mcpServers": {
    "next-devtools": {
      "command": "npx",
      "args": ["-y", "next-devtools-mcp@latest"]
    }
  }
}
```

Or add globally:

```json
{
  "mcpServers": {
    "next-devtools": {
      "command": "npx",
      "args": ["-y", "next-devtools-mcp@latest"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `get_errors` | Retrieve build, runtime, and type errors from dev server |
| `get_logs` | Get path to development log file with console/server output |
| `get_page_metadata` | Query page routes, components, and rendering details |
| `get_project_metadata` | Retrieve project structure, configuration, and dev server URL |
| `get_server_action_by_id` | Look up Server Actions by ID to find source files |

## Usage

```
User: What errors are in my Next.js app?
Claude: [Uses get_errors to check for build/runtime/type errors]

User: What routes does my app have?
Claude: [Uses get_page_metadata to list all routes and components]

User: Where is this Server Action defined?
Claude: [Uses get_server_action_by_id to locate source file]

User: Show me the project structure
Claude: [Uses get_project_metadata to display configuration and structure]
```

## Workflow

1. Start your dev server: `npm run dev`
2. Agent automatically connects via `next-devtools-mcp`
3. Open app in browser (required for some features)
4. Query agent for insights (errors, routes, state, etc.)

## Use Cases

- **Debugging**: Quickly identify and fix errors without manually checking terminal
- **Code Generation**: Generate code that follows your project patterns
- **Navigation**: Understand app router layout and page structure
- **Upgrades**: Automated upgrade helpers with codemods
- **Testing**: Integrates with Playwright MCP for browser testing

## Comparison with Other Tools

| Feature | Next.js MCP | Manual Debugging |
|---------|-------------|------------------|
| Error Detection | Real-time, automated | Check terminal manually |
| Project Insight | Structured data | Browse files manually |
| Server Actions | ID-based lookup | Search codebase |
| Context Awareness | Full app context | Limited |

## Related MCP Servers

- **[Playwright MCP](../playwright/)**: Browser automation for testing
- **[Context7 MCP](../context7/)**: Fetch Next.js documentation

## Security Notes

- Only works in development mode
- Does not expose production application data
- Runs locally on your development machine

## License

MIT - Vercel