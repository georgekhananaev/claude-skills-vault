# Stripe MCP Server

Payments integration for handling payments, managing customers, and accessing payment data.

## Source

- **Official URL**: [mcp.stripe.com](https://mcp.stripe.com)
- **Documentation**: [Stripe Docs](https://docs.stripe.com/)
- **Maintainer**: Stripe

## Quick Install

```bash
claude mcp add stripe --transport http https://mcp.stripe.com
```

## Features

- **Payment Processing**: Handle payments and refunds
- **Customer Management**: Create and manage customers
- **Subscription Handling**: Manage recurring billing
- **Payment Data Access**: Query payment history and analytics

## Configuration

```json
{
  "mcpServers": {
    "stripe": {
      "type": "http",
      "url": "https://mcp.stripe.com"
    }
  }
}
```

## Usage Examples

```
User: Show recent payments
Claude: [Uses Stripe MCP to query payments]

User: Create a customer for john@example.com
Claude: [Uses Stripe MCP to create customer]

User: Process a refund for payment pi_xxx
Claude: [Uses Stripe MCP to process refund]

User: List all subscriptions
Claude: [Uses Stripe MCP to list subscriptions]
```

## Authentication

Authenticates via Stripe's OAuth flow on first use.

## License

Proprietary - Stripe
