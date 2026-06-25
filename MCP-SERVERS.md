# MCP Servers

Model Context Protocol (MCP) server reference for **Claude Code** — current as of **June 2026**.

[MCP](https://modelcontextprotocol.io) is an open standard for connecting Claude to external
tools, databases, and APIs. Every server listed here is backed by an officially maintained
source (Anthropic, the vendor, or an actively-updated GitHub project). Current spec revision:
**[2025-11-25](https://modelcontextprotocol.io/specification)**.

**Where to discover servers**

- **[Anthropic Directory](https://claude.ai/directory)** — ~440 vetted **remote** connectors across 30 categories (OAuth/API-key). Add any with `claude mcp add`.
- **[Official MCP Registry](https://registry.modelcontextprotocol.io)** — the canonical, machine-readable catalog (preview; `GET /v0/servers`). Source: [modelcontextprotocol/registry](https://github.com/modelcontextprotocol/registry).
- **[Plugin marketplace](https://claude.com/plugins)** — 200+ one-click Claude Code plugins (`claude-plugins-official`), many bundling a pre-configured MCP server.

This file curates the servers we use (§1–§5) plus a broad, source-linked catalog of additional
official / popular servers by category (§6).

## Three ways to add a server

| Method | Best for | How |
|--------|----------|-----|
| **Plugin marketplace** | Popular integrations, one-click + OAuth | `/plugin install <name>@claude-plugins-official` |
| **`claude mcp add`** | Remote (HTTP/SSE) or local (stdio) servers | `claude mcp add --transport http <name> <url>` |
| **`.mcp.json`** | Team-shared, project-scoped, version-controlled | commit `.mcp.json` at the repo root |

**Scopes** (`--scope`): `local` (default, `~/.claude.json`) · `project` (`.mcp.json`, shared) · `user` (all your projects).
Remote servers authenticate via OAuth 2.0 — run `/mcp` to sign in (or `claude mcp login <name>`).

**Official references**

- Connect Claude Code via MCP — <https://code.claude.com/docs/en/mcp>
- MCP quickstart — <https://code.claude.com/docs/en/mcp-quickstart>
- Discover & install plugins — <https://code.claude.com/docs/en/discover-plugins>
- Anthropic connector **Directory** (reviewed remote servers) — <https://claude.ai/directory>
- Official MCP **Registry** (preview) — <https://registry.modelcontextprotocol.io>
- Plugin catalog — <https://claude.com/plugins>
- MCP specification — <https://modelcontextprotocol.io/specification>

---

## 1. Official plugin marketplace (recommended)

The `claude-plugins-official` marketplace is registered automatically. Its **external-integration**
plugins ship a pre-configured MCP server — install one command, then authenticate in `/mcp`.
Browse with `/plugin` → **Discover**, or at [claude.com/plugins](https://claude.com/plugins).

| Service | What it connects | Install |
|---------|------------------|---------|
| **GitHub** | Repos, issues, PRs, Actions | `/plugin install github@claude-plugins-official` |
| **GitLab** | Repos, MRs, pipelines | `/plugin install gitlab@claude-plugins-official` |
| **Atlassian** | Jira & Confluence | `/plugin install atlassian@claude-plugins-official` |
| **Asana** | Tasks & projects | `/plugin install asana@claude-plugins-official` |
| **Linear** | Issue tracking | `/plugin install linear@claude-plugins-official` |
| **Notion** | Pages & databases | `/plugin install notion@claude-plugins-official` |
| **Figma** | Design inspection | `/plugin install figma@claude-plugins-official` |
| **Vercel** | Deployments & projects | `/plugin install vercel@claude-plugins-official` |
| **Firebase** | Backend services | `/plugin install firebase@claude-plugins-official` |
| **Supabase** | DB, auth, storage, edge functions | `/plugin install supabase@claude-plugins-official` |
| **Slack** | Messaging & channels | `/plugin install slack@claude-plugins-official` |
| **Sentry** | Error tracking & monitoring | `/plugin install sentry@claude-plugins-official` |

The table above is the curated highlight; the official marketplace actually carries **200+ plugins**,
many of which bundle an MCP server — e.g. `stripe`, `datadog`, `posthog`, `mongodb`, `neon`, `prisma`,
`planetscale`, `clickhouse`, `pinecone`, `playwright`, `chrome-devtools-mcp`, `sonarqube`, `semgrep`,
`auth0`, `pagerduty`, `box`, `zapier`, `huggingface`, `firecrawl`, `exa`, `postman`, `sanity`, `wix`.
Install any with `/plugin install <name>@claude-plugins-official`; browse the full set in `/plugin` → **Discover**.

> Plugins can also bundle skills, agents, hooks, commands, and LSP servers. A plugin declares its
> MCP servers in a `.mcp.json` at the plugin root (using `${CLAUDE_PLUGIN_ROOT}`), and they appear in
> `/mcp` alongside manually-added servers. **Community marketplace:**
> `/plugin marketplace add anthropics/claude-plugins-community` then `/plugin install <name>@claude-community`.

---

## 2. Remote MCP servers — `claude mcp add` (HTTP / SSE, OAuth)

Vendor-hosted servers added by URL. The services in §1 can also be added this way; below are ones
not (yet) in the official marketplace. All are listed in the [Anthropic Directory](https://claude.ai/directory).

| Server | Official source | Add | Local config |
|--------|-----------------|-----|--------------|
| **Stripe** | [docs.stripe.com/mcp](https://docs.stripe.com/mcp) | `claude mcp add --transport http stripe https://mcp.stripe.com` | [README](mcp-servers/stripe/README.md) |
| **Sentry** | [mcp.sentry.dev](https://mcp.sentry.dev) | `claude mcp add --transport http sentry https://mcp.sentry.dev/mcp` | [README](mcp-servers/sentry/README.md) |
| **Linear** | [linear.app/docs/mcp](https://linear.app/docs/mcp) | `claude mcp add --transport sse linear https://mcp.linear.app/sse` | [README](mcp-servers/linear/README.md) |
| **Notion** | [developers.notion.com](https://developers.notion.com/docs/mcp) | `claude mcp add --transport http notion https://mcp.notion.com/mcp` | [README](mcp-servers/notion/README.md) |
| **Figma** | [developers.figma.com](https://developers.figma.com/docs/figma-mcp-server/) | `claude mcp add --transport http figma https://mcp.figma.com/mcp` | [README](mcp-servers/figma/README.md) |
| **Canva** | [canva.dev](https://www.canva.dev/docs/apps/mcp-server/) | `claude mcp add --transport http canva https://mcp.canva.com/mcp` | [README](mcp-servers/canva/README.md) |
| **Netlify** | [docs.netlify.com](https://docs.netlify.com/welcome/build-with-ai/netlify-mcp-server/) | `claude mcp add --transport http netlify https://mcp.netlify.com/mcp` | [README](mcp-servers/netlify/README.md) |
| **Vercel** | [vercel.com/docs/mcp](https://vercel.com/docs/mcp/vercel-mcp) | `claude mcp add --transport http vercel https://mcp.vercel.com` | [README](mcp-servers/vercel/README.md) |
| **PostHog** | [posthog.com/docs/mcp](https://posthog.com/docs/model-context-protocol) | `claude mcp add --transport http posthog https://mcp.posthog.com/mcp` | [README](mcp-servers/posthog/README.md) |
| **Cloudflare** | [developers.cloudflare.com](https://developers.cloudflare.com/agents/model-context-protocol/) | per-product remote servers (see docs) | [README](mcp-servers/cloudflare/README.md) |
| **Monday.com** | [github.com/mondaycom/mcp](https://github.com/mondaycom/mcp) | `claude mcp add --transport http monday https://mcp.monday.com/mcp` | [README](mcp-servers/monday/README.md) |
| **Atlassian** | [mcp.atlassian.com](https://www.atlassian.com/platform/remote-mcp-server) | `claude mcp add --transport sse atlassian https://mcp.atlassian.com/v1/sse` | [README](mcp-servers/atlassian/README.md) |
| **Context7** | [github.com/upstash/context7](https://github.com/upstash/context7) | `claude mcp add --transport http context7 https://mcp.context7.com/mcp` | [README](mcp-servers/context7/README.md) |

> `--transport http` is the recommended transport; `sse` is supported for servers that publish an
> SSE endpoint. In `.mcp.json` the `type` field accepts `http` (alias `streamable-http`), `sse`, `ws`, and `stdio`.

---

## 3. Local MCP servers — `claude mcp add ... -- npx ...` (stdio)

Run locally over stdio. Each is an actively-maintained GitHub project.

| Server | Official source | Add |
|--------|-----------------|-----|
| **GitHub** (local) | [github/github-mcp-server](https://github.com/github/github-mcp-server) | `claude mcp add --transport http github https://api.githubcopilot.com/mcp/ --header "Authorization: Bearer $GITHUB_PAT"` |
| **Chrome DevTools** | [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | `claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest` |
| **Playwright** | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | `claude mcp add playwright -- npx -y @playwright/mcp@latest` |
| **MongoDB** | [mongodb-js/mongodb-mcp-server](https://github.com/mongodb-js/mongodb-mcp-server) | `claude mcp add mongodb --env MDB_MCP_CONNECTION_STRING=… -- npx -y mongodb-mcp-server` |
| **PostgreSQL** | [crystaldba/postgres-mcp](https://github.com/crystaldba/postgres-mcp) | `claude mcp add postgres --env DATABASE_URI=… -- npx -y @crystaldba/postgres-mcp` |
| **Supabase** (local) | [supabase-community/supabase-mcp](https://github.com/supabase-community/supabase-mcp) | `claude mcp add supabase -- npx -y @supabase/mcp-server-supabase --access-token=…` |
| **AWS** | [awslabs/mcp](https://github.com/awslabs/mcp) | per-server, e.g. `claude mcp add aws-docs -- uvx awslabs.aws-documentation-mcp-server@latest` |
| **Kubernetes** | [Flux159/mcp-server-kubernetes](https://github.com/Flux159/mcp-server-kubernetes) | `claude mcp add kubernetes -- npx -y mcp-server-kubernetes` |
| **Airtable** | [domdomegg/airtable-mcp-server](https://github.com/domdomegg/airtable-mcp-server) | `claude mcp add airtable --env AIRTABLE_API_KEY=… -- npx -y airtable-mcp-server` |
| **Material UI** | [@mui/mcp](https://www.npmjs.com/package/@mui/mcp) | `claude mcp add mui -- npx -y @mui/mcp@latest` |
| **Next.js** | [nextjs.org/docs](https://nextjs.org/docs) | runs from the Next.js dev server — see [config](mcp-servers/nextjs/README.md) |
| **Codex** | [openai/codex](https://github.com/openai/codex) | `claude mcp add codex -- codex mcp` |

Local config snippets, where available, are under [`mcp-servers/`](mcp-servers).

---

## 4. Reference servers — `modelcontextprotocol/servers`

Maintained by the MCP project as canonical examples ([repo](https://github.com/modelcontextprotocol/servers)).

> In **April 2026** this repo retired its long "Official integrations" / third-party list in favor of the
> [official MCP Registry](https://registry.modelcontextprotocol.io) — query that for the canonical,
> machine-readable list of vendor servers. The repo now keeps only the reference servers below.

### Active

| Server | Description | Add |
|--------|-------------|-----|
| **everything** | Reference/test server exercising every MCP feature | `claude mcp add everything -- npx -y @modelcontextprotocol/server-everything` |
| **fetch** | Web content fetching for LLM consumption | `claude mcp add fetch -- uvx mcp-server-fetch` |
| **filesystem** | Secure file operations with access controls | `claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem ~/projects` |
| **git** | Read, search, and manipulate Git repos | `claude mcp add git -- uvx mcp-server-git` |
| **memory** | Knowledge-graph persistent memory | `claude mcp add memory -- npx -y @modelcontextprotocol/server-memory` |
| **sequential-thinking** | Step-by-step structured reasoning | `claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking` |
| **time** | Time & timezone conversion | `claude mcp add time -- uvx mcp-server-time` |

### Archived (moved to [`servers-archived`](https://github.com/modelcontextprotocol/servers-archived), still usable)

| Server | Description |
|--------|-------------|
| **slack** | Slack messaging & channels (prefer the `slack` plugin in §1) |
| **sqlite** | SQLite database access |

---

## 5. More verified servers (by category)

A broad catalog of additional servers beyond §1–§4, each backed by an official vendor source or an
actively-maintained GitHub repo (verified June 2026). `community` marks a non-vendor but maintained
repo. Remote servers use OAuth/API-key (`--transport http`/`sse`); local servers run over stdio via
`npx`/`uvx`. Replace `…`/`<…>` with your own keys, endpoints, or tokens.

### Databases & data

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **Redis** | Redis | [redis/mcp-redis](https://github.com/redis/mcp-redis) | `claude mcp add redis -- uvx --from redis-mcp-server@latest redis-mcp-server --url redis://localhost:6379/0` |
| **Neo4j** | Neo4j | [neo4j-contrib/mcp-neo4j](https://github.com/neo4j-contrib/mcp-neo4j) | `claude mcp add neo4j -- uvx mcp-neo4j-cypher` |
| **ClickHouse** | ClickHouse | [ClickHouse/mcp-clickhouse](https://github.com/ClickHouse/mcp-clickhouse) | `claude mcp add clickhouse --env CLICKHOUSE_HOST=… -- uvx mcp-clickhouse` · Cloud: `claude mcp add --transport http clickhouse https://mcp.clickhouse.cloud/mcp` |
| **Neon** | Neon | [neondatabase/mcp-server-neon](https://github.com/neondatabase/mcp-server-neon) | `claude mcp add --transport http neon https://mcp.neon.tech/mcp` |
| **Prisma Postgres** | Prisma | [prisma/mcp](https://github.com/prisma/mcp) | `claude mcp add --transport http prisma https://mcp.prisma.io/mcp` · local: `claude mcp add prisma -- npx -y prisma mcp` |
| **MotherDuck / DuckDB** | MotherDuck | [motherduckdb/mcp-server-motherduck](https://github.com/motherduckdb/mcp-server-motherduck) | `claude mcp add motherduck --env motherduck_token=… -- uvx mcp-server-motherduck --db-path md:` |
| **Couchbase** | Couchbase | [couchbase/mcp-server-couchbase](https://github.com/couchbase/mcp-server-couchbase) | `claude mcp add couchbase --env CB_CONNECTION_STRING=… -- uvx couchbase-mcp-server` |
| **InfluxDB 3** | InfluxData | [influxdata/influxdb3_mcp_server](https://github.com/influxdata/influxdb3_mcp_server) | `claude mcp add influxdb --env INFLUX_DB_TOKEN=… -- npx -y @influxdata/influxdb3-mcp-server` |
| **BigQuery** | Google | [googleapis/mcp-toolbox](https://github.com/googleapis/genai-toolbox) | `claude mcp add bigquery --env BIGQUERY_PROJECT=… -- npx -y @toolbox-sdk/server --prebuilt bigquery --stdio` |
| **Snowflake** | Snowflake | [docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp) | `claude mcp add --transport http snowflake https://<account>.snowflakecomputing.com/api/v2/.../mcp-servers/<name>` |
| **Databricks** | Databricks | [docs](https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp) | `claude mcp add --transport http databricks https://<workspace>/api/2.0/mcp/genie --header "Authorization: Bearer …"` |
| **Astra DB** | DataStax | [datastax/astra-db-mcp](https://github.com/datastax/astra-db-mcp) | `claude mcp add astra-db --env ASTRA_DB_APPLICATION_TOKEN=… -- npx -y @datastax/astra-db-mcp` |
| **Tinybird** | Tinybird | [docs](https://www.tinybird.co/docs/forward/analytics-agents/mcp) | `claude mcp add --transport http tinybird "https://mcp.tinybird.co?token=…"` |
| **TimescaleDB** | TigerData | [timescale/tiger-cli](https://github.com/timescale/tiger-cli) | install Tiger CLI, then `tiger mcp install claude-code` |

> Notes: **Elasticsearch** ([elastic/mcp-server-elasticsearch](https://github.com/elastic/mcp-server-elasticsearch)) is in maintenance/security-fix mode — Elastic now ships an Agent Builder MCP endpoint inside the cluster (9.2+). **Weaviate** is now embedded in the database (`/v1/mcp`), no standalone server. Generic Apache **Cassandra** has no official server — use DataStax Astra or AWS Keyspaces.

### Search & vector

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **Qdrant** | Qdrant | [qdrant/mcp-server-qdrant](https://github.com/qdrant/mcp-server-qdrant) | `claude mcp add qdrant --env QDRANT_URL=… -- uvx mcp-server-qdrant` |
| **Pinecone** | Pinecone | [pinecone-io/pinecone-mcp](https://github.com/pinecone-io/pinecone-mcp) | `claude mcp add pinecone --env PINECONE_API_KEY=… -- npx -y @pinecone-database/mcp` |
| **Chroma** | Chroma | [chroma-core/chroma-mcp](https://github.com/chroma-core/chroma-mcp) | `claude mcp add chroma -- uvx chroma-mcp` |
| **Zilliz / Milvus** | Zilliz | [zilliztech/zilliz-mcp-server](https://github.com/zilliztech/zilliz-mcp-server) | `claude mcp add zilliz --env ZILLIZ_CLOUD_TOKEN=… -- uvx zilliz-mcp-server` |
| **Meilisearch** | Meilisearch | [meilisearch/meilisearch-mcp](https://github.com/meilisearch/meilisearch-mcp) | `claude mcp add meilisearch -- uvx meilisearch-mcp` |
| **Algolia** | Algolia | [algolia/mcp](https://github.com/algolia/mcp) | Go binary — build from repo, then `claude mcp add algolia -- /path/to/mcp` |
| **Typesense** | community | [suhail-ak-2/mcp-typesense-server](https://github.com/suhail-ak-2/mcp-typesense-server) | `claude mcp add typesense -- npx -y typesense-mcp-server` |

### Cloud & deployment

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **Azure** | Microsoft | [microsoft/mcp](https://github.com/microsoft/mcp) | `claude mcp add azure -- npx -y @azure/mcp@latest server start` |
| **Azure DevOps** | Microsoft | [microsoft/azure-devops-mcp](https://github.com/microsoft/azure-devops-mcp) | `claude mcp add azure-devops -- npx -y @azure-devops/mcp <org>` |
| **Heroku** | Heroku | [heroku/heroku-mcp-server](https://github.com/heroku/heroku-mcp-server) | `claude mcp add heroku -- npx -y @heroku/mcp-server` |
| **DigitalOcean** | DigitalOcean | [digitalocean-labs/mcp-digitalocean](https://github.com/digitalocean-labs/mcp-digitalocean) | `claude mcp add digitalocean --env DIGITALOCEAN_API_TOKEN=… -- npx -y @digitalocean/mcp` |
| **Railway** | Railway | [docs](https://docs.railway.com/ai/mcp-server) | `claude mcp add --transport http railway https://mcp.railway.com` |
| **Render** | Render | [render-oss/render-mcp-server](https://github.com/render-oss/render-mcp-server) | `claude mcp add --transport http render https://mcp.render.com/mcp --header "Authorization: Bearer …"` |
| **Fly.io** | Fly.io | [docs](https://fly.io/docs/flyctl/mcp-server/) | ships in flyctl — `fly mcp server --claude` |

### DevOps, CI/CD & IaC

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **Terraform** | HashiCorp | [hashicorp/terraform-mcp-server](https://github.com/hashicorp/terraform-mcp-server) | `claude mcp add terraform -- docker run -i --rm hashicorp/terraform-mcp-server` |
| **Pulumi** | Pulumi | [docs](https://www.pulumi.com/docs/ai/mcp-server/) | `claude mcp add --transport http pulumi https://mcp.ai.pulumi.com/mcp` |
| **Docker** | Docker | [docker/mcp-gateway](https://github.com/docker/mcp-gateway) | `claude mcp add docker -- docker mcp gateway run` |
| **Ansible** | Ansible | [ansible/vscode-ansible](https://github.com/ansible/vscode-ansible) | `claude mcp add ansible -- npx -y @ansible/ansible-mcp-server --stdio` |
| **CircleCI** | CircleCI | [CircleCI-Public/mcp-server-circleci](https://github.com/CircleCI-Public/mcp-server-circleci) | `claude mcp add circleci --env CIRCLECI_TOKEN=… -- npx -y @circleci/mcp-server-circleci@latest` |
| **Buildkite** | Buildkite | [buildkite/buildkite-mcp-server](https://github.com/buildkite/buildkite-mcp-server) | `claude mcp add --transport http buildkite https://mcp.buildkite.com/mcp` |
| **Snyk** | Snyk | [docs](https://docs.snyk.io) | ships in Snyk CLI — `claude mcp add snyk -- snyk mcp -t stdio` |
| **JetBrains** | JetBrains | [JetBrains/mcp-jetbrains](https://github.com/JetBrains/mcp-jetbrains) | `claude mcp add jetbrains -- npx -y @jetbrains/mcp-proxy` |
| **Microsoft Learn** | Microsoft | [MicrosoftDocs/mcp](https://github.com/MicrosoftDocs/mcp) | `claude mcp add --transport http microsoft-learn https://learn.microsoft.com/api/mcp` |

### Observability & monitoring

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **Datadog** | Datadog | [datadog-labs/mcp-server](https://github.com/datadog-labs/mcp-server) | `claude mcp add --transport http datadog https://mcp.datadoghq.com/api/unstable/mcp-server/mcp` |
| **New Relic** | New Relic | [newrelic/mcp-server](https://github.com/newrelic/mcp-server) | `claude mcp add --transport http newrelic https://mcp.newrelic.com/mcp/` |
| **Grafana** | Grafana Labs | [grafana/mcp-grafana](https://github.com/grafana/mcp-grafana) | `claude mcp add grafana -- uvx mcp-grafana` |
| **Honeycomb** | Honeycomb | [docs](https://docs.honeycomb.io/integrations/mcp/) | `claude mcp add --transport http honeycomb https://mcp.honeycomb.io/mcp` |
| **Axiom** | Axiom | [axiomhq/mcp](https://github.com/axiomhq/mcp) | `claude mcp add --transport http axiom https://mcp.axiom.co/mcp` |
| **PagerDuty** | PagerDuty | [PagerDuty/pagerduty-mcp-server](https://github.com/PagerDuty/pagerduty-mcp-server) | `claude mcp add pagerduty -- uvx pagerduty-mcp` |
| **Raygun** | Raygun | [MindscapeHQ/mcp-server-raygun](https://github.com/MindscapeHQ/mcp-server-raygun) | `claude mcp add --transport http raygun https://api.raygun.com/v3/mcp --header "Authorization: Bearer …"` |
| **Prometheus** | community | [pab1it0/prometheus-mcp-server](https://github.com/pab1it0/prometheus-mcp-server) | `claude mcp add prometheus -- uvx prometheus-mcp-server` |

### Payments & fintech

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **PayPal** | PayPal | [paypal/agent-toolkit](https://github.com/paypal/agent-toolkit) | `claude mcp add --transport http paypal https://mcp.paypal.com/mcp` · local: `npx -y @paypal/mcp --tools=all` |
| **Square** | Block | [square/square-mcp-server](https://github.com/square/square-mcp-server) | `claude mcp add --transport sse square https://mcp.squareup.com/sse` |
| **Plaid** | Plaid | [plaid/ai-coding-toolkit](https://github.com/plaid/ai-coding-toolkit) | `claude mcp add --transport http plaid https://api.dashboard.plaid.com/mcp/` |
| **Adyen** | Adyen | [Adyen/adyen-mcp](https://github.com/Adyen/adyen-mcp) | `claude mcp add adyen -- npx -y @adyen/mcp --adyenApiKey=… --env=TEST` |

### CRM, support & sales

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **HubSpot** | HubSpot | [docs](https://developers.hubspot.com/mcp) | `claude mcp add --transport http hubspot https://mcp.hubspot.com/anthropic` |
| **Salesforce** | Salesforce | [salesforcecli/mcp](https://github.com/salesforcecli/mcp) | `claude mcp add salesforce -- npx -y @salesforce/mcp --orgs DEFAULT_TARGET_ORG --toolsets all` |
| **Intercom** | Intercom | [docs](https://developers.intercom.com/docs/guides/mcp) | `claude mcp add --transport http intercom https://mcp.intercom.com/mcp` |
| **ClickUp** | ClickUp | [docs](https://developer.clickup.com/docs/connect-an-ai-assistant-to-clickups-mcp-server) | `claude mcp add --transport http clickup https://mcp.clickup.com/mcp` |
| **Freshdesk** | community | [effytech/freshdesk_mcp](https://github.com/effytech/freshdesk_mcp) | `claude mcp add freshdesk --env FRESHDESK_API_KEY=… -- uvx freshdesk-mcp` |

### E-commerce & CMS

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **Shopify (Dev)** | Shopify | [shopify.dev](https://shopify.dev/docs/apps/build/devmcp) | `claude mcp add shopify-dev -- npx -y @shopify/dev-mcp@latest` |
| **Shopify (Storefront)** | Shopify | [shopify.dev](https://shopify.dev/docs/apps/build/storefront-mcp/servers/storefront) | `claude mcp add --transport http shopify-storefront https://{shop}.myshopify.com/api/mcp` |
| **BigCommerce** | BigCommerce | [docs](https://docs.bigcommerce.com/developer/api-reference/mcp/overview) | `claude mcp add --transport http bigcommerce <your-store-mcp-url>` |
| **WooCommerce** | Automattic | [docs](https://developer.woocommerce.com/docs/features/mcp/) | self-hosted: `https://yourstore.com/wp-json/woocommerce/mcp` |
| **commercetools** | commercetools | [commercetools/commerce-mcp](https://github.com/commercetools/commerce-mcp) | `claude mcp add commercetools -- npx -y @commercetools/commerce-mcp --tools=all --clientId=… --clientSecret=… --projectKey=…` |
| **Shopware** | Shopware | [shopware/shopware-admin-mcp](https://github.com/shopware/shopware-admin-mcp) | `claude mcp add shopware -- npx -y @shopware-ag/admin-mcp` |
| **Webflow** | Webflow | [webflow/mcp-server](https://github.com/webflow/mcp-server) | `claude mcp add --transport http webflow https://mcp.webflow.com/mcp` |
| **Wix** | Wix | [wix/wix-mcp](https://github.com/wix/wix-mcp) | `claude mcp add --transport http wix https://mcp.wix.com/mcp` |
| **Contentful** | Contentful | [contentful/contentful-mcp-server](https://github.com/contentful/contentful-mcp-server) | `claude mcp add --transport http contentful https://mcp.contentful.com/mcp` |
| **Sanity** | Sanity | [docs](https://www.sanity.io/docs/ai/mcp-server) | `claude mcp add --transport http sanity https://mcp.sanity.io/developer` |
| **Storyblok** | Storyblok | [docs](https://www.storyblok.com/docs) | `claude mcp add --transport http storyblok https://mcp.labs.storyblok.com/mcp` |

### Productivity, docs & storage

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **Asana** | Asana | [docs](https://developers.asana.com/docs/using-asanas-mcp-server) | `claude mcp add --transport http asana https://mcp.asana.com/v2/mcp` (also a §1 plugin) |
| **Box** | Box | [docs](https://developer.box.com/guides/box-mcp/) | `claude mcp add --transport http box https://mcp.box.com` |
| **Dropbox** | Dropbox | [docs](https://help.dropbox.com/integrations/connect-dropbox-mcp-server) | `claude mcp add --transport http dropbox https://mcp.dropbox.com/mcp` |
| **DocuSign** | Docusign | [docs](https://developers.docusign.com/platform/mcp-server/) | `claude mcp add --transport http docusign https://mcp.docusign.com/mcp` |

### Communication & automation

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **Twilio** | Twilio Labs | [twilio-labs/mcp](https://github.com/twilio-labs/mcp) | `claude mcp add twilio -- npx -y @twilio-alpha/mcp <SID>/<KEY>:<SECRET>` |
| **Resend** | Resend | [resend/resend-mcp](https://github.com/resend/resend-mcp) | `claude mcp add resend --env RESEND_API_KEY=… -- npx -y resend-mcp` |
| **Mailchimp (Transactional)** | Mailchimp | [docs](https://mailchimp.com/developer/transactional/guides/how-to-use-mailchimps-transactional-messaging-mcp/) | `claude mcp add --transport http mailchimp https://mandrillapp.com/mcp --header "Authorization: Bearer …"` |
| **Zapier** | Zapier | [docs](https://docs.zapier.com/mcp/home) | `claude mcp add --transport http zapier https://mcp.zapier.com/api/v1/mcp --header "Authorization: Bearer …"` |
| **Make** | Make | [integromat/make-mcp-server](https://github.com/integromat/make-mcp-server) | `claude mcp add --transport http make "https://<zone>/mcp/u/<token>/mcp"` |

### Web search & scraping

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **Exa** | Exa Labs | [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server) | `claude mcp add --transport http exa https://mcp.exa.ai/mcp` |
| **Tavily** | Tavily | [tavily-ai/tavily-mcp](https://github.com/tavily-ai/tavily-mcp) | `claude mcp add --transport http tavily "https://mcp.tavily.com/mcp/?tavilyApiKey=…"` |
| **Firecrawl** | Firecrawl | [firecrawl/firecrawl-mcp-server](https://github.com/firecrawl/firecrawl-mcp-server) | `claude mcp add firecrawl --env FIRECRAWL_API_KEY=… -- npx -y firecrawl-mcp` |
| **Brave Search** | Brave | [brave/brave-search-mcp-server](https://github.com/brave/brave-search-mcp-server) | `claude mcp add brave-search --env BRAVE_API_KEY=… -- npx -y @brave/brave-search-mcp-server` |
| **Perplexity** | Perplexity | [perplexityai/modelcontextprotocol](https://github.com/perplexityai/modelcontextprotocol) | `claude mcp add perplexity --env PERPLEXITY_API_KEY=… -- npx -y @perplexity-ai/mcp-server` |
| **Kagi** | Kagi | [kagisearch/kagimcp](https://github.com/kagisearch/kagimcp) | `claude mcp add kagi --env KAGI_API_KEY=… -- uvx kagimcp` |
| **Jina AI** | Jina AI | [jina-ai/MCP](https://github.com/jina-ai/MCP) | `claude mcp add --transport http jina https://mcp.jina.ai/v1 --header "Authorization: Bearer …"` |
| **Apify** | Apify | [apify/apify-mcp-server](https://github.com/apify/apify-mcp-server) | `claude mcp add --transport http apify https://mcp.apify.com` |

### AI, browser & developer tools

| Server | Maintainer | Source | Install |
|--------|------------|--------|---------|
| **Hugging Face** | Hugging Face | [huggingface/hf-mcp-server](https://github.com/huggingface/hf-mcp-server) | `claude mcp add --transport http huggingface https://huggingface.co/mcp --header "Authorization: Bearer …"` |
| **Replicate** | Replicate | [docs](https://replicate.com/docs/reference/mcp) | `claude mcp add --transport sse replicate https://mcp.replicate.com/sse` |
| **Browserbase / Stagehand** | Browserbase | [browserbase/mcp-server-browserbase](https://github.com/browserbase/mcp-server-browserbase) | `claude mcp add browserbase --env BROWSERBASE_API_KEY=… -- npx -y @browserbasehq/mcp` |
| **Postman** | Postman | [postmanlabs/postman-mcp-server](https://github.com/postmanlabs/postman-mcp-server) | `claude mcp add --transport http postman https://mcp.postman.com/mcp` |
| **Apidog** | Apidog | [docs](https://docs.apidog.com/apidog-mcp-server) | `claude mcp add apidog --env APIDOG_ACCESS_TOKEN=… -- npx -y apidog-mcp-server@latest` |
| **AntV Chart** | Ant Group | [antvis/mcp-server-chart](https://github.com/antvis/mcp-server-chart) | `claude mcp add antv-chart -- npx -y @antv/mcp-server-chart` |
| **Octagon** | Octagon AI | [OctagonAI/octagon-mcp-server](https://github.com/OctagonAI/octagon-mcp-server) | `claude mcp add --transport http octagon https://mcp.octagonai.co/mcp` |
| **Wikipedia** | community | [Rudra-ravi/wikipedia-mcp](https://github.com/Rudra-ravi/wikipedia-mcp) | `claude mcp add wikipedia -- uvx wikipedia-mcp` |
| **arXiv** | community | [blazickjp/arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server) | `claude mcp add arxiv -- uvx arxiv-mcp-server` |
| **Google Maps** | community | [cablate/mcp-google-map](https://github.com/cablate/mcp-google-map) | `claude mcp add google-maps --env GOOGLE_MAPS_API_KEY=… -- npx -y @cablate/mcp-google-map` |

> Remote endpoints for hosted/per-tenant servers (Snowflake, Databricks, Shopify Storefront,
> BigCommerce, WooCommerce, Zapier, Make) are account/store-specific — substitute your own host and
> token. Verify package names on first install; vendors occasionally rename or move repos.

---

## 6. Official SDKs (build your own server)

Local snippets: [`mcp-servers/sdk-references`](mcp-servers/sdk-references).

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

---

## Command cheatsheet

```bash
# Plugins (one-click integrations)
/plugin install github@claude-plugins-official       # install from official marketplace
/plugin marketplace add anthropics/claude-plugins-community
/plugin list                                         # manage installed plugins
/reload-plugins                                       # apply changes without restart

# Remote servers (HTTP/SSE + OAuth)
claude mcp add --transport http stripe https://mcp.stripe.com
claude mcp add --transport sse  linear https://mcp.linear.app/sse
/mcp                                                  # authenticate / inspect servers
claude mcp login <name>                               # OAuth from the shell

# Local servers (stdio)
claude mcp add memory -- npx -y @modelcontextprotocol/server-memory
claude mcp add --scope project filesystem -- npx -y @modelcontextprotocol/server-filesystem .

# JSON config (e.g. WebSocket)
claude mcp add-json events '{"type":"ws","url":"wss://mcp.example.com/socket"}'

# Manage
claude mcp list
claude mcp get <name>
claude mcp remove <name>
```
