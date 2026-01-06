# Filesystem MCP Server

Secure file operations with configurable access controls.

## Source

- **npm**: [@modelcontextprotocol/server-filesystem](https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem)
- **GitHub**: [modelcontextprotocol/servers/src/filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
- **Maintainer**: Anthropic (MCP Steering Group)

## Quick Install

```bash
claude mcp add filesystem -s user -- npx -y @modelcontextprotocol/server-filesystem /path/to/allowed/dir
```

## Features

- **Secure Access**: Sandboxed to allowed directories
- **File Operations**: Read, write, list, search
- **Directory Management**: Create, move, delete
- **Search**: Find files by pattern

## Configuration

Pass allowed directories as arguments:

```bash
npx -y @modelcontextprotocol/server-filesystem /path/to/dir1 /path/to/dir2
```

## Claude Code Config

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/me/projects",
        "/Users/me/documents"
      ]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `read_multiple_files` | Read multiple files at once |
| `write_file` | Write content to file |
| `edit_file` | Make selective edits with diffs |
| `list_directory` | List directory contents |
| `create_directory` | Create new directory |
| `move_file` | Move or rename file |
| `search_files` | Search for files by pattern |
| `get_file_info` | Get file metadata |
| `list_allowed_directories` | List accessible directories |

## Security

- Only accesses specified directories
- No access outside sandbox
- Symlink protection
- Path traversal prevention

## Usage

```
User: List files in my projects folder
Claude: [Uses list_directory tool]

User: Read the package.json
Claude: [Uses read_file tool]

User: Find all TypeScript files
Claude: [Uses search_files with *.ts pattern]
```

## License

MIT - [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
