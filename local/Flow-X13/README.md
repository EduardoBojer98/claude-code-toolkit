# Claude Code on Flow-X13

Synced: 2026-10-24T09:33Z by scripts/sync-local.sh
Claude Code: 2.1.308 (Claude Code)

## Copied
- settings.json
- plugins/installed_plugins.json
- plugins/known_marketplaces.json
- mcp-servers.json
- skills/

## MCP servers (claude mcp list)
```
Checking MCP server health…

claude.ai Claude Docs: https://api.anthropic.com/v1/pages/mcp - ✔ Connected
claude.ai Context7: https://mcp.context7.com/mcp - ✔ Connected
plugin:figma:figma: https://mcp.figma.com/mcp (HTTP) - ! Needs authentication
plugin:playwright:playwright: npx @playwright/mcp@latest - ✘ Failed to connect — MCP server "plugin:playwright:playwright" connection timed out after 30000ms
shopify-dev-mcp: npx -y @shopify/dev-mcp@1.17.0 - ✘ Failed to connect — MCP server "shopify-dev-mcp" connection timed out after 30000ms
```
