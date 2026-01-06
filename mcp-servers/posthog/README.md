# PostHog MCP Server

Product analytics and observability platform integration.

## Source

- **Official URL**: [mcp.posthog.com](https://mcp.posthog.com)
- **Documentation**: [PostHog Docs](https://posthog.com/docs)
- **Maintainer**: PostHog

## Quick Install

```bash
claude mcp add posthog --transport sse https://mcp.posthog.com/sse
```

## Features

- **Product Analytics**: Track user behavior and events
- **Feature Flags**: Manage feature flags
- **Session Replay**: Access session recordings
- **A/B Testing**: Manage experiments

## Configuration

```json
{
  "mcpServers": {
    "posthog": {
      "type": "sse",
      "url": "https://mcp.posthog.com/sse"
    }
  }
}
```

## Usage Examples

```
User: Show user engagement metrics
Claude: [Uses PostHog MCP to query analytics]

User: What are the top events this week?
Claude: [Uses PostHog MCP to list events]

User: Check the status of feature flag new-checkout
Claude: [Uses PostHog MCP to check flag]

User: How is the A/B test performing?
Claude: [Uses PostHog MCP to analyze experiment]
```

## Authentication

Authenticates via PostHog's OAuth flow on first use.

## License

Proprietary - PostHog
