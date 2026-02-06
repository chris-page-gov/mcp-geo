# MCP Apps Alignment (2026-01-26)

This note summarizes how the repo aligns with the finalized MCP Apps spec and
removes legacy OpenAI Apps (skybridge) compatibility.

## Sources
- MCP Apps spec: `docs/vendor/mcp/repos/ext-apps/specification/2026-01-26/apps.mdx`
- MCP core spec: `docs/vendor/mcp/repos/modelcontextprotocol/docs/specification/2025-11-25/`

## Alignment Summary
- UI resources are exposed as `ui://mcp-geo/<slug>` with
  `mimeType: text/html;profile=mcp-app`.
- Tool metadata uses `_meta.ui.resourceUri` only (no `openai/*` keys).
- Tool results return standard MCP `content` and optional `structuredContent`.
  Compatibility shims:
  - Legacy `uiResourceUris` field.
  - Optional `resource_link` content block pointing at the UI resource when
    `MCP_APPS_RESOURCE_LINK=1` (disabled by default to avoid unsupported format warnings).
  - `MCP_APPS_CONTENT_MODE` can force `resource_link`, embedded `resource`, or
    text-only content blocks; `contentMode` overrides per call.
  Canonical field remains `_meta.ui.resourceUri`.
- UI host/view communication uses JSON-RPC 2.0 over `postMessage` with
  `ui/initialize` → `ui/notifications/initialized`, and the UI uses standard
  MCP methods like `tools/call` and `resources/read`.
- The MapLibre CSP worker is served locally at `/maps/worker/maplibre-gl-csp-worker.js`.

## CSP Allowlist (Geography Selector)
The geography selector declares:
- `connectDomains`: `self`, `https://api.os.uk`
- `resourceDomains`: `self`, `https://api.os.uk`, `https://fonts.googleapis.com`,
  `https://fonts.gstatic.com`, `https://unpkg.com`
OSM tiles are proxied through the server (`/maps/raster/osm`), so direct tile
host access is not required.

## Quick Validation
- `resources/read` returns `ui://mcp-geo/geography-selector` with
  `text/html;profile=mcp-app` and `_meta.ui.csp`.
- `tools/describe` for `os_apps.render_geography_selector` includes
  `_meta.ui.resourceUri`.
- The playground host responds to `ui/initialize` and bridges `tools/call` /
  `resources/read` for the UI.
