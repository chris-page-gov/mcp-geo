# MCP Apps Alignment (2026-01-26)

This note summarizes how the repo aligns with the finalized MCP Apps spec and
removes legacy OpenAI Apps (skybridge) compatibility.

## Sources
- MCP Apps spec: `docs/vendor/mcp/repos/ext-apps/specification/2026-01-26/apps.mdx`
- MCP core spec: `docs/vendor/mcp/repos/modelcontextprotocol/docs/specification/2025-11-25/`

## Alignment Summary
- Core MCP handshake now negotiates protocol versions instead of echoing client input.
  Server preference is `2025-11-25`, with compatibility support for
  `2025-06-18`, `2025-03-26`, and `2024-11-05`.
- Streamable HTTP now validates `MCP-Protocol-Version` headers against supported and
  negotiated session versions (400 on invalid/unsupported mismatches).
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

## Compatibility-first delivery order

MCP Geo uses a deterministic layering policy for map delivery:

1. `os_maps.render` (static map contract)
2. `overlay_bundle` structured overlays
3. MCP-Apps widget resources (`ui://`) when UI is supported
4. Fallback skeletons (`map_card`, `overlay_bundle`, `export_handoff`) for
   partial/no-UI hosts

Canonical fallback keys and conformance guidance are documented in:

- `docs/spec_package/06_api_contracts.md`
- `docs/spec_package/06a_map_delivery_fallback_contracts.md`

## Host support references

- Browser/host capability matrix: `docs/map_delivery_support_matrix.md`
- Trial evidence index: `research/map_delivery_research_2026-02/README.md`
- Troubleshooting modes/toggles: `docs/troubleshooting.md`

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
