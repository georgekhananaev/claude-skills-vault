# Slack MCP Server

Channel management and messaging capabilities for Slack workspaces.

## Source

- **npm**: [@modelcontextprotocol/server-slack](https://www.npmjs.com/package/@modelcontextprotocol/server-slack)
- **GitHub**: [modelcontextprotocol/servers-archived/src/slack](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/slack)
- **Status**: Archived (still functional, no longer actively maintained)

## Quick Install

```bash
claude mcp add slack -s user -- npx -y @modelcontextprotocol/server-slack
```

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `SLACK_BOT_TOKEN` | Bot OAuth token (xoxb-...) | Yes |
| `SLACK_TEAM_ID` | Workspace team ID | Yes |

### Getting Credentials

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Create new app or select existing
3. OAuth & Permissions → Install to Workspace
4. Copy Bot User OAuth Token
5. Get Team ID from workspace settings

### Required Bot Scopes

- `channels:history`, `channels:read`
- `chat:write`
- `groups:history`, `groups:read`
- `mpim:history`, `mpim:read`
- `im:history`, `im:read`
- `users:read`
- `reactions:write`

## Claude Code Config

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token",
        "SLACK_TEAM_ID": "T01234567"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `slack_list_channels` | List public channels |
| `slack_post_message` | Post message to channel |
| `slack_reply_to_thread` | Reply in a thread |
| `slack_add_reaction` | Add emoji reaction |
| `slack_get_channel_history` | Get channel messages |
| `slack_get_thread_replies` | Get thread replies |
| `slack_get_users` | List workspace users |
| `slack_get_user_profile` | Get user profile |

## Usage

```
User: List all channels
Claude: [Uses slack_list_channels tool]

User: Post "Hello team!" to #general
Claude: [Uses slack_post_message tool]

User: What was discussed in #engineering today?
Claude: [Uses slack_get_channel_history tool]
```

## License

MIT - [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
