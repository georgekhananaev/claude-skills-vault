# Playwright MCP Server

Browser automation using Playwright's accessibility tree for fast, deterministic interactions.

## Source

- **npm**: [@playwright/mcp](https://www.npmjs.com/package/@playwright/mcp)
- **GitHub**: [microsoft/playwright](https://github.com/microsoft/playwright)
- **Maintainer**: Microsoft

## Quick Install

```bash
claude mcp add playwright -s user -- npx -y @playwright/mcp@latest
```

## Features

- **Fast & Lightweight**: Uses accessibility tree, not screenshots
- **LLM-Friendly**: No vision models needed
- **Deterministic**: Structured data, not pixel-based
- **Multi-Browser**: Chromium, Firefox, WebKit

## Configuration

No environment variables required.

## Claude Code Config

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `browser_navigate` | Navigate to URL |
| `browser_screenshot` | Take screenshot |
| `browser_click` | Click element |
| `browser_type` | Type text into element |
| `browser_hover` | Hover over element |
| `browser_select_option` | Select dropdown option |
| `browser_tab_list` | List open tabs |
| `browser_tab_new` | Open new tab |
| `browser_tab_select` | Switch tabs |
| `browser_tab_close` | Close tab |
| `browser_get_text` | Get page text content |
| `browser_console` | Get console logs |
| `browser_network` | Get network requests |

## Usage

```
User: Take a screenshot of example.com
Claude: [Uses browser_navigate then browser_screenshot]

User: Fill out the login form and submit
Claude: [Uses browser_type and browser_click]

User: Get all the text from this page
Claude: [Uses browser_get_text]
```

## Comparison with Puppeteer MCP

| Feature | Playwright MCP | Puppeteer MCP |
|---------|---------------|---------------|
| Approach | Accessibility tree | Screenshots + DOM |
| Speed | Faster | Slower |
| Vision Model | Not needed | Optional |
| Multi-browser | Yes | Chromium only |

## Prerequisites

Playwright browsers are installed automatically on first run.

## Security Notes

- Be careful with automated logins
- Respect robots.txt
- Don't use for malicious scraping

## License

Apache 2.0 - Microsoft
