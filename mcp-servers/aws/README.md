# AWS MCP Servers

Official AWS MCP servers from AWS Labs - 64+ servers for AWS service integration.

## Source

- **GitHub**: [awslabs/mcp](https://github.com/awslabs/mcp)
- **Documentation**: [awslabs.github.io/mcp](https://awslabs.github.io/mcp/)
- **Docker Images**: `public.ecr.aws/awslabs-mcp/`
- **Maintainer**: AWS Labs

## Prerequisites

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python
uv python install 3.10

# Configure AWS credentials
aws configure
```

## Quick Install

```bash
# Core orchestration server
claude mcp add aws-core -s user -- uvx awslabs.core-mcp-server@latest

# AWS Documentation
claude mcp add aws-docs -s user -- uvx awslabs.aws-documentation-mcp-server@latest

# Bedrock Knowledge Bases
claude mcp add aws-bedrock-kb -s user -- uvx awslabs.bedrock-kb-retrieval-mcp-server@latest

# DynamoDB
claude mcp add aws-dynamodb -s user -- uvx awslabs.dynamodb-mcp-server@latest

# CDK Development
claude mcp add aws-cdk -s user -- uvx awslabs.cdk-mcp-server@latest
```

## Available Servers

### Core & Documentation

| Package | Description |
|---------|-------------|
| `awslabs.core-mcp-server` | Planning and orchestration |
| `awslabs.aws-documentation-mcp-server` | AWS docs and API references |
| `awslabs.aws-api-mcp-server` | General AWS API access |

### Infrastructure & Deployment

| Package | Description |
|---------|-------------|
| `awslabs.cdk-mcp-server` | AWS CDK development |
| `awslabs.terraform-mcp-server` | Terraform workflows |
| `awslabs.cloudformation-mcp-server` | CloudFormation templates |
| `awslabs.aws-iac-mcp-server` | Infrastructure as Code toolkit |
| `awslabs.eks-mcp-server` | Amazon EKS management |
| `awslabs.ecs-mcp-server` | Amazon ECS management |
| `awslabs.serverless-mcp-server` | Serverless applications |
| `awslabs.lambda-tool-mcp-server` | Lambda function tools |

### AI & Machine Learning

| Package | Description |
|---------|-------------|
| `awslabs.bedrock-kb-retrieval-mcp-server` | Knowledge base queries |
| `awslabs.kendra-mcp-server` | Amazon Kendra index |
| `awslabs.nova-canvas-mcp-server` | Image generation |
| `awslabs.bedrock-data-automation-mcp-server` | Bedrock automation |
| `awslabs.sagemaker-mcp-server` | SageMaker AI |

### Data & Analytics

| Package | Description |
|---------|-------------|
| `awslabs.dynamodb-mcp-server` | DynamoDB operations |
| `awslabs.postgres-mcp-server` | PostgreSQL via RDS Data API |
| `awslabs.aurora-mcp-server` | Aurora PostgreSQL/MySQL |
| `awslabs.documentdb-mcp-server` | Amazon DocumentDB |
| `awslabs.neptune-mcp-server` | Amazon Neptune |
| `awslabs.elasticache-mcp-server` | Amazon ElastiCache |
| `awslabs.redshift-mcp-server` | Amazon Redshift |
| `awslabs.s3-tables-mcp-server` | S3 Tables |

### Operations & Monitoring

| Package | Description |
|---------|-------------|
| `awslabs.cloudwatch-mcp-server` | Metrics and logs analysis |
| `awslabs.cloudtrail-mcp-server` | CloudTrail audit logs |
| `awslabs.billing-mcp-server` | Billing and cost management |
| `awslabs.cost-explorer-mcp-server` | Cost analysis |
| `awslabs.pricing-mcp-server` | AWS pricing information |
| `awslabs.support-mcp-server` | AWS Support integration |

### Integration & Messaging

| Package | Description |
|---------|-------------|
| `awslabs.sns-sqs-mcp-server` | SNS/SQS messaging |
| `awslabs.mq-mcp-server` | Amazon MQ |
| `awslabs.stepfunctions-mcp-server` | Step Functions workflows |
| `awslabs.appsync-mcp-server` | AWS AppSync |
| `awslabs.location-mcp-server` | Location Service |

### Developer Tools

| Package | Description |
|---------|-------------|
| `awslabs.git-repo-research-mcp-server` | Git repository analysis |
| `awslabs.code-doc-gen-mcp-server` | Code documentation generation |
| `awslabs.diagram-mcp-server` | AWS architecture diagrams |
| `awslabs.iam-mcp-server` | IAM policy management |

## Configuration

### Claude Code Config

```json
{
  "mcpServers": {
    "aws-core": {
      "command": "uvx",
      "args": ["awslabs.core-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    },
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    },
    "aws-dynamodb": {
      "command": "uvx",
      "args": ["awslabs.dynamodb-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

### Windows Configuration

```json
{
  "mcpServers": {
    "aws-core": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "awslabs.core-mcp-server@latest",
        "awslabs.core-mcp-server.exe"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AWS_PROFILE` | AWS profile name |
| `AWS_REGION` | AWS region |
| `AWS_ACCESS_KEY_ID` | Access key (if not using profile) |
| `AWS_SECRET_ACCESS_KEY` | Secret key (if not using profile) |
| `FASTMCP_LOG_LEVEL` | Log level (ERROR, WARNING, INFO, DEBUG) |

## Usage Examples

```
User: Show me the latest Lambda documentation
Claude: [Uses aws-documentation-mcp-server]

User: Query my DynamoDB users table
Claude: [Uses dynamodb-mcp-server]

User: What are my AWS costs this month?
Claude: [Uses cost-explorer-mcp-server]

User: Create a CDK stack for a serverless API
Claude: [Uses cdk-mcp-server]

User: Search my Bedrock knowledge base for auth docs
Claude: [Uses bedrock-kb-retrieval-mcp-server]
```

## Tips

- Remove `@latest` after initial setup for faster startup
- Use `uv cache clean <package>` to refresh cached versions
- Docker containers available for production deployments

## Legacy Server

The archived `@modelcontextprotocol/server-aws-kb-retrieval` is superseded by `awslabs.bedrock-kb-retrieval-mcp-server`.

## License

Apache 2.0 - [AWS Labs](https://github.com/awslabs/mcp)
