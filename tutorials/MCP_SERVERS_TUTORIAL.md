# MCP Servers Tutorial

A comprehensive guide to building Model Context Protocol (MCP) servers for Claude Code.

## Table of Contents

1. [What is MCP?](#what-is-mcp)
2. [Architecture Overview](#architecture-overview)
3. [Setting Up Your Development Environment](#setting-up-your-development-environment)
4. [Building Your First MCP Server](#building-your-first-mcp-server)
5. [Core Concepts](#core-concepts)
6. [Tools Implementation](#tools-implementation)
7. [Resources Implementation](#resources-implementation)
8. [Prompts Implementation](#prompts-implementation)
9. [Configuration & Deployment](#configuration--deployment)
10. [Advanced Patterns](#advanced-patterns)
11. [Testing & Debugging](#testing--debugging)
12. [Best Practices](#best-practices)
13. [Examples](#examples)

---

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard that enables AI models to interact with external systems. It provides a unified way for Claude to:

- **Execute tools**: Run functions, query databases, call APIs
- **Access resources**: Read files, fetch data, browse content
- **Use prompts**: Pre-defined prompt templates

### MCP vs Skills

| Aspect | MCP Servers | Skills |
|--------|-------------|--------|
| Purpose | External tool execution | Knowledge & instructions |
| Runtime | Separate process | In Claude's context |
| Language | Any (TypeScript, Python, etc.) | Markdown |
| Capabilities | Infinite (any API/service) | Claude's built-in abilities |
| State | Can maintain state | Stateless |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Code                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    MCP Client                            ││
│  └────────────────────────┬────────────────────────────────┘│
└───────────────────────────┼─────────────────────────────────┘
                            │ stdio / SSE
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  MCP Server 1 │   │  MCP Server 2 │   │  MCP Server 3 │
│  (postgres)   │   │  (jira)       │   │  (slack)      │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        ▼                   ▼                   ▼
   [PostgreSQL]         [Jira API]         [Slack API]
```

### Communication Flow

1. Claude requests tool execution
2. MCP client sends request to appropriate server
3. Server executes operation
4. Server returns result
5. Claude processes result

---

## Setting Up Your Development Environment

### Prerequisites

```bash
# Node.js 18+ required
node --version  # v18.0.0 or higher

# Install MCP SDK
npm install @modelcontextprotocol/sdk
```

### Project Structure

```
my-mcp-server/
├── src/
│   ├── index.ts        # Entry point
│   ├── tools/          # Tool implementations
│   │   └── myTool.ts
│   ├── resources/      # Resource handlers
│   │   └── myResource.ts
│   └── utils/          # Utilities
│       └── helpers.ts
├── package.json
├── tsconfig.json
└── README.md
```

### package.json Template

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx watch src/index.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.3.0",
    "tsx": "^4.7.0"
  }
}
```

### tsconfig.json Template

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

---

## Building Your First MCP Server

### Minimal Example

```typescript
#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// Create server instance
const server = new Server(
  {
    name: "my-first-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "hello",
      description: "Say hello to someone",
      inputSchema: {
        type: "object",
        properties: {
          name: {
            type: "string",
            description: "Name to greet",
          },
        },
        required: ["name"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "hello") {
    const greeting = `Hello, ${args.name}!`;
    return {
      content: [{ type: "text", text: greeting }],
    };
  }

  throw new Error(`Unknown tool: ${name}`);
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Server started");
}

main().catch(console.error);
```

---

## Core Concepts

### Server Initialization

```typescript
const server = new Server(
  {
    name: "server-name",      // Unique identifier
    version: "1.0.0",         // Semantic version
  },
  {
    capabilities: {
      tools: {},              // Enable tools
      resources: {},          // Enable resources
      prompts: {},            // Enable prompts
    },
  }
);
```

### Transport Types

#### stdio (Standard)
```typescript
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const transport = new StdioServerTransport();
await server.connect(transport);
```

#### SSE (Server-Sent Events)
```typescript
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import express from "express";

const app = express();
const transport = new SSEServerTransport("/mcp", app);
await server.connect(transport);
app.listen(3000);
```

### Request Handlers

```typescript
// Pattern: server.setRequestHandler(Schema, handler)
server.setRequestHandler(ListToolsRequestSchema, async () => {
  // Return list of tools
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // Handle tool execution
});
```

---

## Tools Implementation

### Tool Definition Schema

```typescript
{
  name: "tool_name",
  description: "What this tool does",
  inputSchema: {
    type: "object",
    properties: {
      param1: {
        type: "string",
        description: "Parameter description"
      },
      param2: {
        type: "number",
        description: "Numeric parameter"
      },
      param3: {
        type: "array",
        items: { type: "string" },
        description: "Array parameter"
      }
    },
    required: ["param1"]
  }
}
```

### Implementing Tools

```typescript
import { z } from "zod";

// Define input schema with Zod for validation
const SearchSchema = z.object({
  query: z.string().describe("Search query"),
  limit: z.number().default(10).describe("Max results"),
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "search": {
      // Validate input
      const { query, limit } = SearchSchema.parse(args);

      // Execute operation
      const results = await performSearch(query, limit);

      // Return result
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    }

    default:
      return {
        content: [{ type: "text", text: `Unknown tool: ${name}` }],
        isError: true,
      };
  }
});
```

### Tool Response Types

```typescript
// Text response
{
  content: [{ type: "text", text: "Result text" }]
}

// Image response
{
  content: [{
    type: "image",
    data: base64EncodedImage,
    mimeType: "image/png"
  }]
}

// Error response
{
  content: [{ type: "text", text: "Error message" }],
  isError: true
}

// Multiple content items
{
  content: [
    { type: "text", text: "Summary" },
    { type: "text", text: JSON.stringify(data) }
  ]
}
```

---

## Resources Implementation

Resources provide read-only access to data sources.

### Listing Resources

```typescript
import {
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [
    {
      uri: "myapp://config/settings",
      name: "Application Settings",
      mimeType: "application/json",
      description: "Current application configuration",
    },
    {
      uri: "myapp://data/users",
      name: "User List",
      mimeType: "application/json",
    },
  ],
}));
```

### Reading Resources

```typescript
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  switch (uri) {
    case "myapp://config/settings":
      const settings = await loadSettings();
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify(settings, null, 2),
          },
        ],
      };

    case "myapp://data/users":
      const users = await getUsers();
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify(users, null, 2),
          },
        ],
      };

    default:
      throw new Error(`Unknown resource: ${uri}`);
  }
});
```

### Dynamic Resources with Templates

```typescript
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [],  // No static resources
  resourceTemplates: [
    {
      uriTemplate: "myapp://users/{userId}",
      name: "User Profile",
      mimeType: "application/json",
    },
  ],
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  const match = uri.match(/^myapp:\/\/users\/(.+)$/);

  if (match) {
    const userId = match[1];
    const user = await getUser(userId);
    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(user, null, 2),
        },
      ],
    };
  }

  throw new Error(`Unknown resource: ${uri}`);
});
```

---

## Prompts Implementation

Prompts are reusable prompt templates.

### Listing Prompts

```typescript
import {
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

server.setRequestHandler(ListPromptsRequestSchema, async () => ({
  prompts: [
    {
      name: "code-review",
      description: "Review code for issues",
      arguments: [
        {
          name: "code",
          description: "Code to review",
          required: true,
        },
        {
          name: "language",
          description: "Programming language",
          required: false,
        },
      ],
    },
  ],
}));
```

### Getting Prompts

```typescript
server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "code-review") {
    const code = args?.code || "";
    const language = args?.language || "unknown";

    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Review this ${language} code for issues:\n\n\`\`\`${language}\n${code}\n\`\`\``,
          },
        },
      ],
    };
  }

  throw new Error(`Unknown prompt: ${name}`);
});
```

---

## Configuration & Deployment

### Claude Code Configuration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/absolute/path/to/dist/index.js"],
      "env": {
        "API_KEY": "your-api-key",
        "DATABASE_URL": "connection-string"
      }
    }
  }
}
```

### Using npx (Published Package)

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "my-mcp-server"]
    }
  }
}
```

### Using Python

```json
{
  "mcpServers": {
    "python-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/server"
      }
    }
  }
}
```

### Environment Variables

Access in your server:

```typescript
const config = {
  apiKey: process.env.API_KEY || "",
  databaseUrl: process.env.DATABASE_URL || "",
  debug: process.env.DEBUG === "true",
};

