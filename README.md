# Claude Skills Vault

![Preview](preview.jpg)

A curated collection of skills, commands, and MCP servers for Claude Code.

## Skills

### Core Skills

| Skill | Description |
|-------|-------------|
| **fastapi-senior-dev** | Senior Python Backend Engineer skill for production-ready FastAPI |
| **gemini-cli** | Run Gemini CLI for AI queries and comparisons |
| **mcp-builder** | Guide for creating high-quality MCP servers (Python/TypeScript) |
| **pep8** | Python 3.11+ style enforcement with PEP 8, type hints, and check scripts |
| **pydantic-model** | Pydantic v2 model patterns for validation and MongoDB |
| **skill-creator** | Guide for creating Claude Code skills |
| **system-architect** | System architecture patterns and design guidance |
| **testing-automation-expert** | Production-grade testing strategies (pytest, Jest, Playwright) |
| **token-formatter** | Token compression and formatting utilities |

### Document Skills

| Skill | Description |
|-------|-------------|
| **docx** | Word document handling with OOXML schemas |
| **md** | Markdown validation and processing |
| **pdf** | PDF form filling, extraction, and validation |
| **pptx** | PowerPoint manipulation and HTML-to-PPTX |
| **toon** | Token-Oriented Object Notation - compact, schema-aware data format for LLM prompts |
| **xlsx** | Excel spreadsheet handling and formula recalculation |

## Commands

| Command | Description |
|---------|-------------|
| `/git-commit` | Safe git commit with conventional commits format |
| `/git-push` | Git push with uncommitted changes check and changelog versioning |
| `/create-skill` | Create new skills from templates |
| `/plan-feature` | Production-grade feature planning with multi-source validation |

## MCP Servers

### Custom Implementations

Full source code with advanced features:

| Server | Description |
|--------|-------------|
| **[jira-bridge](mcp-servers/jira-bridge)** | Jira issues, JQL search, sprint management |
| **[mongodb](mcp-servers/mongodb)** | MongoDB with aggregation, schema analysis, indexes |
| **[postgres-mcp](mcp-servers/postgres-mcp)** | PostgreSQL queries, explain plans, table stats |
| **[supabase](mcp-servers/supabase)** | Database, auth, storage, edge functions |

### Reference Configurations

Ready-to-use configurations for official MCP servers:

#### Official @modelcontextprotocol Servers (Active)

| Server | Description | Source |
|--------|-------------|--------|
| **[everything](mcp-servers/everything)** | Reference/test server with all MCP features | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/everything) |
| **[fetch](mcp-servers/fetch)** | Web content fetching for LLM consumption | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) |
| **[filesystem](mcp-servers/filesystem)** | Secure file operations with access controls | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) |
| **[memory](mcp-servers/memory)** | Knowledge graph persistent memory | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) |
| **[sequential-thinking](mcp-servers/sequential-thinking)** | Step-by-step problem solving | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) |
| **[time](mcp-servers/time)** | Time and timezone operations | [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/time) |

#### Official @modelcontextprotocol Servers (Archived)

These servers are still functional but no longer actively maintained:

| Server | Description | Source |
|--------|-------------|--------|
| **[git](mcp-servers/git)** | Git repository operations | [GitHub](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/git) |
| **[slack](mcp-servers/slack)** | Slack messaging and channels | [GitHub](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/slack) |
| **[sqlite](mcp-servers/sqlite)** | SQLite database access | [GitHub](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sqlite) |

#### Third-Party Official Servers

| Server | Description | Source |
|--------|-------------|--------|
| **[airtable](mcp-servers/airtable)** | Airtable spreadsheet/database | [npm](https://www.npmjs.com/package/@domdomegg/airtable-mcp-server) |
| **[atlassian](mcp-servers/atlassian)** | Jira and Confluence integration | [Atlassian](https://mcp.atlassian.com) |
| **[aws](mcp-servers/aws)** | AWS Labs MCP servers (64+ servers) | [GitHub](https://github.com/awslabs/mcp) |
| **[canva](mcp-servers/canva)** | Canva design platform | [Canva](https://mcp.canva.com) |
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

### SDK References

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

## Tutorials

- [Commands Tutorial](tutorials/COMMANDS_TUTORIAL.md) - Creating slash commands
- [Skills Tutorial](tutorials/SKILLS_TUTORIAL.md) - Creating and using skills
- [MCP Servers Tutorial](tutorials/MCP_SERVERS_TUTORIAL.md) - Building MCP servers

## Installation

```bash
git clone https://github.com/georgekhananaev/claude-skills-vault.git

# Copy skills to your project
cp -r claude-skills-vault/.claude your-project/
```

## Quick Start

### Add an MCP Server

```bash
# Remote servers (OAuth)
claude mcp add linear --transport sse https://mcp.linear.app/sse
claude mcp add figma --transport http https://mcp.figma.com/mcp

# NPX-based servers
claude mcp add github -s user -- npx -y @modelcontextprotocol/server-github
claude mcp add memory -s user -- npx -y @modelcontextprotocol/server-memory
```

### Use a Skill

Skills are automatically loaded from `.claude/skills/`. Reference them in your prompts or use the `/create-skill` command to create new ones.

## Contributing

Contributions are welcome! Feel free to submit pull requests with new skills, commands, or MCP servers.

## Credits

Created by **George Khananaev**

Skills sourced from [ComposioHQ](https://github.com/ComposioHQ): document-skills (xlsx, docx, pptx, pdf), project-change-log, skill-creator, mcp-builder

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## License

[MIT License](LICENSE) - See [NOTICE](NOTICE) for attribution guidelines.
