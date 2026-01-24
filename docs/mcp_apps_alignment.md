# MCP Apps Alignment (ext-apps + OpenAI Apps SDK)

This note summarizes how the ext-apps MCP UI standard and the OpenAI Apps SDK
spec diverge, plus how this repo now supports both paths.

## Sources
- ext-apps spec: `docs/vendor/mcp/repos/ext-apps/specification/draft/apps.mdx`
- OpenAI Apps SDK: `docs/vendor/openai/_snapshot/apps-sdk/build/mcp-server.html`
- OpenAI MCP docs: `docs/vendor/openai/_snapshot/docs/mcp.html`

## Key Differences
- MIME type
  - ext-apps: `text/html;profile=mcp-app`
  - OpenAI Apps: `text/html+skybridge`
- Tool metadata for UI templates
  - ext-apps: `_meta.ui.resourceUri` (legacy `_meta["ui/resourceUri"]`)
  - OpenAI Apps: `_meta["openai/outputTemplate"]` plus optional
    `_meta["openai/widgetAccessible"]`
- Resource metadata
  - ext-apps: `_meta.ui.csp`, `_meta.ui.permissions`, `_meta.ui.prefersBorder`
  - OpenAI Apps: `_meta["openai/widgetCSP"]`, `_meta["openai/widgetPrefersBorder"]`,
    `_meta["openai/widgetDescription"]`
- Tool response semantics
  - ext-apps: `content` for model context, `structuredContent` for UI, `_meta` for
    non-model metadata
  - OpenAI Apps: `structuredContent` is model-visible; `_meta` is widget-only

## Dual-path Implementation (this repo)
- Two UI resources per widget
  - ext-apps URI (no extension): `ui://mcp-geo/<slug>`
  - OpenAI Apps URI: `ui://mcp-geo/<slug>.html`
  - Both URIs serve the same HTML file; MIME type differs by URI.
- Tool descriptors
  - `os_apps.render_*` tools include:
    - `_meta.ui.resourceUri` (ext-apps)
    - `_meta["ui/resourceUri"]` (legacy ext-apps)
    - `_meta["openai/outputTemplate"]` (OpenAI Apps)
    - `_meta["openai/widgetAccessible"]` (OpenAI Apps)
- Tool results
  - Render tools return `structuredContent` and `content` alongside the existing
    `status/config/instructions/uiResourceUris` shape.
  - The stdio + HTTP MCP adapters promote `structuredContent` and `_meta` to the
    top-level MCP result while preserving `content` and `resource_link` output.
- Resource reads
  - UI resources return `_meta` inside `contents[]` with both ext-apps `ui` and
    OpenAI `openai/*` keys.

## CSP Allowlist (geography selector)
These domains are allowed for the map UI:
- `https://api.os.uk`
- `https://tile.openstreetmap.org`
- `https://unpkg.com`
- `https://fonts.googleapis.com`
- `https://fonts.gstatic.com`

## Quick Validation
- `resources/read` returns:
  - `ui://mcp-geo/geography-selector` with `text/html;profile=mcp-app`
  - `ui://mcp-geo/geography-selector.html` with `text/html+skybridge`
- `tools/describe` for `os_apps.render_geography_selector` includes both
  `_meta.ui.resourceUri` and `_meta["openai/outputTemplate"]`.
- `tools/call` (MCP JSON-RPC) includes `content`, `structuredContent`, and `_meta`
  for render tools, plus `resource_link` entries when UI is referenced.
