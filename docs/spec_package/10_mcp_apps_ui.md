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
- `os_apps.render_ui_probe`

Each render tool returns:
- `status` + `instructions`
- a UI resource URI
- a structured payload for the host client

For routing, the structured payload is no longer a demo-only shell. The route
planner widget now:

- accepts `stops`, optional `via`, `profile`, `constraints`, and `delivery`
- normalizes payloads from `structuredContent`, legacy result shapes, and host
  notifications
- calls `os_route.get` for route computation
- renders returned route geometry, steps, mode changes, warnings, and graph
  freshness on the OS vector basemap
- preserves compact-window behavior and shows inline errors for ambiguous stops
  or graph-not-ready states

UI content blocks are controlled by `MCP_APPS_CONTENT_MODE`:
- `resource_link` emits a `resource_link` content block pointing at `ui://` resources.
- `embedded` embeds UI HTML as a `resource` content block.
- `text` emits text-only content.

## STDIO UI fallback behavior

- If the client does not advertise UI support, the stdio adapter injects a
  static map fallback payload for the geography selector.
- Environment: `MCP_STDIO_UI_SUPPORTED=1` to force UI mode.

The route planner does not silently fabricate a route when solver data is
unavailable. Hosts should surface the returned `ROUTE_GRAPH_NOT_READY`,
`AMBIGUOUS_STOP`, or `NO_ROUTE` errors directly.

## Known integration issues

- Some clients require an explicit `initialize` message with UI capabilities.
- Inspector proxy or Claude UI may time out when connecting over STDIO if the
  proxy cannot spawn the command or a token mismatch occurs.

## Reference screenshots

Example map render (external reference image captured from Claude):

![Example map render](../MasterMap%20from%20Claude.png)

### UI captures (pending)

![Geography selector UI](images/ui-geography-selector.png)

![Route planner UI](images/ui-route-planner.png)

![Feature inspector UI](images/ui-feature-inspector.png)

![Statistics dashboard UI](images/ui-statistics-dashboard.png)
