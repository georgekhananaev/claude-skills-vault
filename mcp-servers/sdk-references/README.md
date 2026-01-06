# MCP SDK References

Official SDKs for building Model Context Protocol servers and clients.

## Official SDKs

| Language | Repository | Maintainer |
|----------|------------|------------|
| [TypeScript](#typescript) | [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | Anthropic |
| [Python](#python) | [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | Anthropic |
| [Go](#go) | [modelcontextprotocol/go-sdk](https://github.com/modelcontextprotocol/go-sdk) | Google |
| [Rust](#rust) | [modelcontextprotocol/rust-sdk](https://github.com/modelcontextprotocol/rust-sdk) | Anthropic |
| [Java](#java) | [modelcontextprotocol/java-sdk](https://github.com/modelcontextprotocol/java-sdk) | Community |
| [Kotlin](#kotlin) | [modelcontextprotocol/kotlin-sdk](https://github.com/modelcontextprotocol/kotlin-sdk) | JetBrains |
| [C#](#c) | [modelcontextprotocol/csharp-sdk](https://github.com/modelcontextprotocol/csharp-sdk) | Microsoft |
| [Swift](#swift) | [modelcontextprotocol/swift-sdk](https://github.com/modelcontextprotocol/swift-sdk) | Community |
| [Ruby](#ruby) | [modelcontextprotocol/ruby-sdk](https://github.com/modelcontextprotocol/ruby-sdk) | Shopify |
| [PHP](#php) | [modelcontextprotocol/php-sdk](https://github.com/modelcontextprotocol/php-sdk) | PHP Foundation |

---

## TypeScript

The primary SDK for building MCP servers and clients.

```bash
npm install @modelcontextprotocol/sdk
```

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({ name: "my-server", version: "1.0.0" });

server.tool("hello", "Say hello", { name: z.string() }, async ({ name }) => ({
  content: [{ type: "text", text: `Hello, ${name}!` }],
}));

server.run();
```

**Links:** [GitHub](https://github.com/modelcontextprotocol/typescript-sdk) | [npm](https://www.npmjs.com/package/@modelcontextprotocol/sdk)

---

## Python

High-level SDK using FastMCP for rapid development.

```bash
pip install mcp
```

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()
```

**Links:** [GitHub](https://github.com/modelcontextprotocol/python-sdk) | [PyPI](https://pypi.org/project/mcp/)

---

## Go

Official Go SDK maintained with Google.

```bash
go get github.com/modelcontextprotocol/go-sdk
```

```go
package main

import (
    "github.com/modelcontextprotocol/go-sdk/mcp"
)

func main() {
    server := mcp.NewServer("my-server", "1.0.0")

    server.AddTool("hello", "Say hello", func(args map[string]any) (any, error) {
        name := args["name"].(string)
        return map[string]any{"text": "Hello, " + name + "!"}, nil
    })

    server.Run()
}
```

**Links:** [GitHub](https://github.com/modelcontextprotocol/go-sdk)

---

## Rust

Official Rust SDK for high-performance servers.

```toml
[dependencies]
mcp-sdk = "0.1"
```

```rust
use mcp_sdk::{Server, Tool};

#[tokio::main]
async fn main() {
    let server = Server::new("my-server", "1.0.0");

    server.add_tool(Tool::new("hello", "Say hello", |args| {
        let name = args.get("name").unwrap();
        Ok(format!("Hello, {}!", name))
    }));

    server.run().await;
}
```

**Links:** [GitHub](https://github.com/modelcontextprotocol/rust-sdk) | [crates.io](https://crates.io/crates/mcp-sdk)

---

## Java

Official Java SDK for JVM-based servers.

```xml
<dependency>
    <groupId>io.modelcontextprotocol</groupId>
    <artifactId>mcp-sdk</artifactId>
    <version>1.0.0</version>
</dependency>
```

```java
import io.modelcontextprotocol.McpServer;

public class MyServer {
    public static void main(String[] args) {
        McpServer server = new McpServer("my-server", "1.0.0");

        server.addTool("hello", "Say hello", params -> {
            String name = params.get("name").toString();
            return "Hello, " + name + "!";
        });

        server.run();
    }
}
```

**Links:** [GitHub](https://github.com/modelcontextprotocol/java-sdk)

---

## Kotlin

Official Kotlin SDK maintained with JetBrains.

```kotlin
dependencies {
    implementation("io.modelcontextprotocol:mcp-sdk:1.0.0")
}
```

```kotlin
import io.modelcontextprotocol.McpServer

fun main() {
    val server = McpServer("my-server", "1.0.0")

    server.addTool("hello", "Say hello") { args ->
        val name = args["name"] as String
        "Hello, $name!"
    }

    server.run()
}
```

**Links:** [GitHub](https://github.com/modelcontextprotocol/kotlin-sdk)

---

## C#

Official C# SDK maintained with Microsoft.

```bash
dotnet add package ModelContextProtocol.Sdk
```

```csharp
using ModelContextProtocol;

var server = new McpServer("my-server", "1.0.0");

server.AddTool("hello", "Say hello", async (args) => {
    var name = args["name"].ToString();
    return $"Hello, {name}!";
});

await server.RunAsync();
```

**Links:** [GitHub](https://github.com/modelcontextprotocol/csharp-sdk) | [NuGet](https://www.nuget.org/packages/ModelContextProtocol.Sdk)

---

## Swift

Official Swift SDK for Apple platforms.

```swift
// Package.swift
dependencies: [
    .package(url: "https://github.com/modelcontextprotocol/swift-sdk", from: "1.0.0")
]
```

```swift
import MCP

let server = McpServer(name: "my-server", version: "1.0.0")

server.addTool("hello", description: "Say hello") { args in
    let name = args["name"] as! String
    return "Hello, \(name)!"
}

try await server.run()
```

**Links:** [GitHub](https://github.com/modelcontextprotocol/swift-sdk)

---

## Ruby

Official Ruby SDK maintained with Shopify.

```bash
gem install mcp-sdk
```

```ruby
require 'mcp'

server = MCP::Server.new('my-server', '1.0.0')

server.add_tool('hello', 'Say hello') do |args|
  name = args['name']
  "Hello, #{name}!"
end

server.run
```

**Links:** [GitHub](https://github.com/modelcontextprotocol/ruby-sdk) | [RubyGems](https://rubygems.org/gems/mcp-sdk)

---

## PHP

Official PHP SDK maintained with The PHP Foundation.

```bash
composer require modelcontextprotocol/sdk
```

```php
<?php
use ModelContextProtocol\McpServer;

$server = new McpServer('my-server', '1.0.0');

$server->addTool('hello', 'Say hello', function($args) {
    $name = $args['name'];
    return "Hello, {$name}!";
});

$server->run();
```

**Links:** [GitHub](https://github.com/modelcontextprotocol/php-sdk) | [Packagist](https://packagist.org/packages/modelcontextprotocol/sdk)

---

## Core Features (All SDKs)

All official SDKs provide:

- **Tools**: Expose callable functions to LLMs
- **Resources**: Provide data/content access
- **Prompts**: Define reusable prompt templates
- **Transport**: stdio, SSE, HTTP support
- **Type Safety**: Full protocol compliance

## Official Resources

- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [MCP SDK Docs](https://modelcontextprotocol.io/docs/sdk)
- [MCP Servers](https://github.com/modelcontextprotocol/servers)
- [MCP GitHub Org](https://github.com/modelcontextprotocol)

## License

MCP is an open source project hosted by The Linux Foundation.
