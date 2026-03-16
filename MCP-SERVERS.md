# MCP Servers

Model Context Protocol server configurations for Claude Code.

## Custom Implementations

Full source code with advanced features:

| Server | Description | Config |
|--------|-------------|--------|
| **[jira-bridge](mcp-servers/jira-bridge)** | Jira issues, JQL search, sprint management | [README](mcp-servers/jira-bridge/README.md) |
| **[mongodb](mcp-servers/mongodb)** | MongoDB with aggregation, schema analysis, indexes | [README](mcp-servers/mongodb/README.md) |
| **[postgres-mcp](mcp-servers/postgres-mcp)** | PostgreSQL queries, explain plans, table stats | [README](mcp-servers/postgres-mcp/README.md) |
| **[supabase](mcp-servers/supabase)** | Database, auth, storage, edge functions | [README](mcp-servers/supabase/README.md) |

## Official @modelcontextprotocol Servers

### Active

| Server | Description | Source |
|--------|-------------|--------|
| **[everything](mcp-servers/everything)** | Reference/test server with all MCP features | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/everything) |
| **[fetch](mcp-servers/fetch)** | Web content fetching for LLM consumption | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) |
| **[filesystem](mcp-servers/filesystem)** | Secure file operations with access controls | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) |
| **[memory](mcp-servers/memory)** | Knowledge graph persistent memory | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) |
| **[sequential-thinking](mcp-servers/sequential-thinking)** | Step-by-step problem solving | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) |
| **[time](mcp-servers/time)** | Time and timezone operations | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/time) |

### Archived (still functional)

| Server | Description | Source |
|--------|-------------|--------|
| **[git](mcp-servers/git)** | Git repository operations | [GitHub](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/git) |
| **[slack](mcp-servers/slack)** | Slack messaging and channels | [GitHub](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/slack) |
| **[sqlite](mcp-servers/sqlite)** | SQLite database access | [GitHub](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sqlite) |

## Third-Party Official Servers

| Server | Description | Source |
|--------|-------------|--------|
| **[airtable](mcp-servers/airtable)** | Airtable spreadsheet/database | [npm](https://www.npmjs.com/package/@domdomegg/airtable-mcp-server) |
| **[atlassian](mcp-servers/atlassian)** | Jira and Confluence integration | [Atlassian](https://mcp.atlassian.com) |
| **[aws](mcp-servers/aws)** | AWS Labs MCP servers (64+ servers) | [GitHub](https://github.com/awslabs/mcp) |
| **[canva](mcp-servers/canva)** | Canva design platform | [Canva](https://mcp.canva.com) |
| **[chrome-devtools](mcp-servers/chrome-devtools)** | Browser automation, performance, debugging | [GitHub](https://github.com/ChromeDevTools/chrome-devtools-mcp) |
| **[cloudflare](mcp-servers/cloudflare)** | Cloudflare Workers, KV, R2, D1 | [Docs](https://developers.cloudflare.com/agents/model-context-protocol/) |
| **[codex](mcp-servers/codex)** | OpenAI Codex integration | [OpenAI](https://platform.openai.com/) |
| **[context7](mcp-servers/context7)** | Library documentation fetching | [Upstash](https://upstash.com/docs/context7) |
| **[figma](mcp-servers/figma)** | Figma design inspection | [Docs](https://developers.figma.com/docs/figma-mcp-server/) |
| **[gcp](mcp-servers/gcp)** | Google Cloud Platform | [npm](https://www.npmjs.com/package/@eniayomi/gcp-mcp-server) |
| **[github](mcp-servers/github)** | GitHub repos, issues, PRs, Actions | [GitHub](https://github.com/github/github-mcp-server) |
| **[kubernetes](mcp-servers/kubernetes)** | Kubernetes cluster management | [GitHub](https://github.com/Flux159/mcp-server-kubernetes) |
| **[linear](mcp-servers/linear)** | Linear issue tracking | [Docs](https://linear.app/docs/mcp) |
| **[monday](mcp-servers/monday)** | Monday.com work management | [GitHub](https://github.com/mondaycom/mcp) |
| **[mui](mcp-servers/mui)** | Material UI documentation | [npm](https://www.npmjs.com/package/@mui/mcp) |
| **[netlify](mcp-servers/netlify)** | Netlify site deployment | [Netlify](https://netlify-mcp.netlify.app) |
| **[nextjs](mcp-servers/nextjs)** | Next.js dev server integration | [Docs](https://nextjs.org/docs/app/guides/mcp) |
| **[notion](mcp-servers/notion)** | Notion pages and databases | [GitHub](https://github.com/makenotion/notion-mcp-server) |
| **[playwright](mcp-servers/playwright)** | Browser automation | [npm](https://www.npmjs.com/package/@playwright/mcp) |
| **[posthog](mcp-servers/posthog)** | Product analytics | [PostHog](https://mcp.posthog.com) |
| **[puppeteer](mcp-servers/puppeteer)** | Browser automation (Anthropic) | [npm](https://www.npmjs.com/package/@anthropic-ai/mcp-puppeteer) |
| **[sentry](mcp-servers/sentry)** | Error tracking & monitoring | [Sentry](https://mcp.sentry.dev) |
| **[stripe](mcp-servers/stripe)** | Payments integration | [Stripe](https://mcp.stripe.com) |
| **[vercel](mcp-servers/vercel)** | Vercel deployment platform | [Vercel](https://mcp.vercel.com) |

## SDK References

Official SDKs for building MCP servers: **[sdk-references](mcp-servers/sdk-references)**

| Language | Repository | Maintainer |
|----------|------------|------------|
| TypeScript | [typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) | Anthropic |
| Python | [python-sdk](https://github.com/modelcontextprotocol/python-sdk) | Anthropic |
| Go | [go-sdk](https://github.com/modelcontextprotocol/go-sdk) | Google |
| Rust | [rust-sdk](https://github.com/modelcontextprotocol/rust-sdk) | Anthropic |
| Java | [java-sdk](https://github.com/modelcontextprotocol/java-sdk) | Community |
| Kotlin | [kotlin-sdk](https://github.com/modelcontextprotocol/kotlin-sdk) | JetBrains |
| C# | [csharp-sdk](https://github.com/modelcontextprotocol/csharp-sdk) | Microsoft |
| Swift | [swift-sdk](https://github.com/modelcontextprotocol/swift-sdk) | Community |
| Ruby | [ruby-sdk](https://github.com/modelcontextprotocol/ruby-sdk) | Shopify |
| PHP | [php-sdk](https://github.com/modelcontextprotocol/php-sdk) | PHP Foundation |

## Quick Setup

```bash
# Remote servers (OAuth)
claude mcp add linear --transport sse https://mcp.linear.app/sse
claude mcp add figma --transport http https://mcp.figma.com/mcp

# NPX-based servers
claude mcp add github -s user -- npx -y @modelcontextprotocol/server-github
claude mcp add memory -s user -- npx -y @modelcontextprotocol/server-memory
```
