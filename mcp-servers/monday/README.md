# Monday.com MCP Server

AI agent integration with the monday.com work operating system.

## Source

- **Documentation**: [developer.monday.com/apps/docs/mondaycom-mcp-integration](https://developer.monday.com/apps/docs/mondaycom-mcp-integration)
- **Landing Page**: [monday.com/w/mcp](https://monday.com/w/mcp)
- **GitHub**: [mondaycom/mcp](https://github.com/mondaycom/mcp)
- **npm**: [@mondaydotcomorg/monday-api-mcp](https://www.npmjs.com/package/@mondaydotcomorg/monday-api-mcp)
- **Marketplace**: [monday MCP app](https://auth.monday.com/marketplace/listing/10000806/monday-mcp)
- **Hosted MCP**: `https://mcp.monday.com/mcp`
- **Maintainer**: Monday.com

## Quick Install

```bash
# Hosted (OAuth - recommended)
claude mcp add monday --transport http https://mcp.monday.com/mcp

# Local with API token
claude mcp add monday -s user -- npx -y @mondaydotcomorg/monday-api-mcp@latest -t YOUR_API_TOKEN
```

## Features

- **Item Operations**: Create, update, delete, search items
- **Board Management**: Create boards, manage columns and groups
- **User Management**: List users and teams
- **WorkForms**: Form operations
- **Dynamic API**: Custom GraphQL queries (beta)
- **Read-Only Mode**: Safe exploration without modifications

## Configuration

### Hosted MCP (OAuth)

```json
{
  "mcpServers": {
    "monday": {
      "type": "http",
      "url": "https://mcp.monday.com/mcp"
    }
  }
}
```

### Local with API Token

```json
{
  "mcpServers": {
    "monday": {
      "command": "npx",
      "args": [
        "-y",
        "@mondaydotcomorg/monday-api-mcp@latest",
        "-t",
        "YOUR_API_TOKEN"
      ]
    }
  }
}
```

### Read-Only Mode

```json
{
  "mcpServers": {
    "monday": {
      "command": "npx",
      "args": [
        "-y",
        "@mondaydotcomorg/monday-api-mcp@latest",
        "-t",
        "YOUR_API_TOKEN",
        "--read-only"
      ]
    }
  }
}
```

## Tools

### Item Operations

| Tool | Description |
|------|-------------|
| `create_item` | Create new item on a board |
| `delete_item` | Delete an item |
| `get_board_items_by_name` | Search items by name |
| `create_update` | Add update/comment to item |
| `change_item_column_values` | Update item column values |
| `move_item_to_group` | Move item to different group |

### Board Operations

| Tool | Description |
|------|-------------|
| `create_board` | Create new board |
| `get_board_schema` | Get board structure and columns |
| `create_group` | Create new group on board |
| `create_column` | Add column to board |
| `delete_column` | Remove column from board |

### Account

| Tool | Description |
|------|-------------|
| `list_users_and_teams` | List all users and teams |

### Dynamic API (Beta)

| Tool | Description |
|------|-------------|
| `all_monday_api` | Execute custom GraphQL queries |
| `get_graphql_schema` | Get API schema |
| `get_type_details` | Get type definitions |

Enable with `--enable-dynamic-api-tools` flag.

## CLI Options

| Option | Description |
|--------|-------------|
| `-t, --token` | Monday.com API token |
| `-v, --version` | API version |
| `-m, --mode` | Tool mode (default/apps) |
| `-ro, --read-only` | Enable read-only mode |
| `-edat, --enable-dynamic-api-tools` | Enable dynamic API tools |

## Usage Examples

```
User: Show my Monday.com boards
Claude: [Uses get_board_schema tool]

User: Create a task "Review PR" on the Dev board
Claude: [Uses create_item tool]

User: Move task to Done group
Claude: [Uses move_item_to_group tool]

User: Add a comment to the task
Claude: [Uses create_update tool]

User: List all team members
Claude: [Uses list_users_and_teams tool]
```

## Prerequisites

- Node.js v20+
- Monday.com API token (for local) or OAuth (for hosted)

## Getting API Token

1. Go to monday.com
2. Click profile picture → Developers
3. My Access Tokens → Show/Generate

## License

MIT - [Monday.com](https://github.com/mondaycom/mcp)
