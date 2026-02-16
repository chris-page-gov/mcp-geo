# Map Delivery Support Matrix

Last verified: 2026-02-14

This matrix defines the map-delivery behavior MCP Geo operators should expect by
host/browser profile. It anchors to the compatibility-first order:

1. `os_maps.render` static contract
2. `overlay_bundle` data overlays
3. MCP-Apps widgets (`os_apps.render_*`) when UI is supported
4. Deterministic fallback skeletons (`map_card`, `overlay_bundle`, `export_handoff`)

## Capability matrix

| Host profile | Engine | Static contract (`os_maps.render`) | Overlay bundle | Widgets | Fallback skeletons | Required toggles | Verified | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Playwright trial harness | Chromium desktop | supported | supported | supported (simulated host) | supported | none | 2026-02-13 | `research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl`, `research/map_delivery_research_2026-02/evidence/screenshots/chromium-desktop-trial-3-geography-selector.png` |
| Playwright trial harness | Firefox desktop | supported | supported | unknown (host simulation not validated) | supported | none | 2026-02-13 | `research/map_delivery_research_2026-02/evidence/screenshots/firefox-desktop-trial-1-static-osm.png`, `research/map_delivery_research_2026-02/evidence/screenshots/firefox-desktop-trial-2-os-maps-render.png` |
| Playwright trial harness | WebKit desktop | supported | supported | unknown (host simulation not validated) | supported | none | 2026-02-13 | `research/map_delivery_research_2026-02/evidence/screenshots/webkit-desktop-trial-1-static-osm.png`, `research/map_delivery_research_2026-02/evidence/screenshots/webkit-desktop-trial-2-os-maps-render.png` |
| Playwright trial harness | Chromium mobile | supported | supported | partial (simulated host path) | supported | none | 2026-02-14 | `research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl` |
| Playwright trial harness | WebKit mobile | supported | supported | unsupported/unknown | supported | none | 2026-02-14 | `research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl` |
| Claude Desktop (STDIO) | Host webview | supported | supported | partial (depends on ext-apps support + content mode) | supported | `MCP_STDIO_CLAUDE_APPS_CONTENT_MODE=resource_link`, keep `MCP_APPS_RESOURCE_LINK=0` | 2026-02-14 | `docs/troubleshooting.md`, `logs/claude-trace.jsonl` |
| MCP clients without `io.modelcontextprotocol/ui` | any | supported | supported | unsupported by definition | required | none | 2026-02-14 | `server/stdio_adapter.py`, `server/mcp/http_transport.py`, `server/mcp/client_capabilities.py` |

## Limits and operational notes

- Prefer `MCP_TOOLS_DEFAULT_TOOLSET=starter` for initialization to reduce
  startup schema payloads.
- Non-UI hosts should consume explicit `fallback` data and avoid retry loops
  that assume widget rendering is available.
- Treat `resource_link` content blocks as opt-in until host-specific evidence
  confirms support.
- Claude inline web previews are not a full browser runtime; external-CDN
  MapLibre HTML helpers may fail there even when they work correctly in Safari/
  Chrome.
- For Claude stdio widget calls, use
  `MCP_STDIO_CLAUDE_APPS_CONTENT_MODE=resource_link` to avoid embedded HTML
  transcript dumps while still emitting a UI-launchable widget link block.
- Latest Claude evidence (2026-02-14): tool results now emit `resource_link`
  and Claude performs `resources/read` on `ui://...`, but widget bridge events
  (`os_apps.log_event`) still do not appear in trace, indicating host-side
  runtime mount/bridge failure.
- Boundary Explorer requires the 2026-02-14 runtime hardening path so host
  initialization can complete even when map runtime init degrades; otherwise
  some Claude sessions may show raw HTML fallback.
- Geography Selector and Boundary Explorer now use absolute MapLibre CDN asset
  URLs (with jsDelivr fallback) instead of `ui://`-relative `vendor/*` links,
  because some hosts do not resolve relative subresources for UI resources.
- Apply constrained profiles from
  `resource://mcp-geo/map-embedding-style-profiles` for mixed/no-UI fleets.
- Revalidate this matrix on every release that changes map tools, UI payload
  shape, or client capability negotiation.
