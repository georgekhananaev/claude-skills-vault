# Git MCP Server

Tools to read, search, and manipulate Git repositories.

## Source

- **npm**: [@modelcontextprotocol/server-git](https://www.npmjs.com/package/@modelcontextprotocol/server-git)
- **GitHub**: [modelcontextprotocol/servers-archived/src/git](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/git)
- **Status**: Archived (still functional, no longer actively maintained)

## Quick Install

```bash
claude mcp add git -s user -- npx -y @modelcontextprotocol/server-git
```

## Features

- **Repository Info**: Status, branches, remotes
- **History**: Log, diff, blame
- **Search**: Find commits, search code
- **Operations**: Commit, branch, checkout

## Configuration

No environment variables required. Works with repositories in current directory.

## Claude Code Config

```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `git_status` | Get repository status |
| `git_diff_unstaged` | Show unstaged changes |
| `git_diff_staged` | Show staged changes |
| `git_diff` | Show diff between refs |
| `git_commit` | Create a commit |
| `git_add` | Stage files |
| `git_reset` | Unstage files |
| `git_log` | View commit history |
| `git_show` | Show commit details |
| `git_branch` | List or create branches |
| `git_checkout` | Switch branches |

## Usage

```
User: What changed in the last 5 commits?
Claude: [Uses git_log tool]

User: Show the diff for the login feature
Claude: [Uses git_diff tool]

User: Commit my changes with message "Fix bug"
Claude: [Uses git_add and git_commit tools]
```

## Notes

- Works with local repositories
- Supports all common git operations
- Safe defaults for destructive operations

## License

MIT - [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