if (!config.apiKey) {
  throw new Error("API_KEY environment variable required");
}
```

---

## Advanced Patterns

### 1. Error Handling

```typescript
async function safeExecute<T>(
  operation: () => Promise<T>,
  errorMessage: string
): Promise<{ content: Array<{ type: string; text: string }>; isError?: boolean }> {
  try {
    const result = await operation();
    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      content: [{ type: "text", text: `${errorMessage}: ${message}` }],
      isError: true,
    };
  }
}
```

### 2. Rate Limiting

```typescript
class RateLimiter {
  private requests: number[] = [];
  private limit: number;
  private window: number;

  constructor(limit: number, windowMs: number) {
    this.limit = limit;
    this.window = windowMs;
  }

  async acquire(): Promise<void> {
    const now = Date.now();
    this.requests = this.requests.filter(t => now - t < this.window);

    if (this.requests.length >= this.limit) {
      const waitTime = this.window - (now - this.requests[0]);
      await new Promise(resolve => setTimeout(resolve, waitTime));
      return this.acquire();
    }

    this.requests.push(now);
  }
}

const limiter = new RateLimiter(100, 60000); // 100 requests per minute

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  await limiter.acquire();
  // Handle request
});
```

### 3. Caching

```typescript
class Cache<T> {
  private data = new Map<string, { value: T; expires: number }>();
  private ttl: number;

