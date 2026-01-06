# Supabase MCP Server

Custom MCP server for Supabase with database, auth, storage, and edge functions integration.

## Features

- **Database**: Query, insert, update, delete with RLS support
- **Schema**: List tables, describe columns, view RLS policies
- **Auth**: List users, get user details, create users
- **Storage**: List buckets, browse files, get URLs
- **Edge Functions**: Invoke serverless functions
- **RPC**: Call database functions

## Installation

```bash
cd mcp-servers/supabase
npm install
npm run build
```

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Project URL | Yes |
| `SUPABASE_SERVICE_KEY` | Service role key (full access) | Recommended |
| `SUPABASE_ANON_KEY` | Anon key (limited access) | Fallback |
| `MAX_ROWS` | Max rows returned | 100 |
| `ALLOW_WRITES` | Enable write operations | false |

### Getting Credentials

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select project → Settings → API
3. Copy Project URL and service_role key

### Claude Code Config

```json
{
  "mcpServers": {
    "supabase": {
      "command": "node",
      "args": ["/path/to/supabase/dist/index.js"],
      "env": {
        "SUPABASE_URL": "https://xxx.supabase.co",
        "SUPABASE_SERVICE_KEY": "eyJ...",
        "ALLOW_WRITES": "false"
      }
    }
  }
}
```

## Tools

### Database

| Tool | Description |
|------|-------------|
| `query` | Query table with filters, ordering, pagination |
| `list_tables` | List all tables with row counts |
| `describe_table` | Get table schema and columns |
| `insert` | Insert row(s) (requires ALLOW_WRITES) |
| `update` | Update rows (requires ALLOW_WRITES) |
| `delete` | Delete rows (requires ALLOW_WRITES) |
| `rpc` | Call database function |
| `sql` | Execute raw SQL |

### RLS Policies

| Tool | Description |
|------|-------------|
| `list_policies` | List RLS policies for a table |

### Auth

| Tool | Description |
|------|-------------|
| `list_users` | List auth users (paginated) |
| `get_user` | Get user by ID or email |
| `create_user` | Create new user (requires ALLOW_WRITES) |

### Storage

| Tool | Description |
|------|-------------|
| `list_buckets` | List storage buckets |
| `list_files` | List files in a bucket |
| `get_file_url` | Get public or signed URL |

### Edge Functions

| Tool | Description |
|------|-------------|
| `invoke_function` | Invoke an Edge Function |

## Usage Examples

```
User: Show all tables in the database
Claude: [Uses list_tables tool]

User: Get all active users with their profiles
Claude: [Uses query with filter: { status: 'active' }]

User: What RLS policies are on the posts table?
Claude: [Uses list_policies tool]

User: List all auth users
Claude: [Uses list_users tool]

User: Get files in the avatars bucket
Claude: [Uses list_files with bucket: 'avatars']

User: Call the calculate_stats function
Claude: [Uses rpc tool]
```

## Security

- Read-only by default (`ALLOW_WRITES=false`)
- Service key bypasses RLS - use carefully
- Consider anon key for read-only access
- Row limit prevents memory issues

## Helper Functions

For `sql` and `list_policies` to work, create these functions in Supabase:

```sql
-- Execute raw SQL (be careful with permissions!)
CREATE OR REPLACE FUNCTION execute_sql(query_text TEXT)
RETURNS JSON AS $$
BEGIN
  RETURN (SELECT json_agg(row_to_json(t)) FROM (SELECT * FROM query_text) t);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get RLS policies
CREATE OR REPLACE FUNCTION get_policies(p_table TEXT)
RETURNS TABLE (policyname NAME, cmd TEXT, qual TEXT, with_check TEXT) AS $$
BEGIN
  RETURN QUERY
  SELECT pol.polname, pol.polcmd::TEXT, pg_get_expr(pol.polqual, pol.polrelid), pg_get_expr(pol.polwithcheck, pol.polrelid)
  FROM pg_policy pol
  JOIN pg_class cls ON pol.polrelid = cls.oid
  WHERE cls.relname = p_table;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## License

MIT
