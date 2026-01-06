# Puppeteer MCP Server

Browser automation for web scraping, testing, and workflow automation.

## Source

- **npm**: [@anthropic-ai/mcp-puppeteer](https://www.npmjs.com/package/@anthropic-ai/mcp-puppeteer)
- **Maintainer**: Anthropic

## Quick Install

```bash
claude mcp add puppeteer -s user -- npx -y @anthropic-ai/mcp-puppeteer
```

## Features

- **Browser Control**: Automated browser interactions
- **Web Scraping**: Extract data from web pages
- **Testing**: Automated UI testing
- **Screenshots**: Capture page screenshots
- **PDF Generation**: Generate PDFs from pages

## Configuration

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-puppeteer"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `navigate` | Navigate to a URL |
| `screenshot` | Take a screenshot |
| `click` | Click an element |
| `type` | Type text into an input |
| `evaluate` | Execute JavaScript |
| `get_content` | Get page content |
| `pdf` | Generate PDF |

## Usage Examples

```
User: Take a screenshot of google.com
Claude: [Uses navigate and screenshot tools]

User: Scrape the product prices from this page
Claude: [Uses navigate and evaluate tools]

User: Fill out the contact form
Claude: [Uses navigate, type, and click tools]

User: Generate a PDF of the report page
Claude: [Uses navigate and pdf tools]
```

## Prerequisites

- Node.js v18+
- Chromium (auto-installed by Puppeteer)

## Notes

- Runs headless Chrome by default
- Useful for automating web workflows
- Consider rate limiting for scraping

## License

MIT - Anthropic