  constructor(ttlMs: number) {
    this.ttl = ttlMs;
  }

  get(key: string): T | undefined {
    const entry = this.data.get(key);
    if (!entry) return undefined;
    if (Date.now() > entry.expires) {
      this.data.delete(key);
      return undefined;
    }
    return entry.value;
  }

  set(key: string, value: T): void {
    this.data.set(key, {
      value,
      expires: Date.now() + this.ttl,
    });
  }
}

const cache = new Cache<string>(5 * 60 * 1000); // 5 minute cache
```

### 4. Connection Pooling

```typescript
import { Pool } from "pg";

const pool = new Pool({
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

async function query(sql: string, params: unknown[]) {
  const client = await pool.connect();
  try {
    return await client.query(sql, params);
  } finally {
    client.release();
  }
}
```

### 5. Logging

```typescript
function log(level: "info" | "warn" | "error", message: string, data?: unknown) {
  const timestamp = new Date().toISOString();
  const logMessage = JSON.stringify({ timestamp, level, message, data });
  console.error(logMessage); // stderr for logs (stdout reserved for MCP)
}

log("info", "Server started", { port: 3000 });
log("error", "Operation failed", { error: err.message });
```

---

## Testing & Debugging

### Using MCP Inspector

```bash
# Install inspector
npm install -g @anthropic/mcp-inspector

# Run with your server
npx @anthropic/mcp-inspector node dist/index.js
```

### Manual Testing

```typescript
// test/manual.ts
import { spawn } from "child_process";

const server = spawn("node", ["dist/index.js"]);

// Send list tools request
const request = {
  jsonrpc: "2.0",
  id: 1,
  method: "tools/list",
  params: {},
};

server.stdin.write(JSON.stringify(request) + "\n");

server.stdout.on("data", (data) => {
  console.log("Response:", data.toString());
});
```

### Unit Tests

```typescript
// test/tools.test.ts
import { describe, it, expect } from "vitest";
import { handleSearch } from "../src/tools/search.js";

describe("search tool", () => {
  it("should return results for valid query", async () => {
    const result = await handleSearch({ query: "test", limit: 5 });
    expect(result.content).toHaveLength(1);
    expect(result.isError).toBeUndefined();
  });

  it("should handle empty query", async () => {
    const result = await handleSearch({ query: "", limit: 5 });
    expect(result.isError).toBe(true);
  });
});
```

---

## Best Practices

### Security

1. **Validate all inputs** with Zod or similar
2. **Use environment variables** for secrets
3. **Implement rate limiting** for external APIs
4. **Sanitize outputs** to prevent injection
5. **Use parameterized queries** for databases

### Performance

1. **Connection pooling** for databases
2. **Caching** for expensive operations
3. **Timeouts** for external requests
4. **Pagination** for large result sets
5. **Streaming** for large responses

### Reliability

1. **Graceful error handling**
2. **Retry with exponential backoff**
3. **Circuit breaker** for failing services
4. **Health checks** for dependencies
5. **Proper shutdown** handling

### Code Organization

```typescript
// Separate concerns
src/
├── index.ts          // Entry point, server setup
├── handlers/         // Request handlers
│   ├── tools.ts
│   ├── resources.ts
│   └── prompts.ts
├── services/         // Business logic
│   ├── database.ts
│   └── api.ts
├── utils/            // Utilities
│   ├── validation.ts
│   └── cache.ts
└── types/            // Type definitions
    └── index.ts
```

---

## Examples

### Database Server (PostgreSQL)

See `mcp-servers/postgres-mcp/` for complete implementation.

Key features:
- Query execution with row limits
- Schema exploration
- Query explanation
- Connection pooling

### API Integration (Jira)

See `mcp-servers/jira-bridge/` for complete implementation.

Key features:
- Issue CRUD operations
- JQL search
- Workflow transitions
- Sprint management

### File System Server

```typescript
const tools = [
  {
    name: "read_file",
    description: "Read file contents",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string" }
      },
      required: ["path"]
    }
  },
  {
    name: "write_file",
    description: "Write to file",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string" },
        content: { type: "string" }
      },
      required: ["path", "content"]
    }
  },
  {
    name: "list_directory",
    description: "List directory contents",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string" }
      },
      required: ["path"]
    }
  }
];
```

### REST API Wrapper

```typescript
async function apiRequest(
  method: string,
  endpoint: string,
  body?: unknown
) {
  const response = await fetch(`${baseUrl}${endpoint}`, {
    method,
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
```

---

## Quick Reference

### Minimal Server Template

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "my-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [/* tool definitions */]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // Handle tool calls
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Common Imports

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
```

---

Created by George Khananaev
