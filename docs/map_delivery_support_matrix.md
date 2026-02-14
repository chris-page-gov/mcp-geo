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
| Claude Desktop (STDIO) | Host webview | supported | supported | partial (depends on ext-apps support + content mode) | supported | `MCP_APPS_CONTENT_MODE=embedded`, keep `MCP_APPS_RESOURCE_LINK=0` | 2026-02-13 | `docs/troubleshooting.md`, `logs/claude-trace.jsonl` |
| MCP clients without `io.modelcontextprotocol/ui` | any | supported | supported | unsupported by definition | required | none | 2026-02-14 | `server/stdio_adapter.py`, `server/mcp/http_transport.py`, `server/mcp/client_capabilities.py` |

## Limits and operational notes

- Prefer `MCP_TOOLS_DEFAULT_TOOLSET=starter` for initialization to reduce
  startup schema payloads.
- Non-UI hosts should consume explicit `fallback` data and avoid retry loops
  that assume widget rendering is available.
- Treat `resource_link` content blocks as opt-in until host-specific evidence
  confirms support.
- Revalidate this matrix on every release that changes map tools, UI payload
  shape, or client capability negotiation.
