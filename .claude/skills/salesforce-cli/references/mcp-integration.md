# Salesforce MCP Server Integration

Setup, configuration, and usage patterns for Salesforce MCP servers.

## Official: Salesforce DX MCP Server

The official MCP server from the Salesforce CLI team.

### Installation

Add to `.mcp.json` or Claude Code MCP config:

```json
{
  "mcpServers": {
    "salesforce-dx": {
      "command": "npx",
      "args": ["-y", "@salesforce/mcp", "--orgs", "DEFAULT_TARGET_ORG"]
    }
  }
}
```

**Multiple orgs:**

```json
{
  "mcpServers": {
    "salesforce-dx": {
      "command": "npx",
      "args": ["-y", "@salesforce/mcp", "--orgs", "dev-org,staging-org,prod-org"]
    }
  }
}
```

### Prerequisites

- Node.js 18+
- Orgs must be pre-authorized: `sf org login web --alias <name>`
- The MCP server uses existing CLI auth — no separate credentials needed

### Available Toolsets

Enable specific toolsets with `--toolsets`:

```json
{
  "args": ["-y", "@salesforce/mcp", "--orgs", "my-org", "--toolsets", "Orgs,Data,Metadata,Testing"]
}
```

| Toolset | Tools | Description |
|---------|-------|-------------|
| **Core** | `get_username`, `resume_tool_operation` | Always enabled |
| **Orgs** | `list_all_orgs`, `create_scratch_org`, `create_org_snapshot`, `delete_org`, `open_org` | Org lifecycle |
| **Data** | `run_soql_query` | SOQL queries |
| **Users** | `assign_permission_set` | Permission management |
| **Metadata** | `deploy_metadata`, `retrieve_metadata` | Deploy/retrieve |
| **Testing** | `run_apex_test`, `run_agent_test` | Test execution |
| **Code-Analysis** | `run_code_analyzer`, `describe_code_analyzer_rule` | Static analysis |
| **LWC** | Component dev, testing, accessibility, SLDS2 migration | Lightning Web Components |
| **Aura** | Blueprint, migration, enhancement | Aura components |
| **All** | Everything (60+ tools) | Full access |

### Dynamic Tool Discovery

Use `--dynamic-tools` to start with minimal tools and load others on demand:

```json
{
  "args": ["-y", "@salesforce/mcp", "--orgs", "my-org", "--dynamic-tools"]
}
```

---

## Community: tsmztech/mcp-server-salesforce

### Installation

```json
{
  "mcpServers": {
    "salesforce": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-salesforce"],
      "env": {
        "SALESFORCE_INSTANCE_URL": "https://your-instance.my.salesforce.com",
        "SALESFORCE_ACCESS_TOKEN": "<token>"
      }
    }
  }
}
```

Or with username/password:

```json
{
  "env": {
    "SALESFORCE_INSTANCE_URL": "https://login.salesforce.com",
    "SALESFORCE_USERNAME": "user@example.com",
    "SALESFORCE_PASSWORD": "password",
    "SALESFORCE_TOKEN": "security-token"
  }
}
```

### Available Tools (16)

| Tool | Description | Safety |
|------|-------------|--------|
| `salesforce_search_objects` | Search standard/custom objects | Safe |
| `salesforce_describe_object` | Get object schema (fields, relationships) | Safe |
| `salesforce_query_records` | SOQL queries | Safe |
| `salesforce_aggregate_query` | GROUP BY / aggregate | Safe |
| `salesforce_search_all` | SOSL search | Safe |
| `salesforce_read_apex` | Read Apex class source | Safe |
| `salesforce_read_apex_trigger` | Read trigger source | Safe |
| `salesforce_dml_records` | Insert, update, delete, upsert | Write/Destructive |
| `salesforce_manage_object` | Create/modify custom objects | Write |
| `salesforce_manage_field` | Add/modify custom fields | Write |
| `salesforce_manage_field_permissions` | Field-level security | Write |
| `salesforce_write_apex` | Create/update Apex classes | Destructive |
| `salesforce_write_apex_trigger` | Create/update triggers | Destructive |
| `salesforce_execute_anonymous` | Run anonymous Apex | Destructive |
| `salesforce_manage_debug_logs` | Enable debug logs | Write |

---

## Community: advancedcommunities/salesforce-mcp-server

### Installation

```json
{
  "mcpServers": {
    "salesforce-adv": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-salesforce-advanced"],
      "env": {
        "SF_CLI_PATH": "/usr/local/bin/sf"
      }
    }
  }
}
```

### Key Features (36 tools)

- List/describe objects, query/export records (CSV/JSON)
- Execute Apex, run tests, get code coverage
- Get/list Apex logs
- Run code analyzer
- Safety controls via `READ_ONLY` and `ALLOWED_ORGS` env vars

### Safety Configuration

```json
{
  "env": {
    "READ_ONLY": "true",
    "ALLOWED_ORGS": "dev-org,staging-org"
  }
}
```

---

## Tool Detection Flow

When handling Salesforce operations, detect available tools in this order:

```
1. ToolSearch "salesforce" → Check for MCP tools
   → Found: Use MCP tools (structured input/output, validation)

2. Check `sf` CLI availability
   → which sf → Found: Use sf CLI commands

3. Neither available
   → Guide user: "Install Salesforce CLI: npm install -g @salesforce/cli"
   → Or: "Set up Salesforce MCP server in .mcp.json"
```

### MCP vs CLI Decision Matrix

| Scenario | Prefer |
|----------|--------|
| Single SOQL query | MCP (`run_soql_query`) or CLI (`sf data query`) |
| Bulk data operations | CLI (`sf data import/export bulk`) |
| Metadata deploy/retrieve | Either — MCP has validation built in |
| Schema inspection | MCP (`describe_object`) — more structured output |
| Code analysis | MCP (`run_code_analyzer`) — integrated rules |
| Complex pipelines | CLI — more flexible piping and scripting |
| Headless/CI environments | CLI — no MCP server needed |

---

## Security Considerations

### Auth Token Handling

- MCP servers inherit CLI auth — tokens are managed by `sf`
- Never expose tokens in MCP server config if using env vars
- Use `.env` files (not committed to git) for sensitive config
- The official server uses `--orgs` flag to restrict which orgs are accessible

### Read-Only Mode

For safety, configure MCP servers in read-only mode when possible:

```json
{
  "env": {
    "READ_ONLY": "true"
  }
}
```

### Org Restrictions

Limit which orgs the MCP server can access:

```json
{
  "args": ["-y", "@salesforce/mcp", "--orgs", "dev-only-org"]
}
```

This prevents accidental operations on production through the MCP server.
