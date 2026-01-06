# GCP MCP Server

Google Cloud Platform integration for managing GCP services.

## Source

- **npm**: [@eniayomi/gcp-mcp-server](https://www.npmjs.com/package/@eniayomi/gcp-mcp-server)
- **GitHub**: [eniayomi/gcp-mcp-server](https://github.com/eniayomi/gcp-mcp-server)
- **Maintainer**: Community

## Quick Install

```bash
claude mcp add gcp -e GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json -e GCP_PROJECT_ID=your-project-id -s user -- npx -y @eniayomi/gcp-mcp-server
```

## Features

- **Compute Engine**: Manage VMs and instances
- **Cloud Storage**: Access GCS buckets and objects
- **BigQuery**: Query and manage datasets
- **Cloud Functions**: Deploy and manage functions

## Configuration

```json
{
  "mcpServers": {
    "gcp": {
      "command": "npx",
      "args": ["-y", "@eniayomi/gcp-mcp-server"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account-key.json",
        "GCP_PROJECT_ID": "your-project-id"
      }
    }
  }
}
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Yes |
| `GCP_PROJECT_ID` | GCP project ID | Yes |

## Getting Credentials

1. Go to [GCP Console](https://console.cloud.google.com/)
2. Navigate to IAM & Admin → Service Accounts
3. Create a service account or use existing
4. Generate and download JSON key

## Usage Examples

```
User: List my GCP instances
Claude: [Uses GCP MCP to list VMs]

User: Show buckets in my project
Claude: [Uses GCP MCP to list storage buckets]

User: Query BigQuery for user stats
Claude: [Uses GCP MCP to run query]

User: Deploy the function to Cloud Functions
Claude: [Uses GCP MCP to deploy]
```

## Prerequisites

- Node.js v18+
- GCP account with appropriate permissions
- Service account key file

## Security Notes

- Use least privilege for service accounts
- Never commit credentials to git
- Rotate keys regularly

## License

MIT - Community
