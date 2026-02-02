# MCP-Apps UI (Interactive Tools)

## Overview

MCP Geo exposes UI resources that can be opened by MCP clients that support
`text/html;profile=mcp-app` resources.

## UI resources

- `ui://mcp-geo/geography-selector`
- `ui://mcp-geo/route-planner`
- `ui://mcp-geo/feature-inspector`
- `ui://mcp-geo/statistics-dashboard`

## Render tools

- `os_apps.render_geography_selector`
- `os_apps.render_route_planner`
- `os_apps.render_feature_inspector`
- `os_apps.render_statistics_dashboard`

Each render tool returns:
- `status` + `instructions`
- a UI resource URI
- a structured payload for the host client

## STDIO UI fallback behavior

- If the client does not advertise UI support, the stdio adapter injects a
  static map fallback payload for the geography selector.
- Environment: `MCP_STDIO_UI_SUPPORTED=1` to force UI mode.

## Known integration issues

- Some clients require an explicit `initialize` message with UI capabilities.
- Inspector proxy or Claude UI may time out when connecting over STDIO if the
  proxy cannot spawn the command or a token mismatch occurs.

## Reference screenshots

Example map render (external reference image captured from Claude):

![Example map render](../MasterMap%20from%20Claude.png)
