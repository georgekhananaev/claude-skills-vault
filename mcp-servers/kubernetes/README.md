# Kubernetes MCP Server

Manage Kubernetes clusters, pods, and deployments.

## Source

- **GitHub**: [Flux159/mcp-server-kubernetes](https://github.com/Flux159/mcp-server-kubernetes)
- **npm**: [mcp-server-kubernetes](https://www.npmjs.com/package/mcp-server-kubernetes)
- **Alternative**: [containers/kubernetes-mcp-server](https://github.com/containers/kubernetes-mcp-server) (Go implementation)
- **Maintainer**: Community

## Quick Install

```bash
# Using community server
claude mcp add kubernetes -s user -- npx -y mcp-server-kubernetes
```

## Features

- **Cluster Management**: View cluster info
- **Pod Operations**: List, describe, logs
- **Deployments**: Scale, update, rollback
- **Services**: View service configurations

## Configuration

Uses local kubeconfig from `~/.kube/config`.

| Variable | Description | Default |
|----------|-------------|---------|
| `KUBECONFIG` | Path to kubeconfig | ~/.kube/config |
| `KUBERNETES_CONTEXT` | Context to use | current-context |

## Claude Code Config

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "mcp-server-kubernetes"],
      "env": {
        "KUBECONFIG": "~/.kube/config"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `list_pods` | List pods in namespace |
| `get_pod_logs` | Get pod logs |
| `describe_pod` | Get pod details |
| `list_deployments` | List deployments |
| `scale_deployment` | Scale replicas |
| `list_services` | List services |
| `list_namespaces` | List namespaces |
| `get_events` | Get cluster events |
| `apply_manifest` | Apply YAML manifest |

## Usage

```
User: Show pods in the production namespace
Claude: [Uses list_pods tool]

User: What's wrong with the api deployment?
Claude: [Uses describe_pod and get_events tools]

User: Scale the web deployment to 5 replicas
Claude: [Uses scale_deployment tool]

User: Show logs for the crashing pod
Claude: [Uses get_pod_logs tool]
```

## Security Notes

- Use RBAC for least privilege access
- Consider read-only service accounts
- Audit all kubectl operations

## Alternative Implementations

- [Robusta Kubernetes MCP](https://github.com/robusta-dev/kubernetes-mcp-server) - Recommended for production

## License

MIT - Community
