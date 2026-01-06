# Chrome DevTools MCP Server

Chrome DevTools for coding agents - enables browser automation, performance analysis, and debugging capabilities.

**Repository:** https://github.com/ChromeDevTools/chrome-devtools-mcp
**License:** Apache-2.0

## Requirements

- Node.js v20.19+ (LTS)
- Chrome stable or newer
- npm

## Installation

### Claude Code CLI

```bash
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest
```

### Manual Configuration

Add to your MCP client config:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

### With Options

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["chrome-devtools-mcp@latest", "--channel=canary", "--headless=true"]
    }
  }
}
```

## Configuration Options

### Connection Methods

| Option | Description |
|--------|-------------|
| `--browserUrl, -u` | Connect to running Chrome (e.g., `http://127.0.0.1:9222`) |
| `--wsEndpoint, -w` | WebSocket endpoint for remote Chrome |
| `--wsHeaders` | Custom JSON headers for WebSocket auth |
| `--autoConnect` | Auto-connect to running Chrome 145+ |

### Chrome Launch Options

| Option | Description | Default |
|--------|-------------|---------|
| `--channel` | `stable`, `canary`, `beta`, or `dev` | stable |
| `--headless` | Run without UI | false |
| `--isolated` | Temporary profile, auto-cleaned | false |
| `--userDataDir` | Custom profile path | - |
| `--executablePath, -e` | Path to Chrome binary | - |
| `--viewport` | Initial size (e.g., `1280x720`) | - |

### Advanced Options

| Option | Description |
|--------|-------------|
| `--proxyServer` | Proxy configuration |
| `--acceptInsecureCerts` | Ignore certificate errors |
| `--chromeArg` | Additional Chrome arguments (array) |
| `--logFile` | Debug log output path |
| `--categoryEmulation` | Toggle emulation features |
| `--categoryPerformance` | Toggle performance features |
| `--categoryNetwork` | Toggle network features |

## Available Tools (26)

### Input Automation (8)

- `click` - Click on elements
- `drag` - Drag elements
- `fill` - Fill input fields
- `fill_form` - Fill entire forms
- `handle_dialog` - Handle browser dialogs
- `hover` - Hover over elements
- `press_key` - Simulate key presses
- `upload_file` - Upload files

### Navigation (6)

- `close_page` - Close browser page
- `list_pages` - List open pages
- `navigate_page` - Navigate to URL
- `new_page` - Open new page
- `select_page` - Switch between pages
- `wait_for` - Wait for conditions

### Emulation (2)

- `emulate` - Emulate device/conditions
- `resize_page` - Resize viewport

### Performance (3)

- `performance_analyze_insight` - Get performance insights
- `performance_start_trace` - Start performance trace
- `performance_stop_trace` - Stop and get trace data

### Network (2)

- `get_network_request` - Get request details
- `list_network_requests` - List all requests

### Debugging (5)

- `evaluate_script` - Execute JavaScript
- `get_console_message` - Get console message
- `list_console_messages` - List console output
- `take_screenshot` - Capture screenshot
- `take_snapshot` - Take DOM snapshot

## Connecting to Existing Chrome

### Automatic (Chrome 144+)

1. Enable at `chrome://inspect/#remote-debugging`
2. Configure with `--autoConnect --channel=beta`

### Manual Port Forwarding

Add `--browser-url=http://127.0.0.1:9222` to config, then start Chrome:

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile-stable
```

**Linux:**
```bash
/usr/bin/google-chrome --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-profile-stable
```

**Windows:**
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" \
  --remote-debugging-port=9222 --user-data-dir="%TEMP%\chrome-profile-stable"
```

## Usage Example

Test the setup:
```
Check the performance of https://developers.chrome.com
```

The browser launches automatically when a tool requiring it is invoked.

## Notes

- Default profile: `$HOME/.cache/chrome-devtools-mcp/chrome-profile-$CHANNEL`
- Exposes browser content to MCP clients - avoid sensitive data
- Sandboxed environments: Use `--browser-url` instead of auto-launch
