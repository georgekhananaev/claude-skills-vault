# Jira Bridge MCP Server

A Model Context Protocol (MCP) server that provides Claude with access to Jira for issue management, project tracking, and workflow automation.

## Features

- **Issue Management**: Create, read, update issues
- **Search & Query**: JQL queries for finding issues
- **Sprint Management**: View sprint details and boards
- **Workflow Operations**: Transition issues through workflows
- **Comments & Attachments**: Add comments and view issue history
- **Project Information**: Access project details and configurations

## Installation

```bash
cd mcp-servers/jira-bridge
npm install
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
# Jira Cloud
JIRA_HOST=your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token

# OR Jira Server/Data Center
JIRA_HOST=jira.yourcompany.com
JIRA_PERSONAL_ACCESS_TOKEN=your-pat
JIRA_USE_PAT=true

# Optional
JIRA_DEFAULT_PROJECT=PROJ
```

### Getting API Credentials

#### Jira Cloud
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Use your email and API token for authentication

#### Jira Server/Data Center
1. Go to Profile > Personal Access Tokens
2. Create a new token with appropriate permissions

### Claude Code Configuration

Add to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "jira": {
      "command": "node",
      "args": ["/path/to/jira-bridge/dist/index.js"],
      "env": {
        "JIRA_HOST": "your-domain.atlassian.net",
        "JIRA_EMAIL": "your-email@company.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

## Available Tools

### `get_issue`
Get details of a specific issue.

```typescript
{
  name: "get_issue",
  description: "Get issue details by key",
  inputSchema: {
    type: "object",
    properties: {
      issueKey: { type: "string", description: "Issue key (e.g., PROJ-123)" }
    },
    required: ["issueKey"]
  }
}
```

### `search_issues`
Search for issues using JQL.

```typescript
{
  name: "search_issues",
  description: "Search issues using JQL",
  inputSchema: {
    type: "object",
    properties: {
      jql: { type: "string", description: "JQL query" },
      maxResults: { type: "number", default: 50 },
      fields: { type: "array", items: { type: "string" } }
    },
    required: ["jql"]
  }
}
```

### `create_issue`
Create a new issue.

```typescript
{
  name: "create_issue",
  description: "Create a new issue",
  inputSchema: {
    type: "object",
    properties: {
      project: { type: "string", description: "Project key" },
      issueType: { type: "string", description: "Issue type (Bug, Task, Story, etc.)" },
      summary: { type: "string", description: "Issue title" },
      description: { type: "string", description: "Issue description" },
      priority: { type: "string", description: "Priority (Highest, High, Medium, Low, Lowest)" },
      labels: { type: "array", items: { type: "string" } },
      assignee: { type: "string", description: "Assignee account ID or email" }
    },
    required: ["project", "issueType", "summary"]
  }
}
```

### `update_issue`
Update an existing issue.

```typescript
{
  name: "update_issue",
  description: "Update an issue",
  inputSchema: {
    type: "object",
    properties: {
      issueKey: { type: "string" },
      summary: { type: "string" },
      description: { type: "string" },
      priority: { type: "string" },
      labels: { type: "array", items: { type: "string" } },
      assignee: { type: "string" }
    },
    required: ["issueKey"]
  }
}
```

### `transition_issue`
Transition an issue to a new status.

```typescript
{
  name: "transition_issue",
  description: "Transition issue to new status",
  inputSchema: {
    type: "object",
    properties: {
      issueKey: { type: "string" },
      transition: { type: "string", description: "Transition name or ID" }
    },
    required: ["issueKey", "transition"]
  }
}
```

### `add_comment`
Add a comment to an issue.

```typescript
{
  name: "add_comment",
  description: "Add a comment to an issue",
  inputSchema: {
    type: "object",
    properties: {
      issueKey: { type: "string" },
      body: { type: "string", description: "Comment text (supports Jira markdown)" }
    },
    required: ["issueKey", "body"]
  }
}
```

### `get_transitions`
Get available transitions for an issue.

```typescript
{
  name: "get_transitions",
  description: "Get available workflow transitions",
  inputSchema: {
    type: "object",
    properties: {
      issueKey: { type: "string" }
    },
    required: ["issueKey"]
  }
}
```

### `get_project`
Get project details.

```typescript
{
  name: "get_project",
  description: "Get project information",
  inputSchema: {
    type: "object",
    properties: {
      projectKey: { type: "string" }
    },
    required: ["projectKey"]
  }
}
```

### `get_sprint`
Get current sprint for a board.

```typescript
{
  name: "get_sprint",
  description: "Get active sprint for a board",
  inputSchema: {
    type: "object",
    properties: {
      boardId: { type: "number" },
      state: { type: "string", enum: ["active", "future", "closed"] }
    },
    required: ["boardId"]
  }
}
```

### `assign_issue`
Assign an issue to a user.

```typescript
{
  name: "assign_issue",
  description: "Assign issue to a user",
  inputSchema: {
    type: "object",
    properties: {
      issueKey: { type: "string" },
      assignee: { type: "string", description: "Account ID, email, or 'unassigned'" }
    },
    required: ["issueKey", "assignee"]
  }
}
```

## Usage Examples

### With Claude Code

```
User: What's the status of PROJ-123?
Claude: [Uses get_issue tool]

User: Find all open bugs assigned to me
Claude: [Uses search_issues with JQL: "assignee = currentUser() AND type = Bug AND status != Done"]

User: Create a bug for the login issue
Claude: [Uses create_issue tool]

User: Move PROJ-456 to In Progress
Claude: [Uses transition_issue tool]

User: What can I do with PROJ-789?
Claude: [Uses get_transitions to show available workflow actions]
```

### Common JQL Queries

```jql
# My open issues
assignee = currentUser() AND resolution = Unresolved

# Sprint issues
sprint in openSprints() AND project = PROJ

# Recent bugs
type = Bug AND created >= -7d ORDER BY created DESC

# Unassigned high priority
priority in (High, Highest) AND assignee is EMPTY

# Issues updated today
updated >= startOfDay()
```

## Security Considerations

1. **API Token Security**: Store tokens in environment variables, never in code
2. **Least Privilege**: Use tokens with minimal required permissions
3. **Token Rotation**: Rotate API tokens regularly
4. **Audit Logging**: Jira logs all API actions

## Permissions Required

- Browse projects
- Create issues (for create_issue)
- Edit issues (for update_issue)
- Transition issues (for transition_issue)
- Add comments (for add_comment)
- Assign issues (for assign_issue)

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Run locally
npm start

# Run with inspector
npx @anthropic/mcp-inspector node dist/index.js
```

## Troubleshooting

### Common Issues

**Authentication Failed**
- Verify API token is correct
- For Cloud: Use email + API token
- For Server: Use PAT with JIRA_USE_PAT=true

**Permission Denied**
- Check user has required project permissions
- Verify token has necessary scopes

**Rate Limiting**
- Jira Cloud: 100 requests per minute
- Add delays between bulk operations

## License

MIT
