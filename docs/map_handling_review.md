# Map Handling Review and Cost Analysis (mcp-geo)

Date: 2026-01-28  
Branch: `sota-mcp`  
Scope: UI resource map handling + playground host + map proxy + map-related docs.

## Scope and artifacts reviewed

- UI map implementation: `ui/geography_selector.html`
- Playground host (UI sandbox/CSP, logging): `playground/src/App.svelte`
- Map proxy and style rewriting: `server/maps_proxy.py`
- UI resource CSP and permissions: `server/mcp/resource_catalog.py`
- Map tool + UI resource metadata: `tools/os_apps.py`
- Documentation: `README.md`, `CHANGELOG.md`, `docs/mcp_apps_alignment.md`

## Design and execution (documented)

### External dependencies and contracts

- OS Vector Tile API styles/tiles are accessed via `/maps/vector/vts/resources/styles` and tile endpoints, with `key` and `srs` query parameters. The proxy rewrites style URLs so MapLibre can load styles and tiles through the local server. [1]
- OS Places API supports WGS84 (EPSG:4326) output via `output_srs`, which is required for lon/lat MapLibre rendering of address points. [2]
- MapLibre requires a CSP-compatible worker when running under strict CSP/sandbox. The UI uses the CSP worker and adjusts CSP directives accordingly. [3]
- The OSM fallback uses OpenStreetMap tiles; the tile usage policy calls for appropriate usage and user-agent identification, and discourages heavy/uncached use. [4]

### Execution flow (high level)

1. Playground host loads the MCP UI resource (`ui://mcp-geo/geography-selector`) and injects CSP meta into the HTML if missing.
2. The UI initializes via `ui/initialize` and receives host context (proxy base, display mode, capabilities).
3. MapLibre is created with a CSP worker URL and a minimal fallback style.
4. When the map style loads, overlay sources (`boundaries`, `addresses`, `addresses-selected`) and layers are added.
5. Search requests trigger `os_places.*` calls and return addresses; the UI converts them to GeoJSON points and updates sources.
6. Focus boundaries are computed with `admin_lookup.*` calls and set as boundary GeoJSON.
7. Style changes (OS vector tiles vs OSM fallback) reset MapLibre style; overlay sources are re-applied post-load.

### Map data flow (in-repo responsibilities)

- `ui/geography_selector.html` owns map lifecycle, overlay source/layer management, and UI events.
- `server/maps_proxy.py` mediates OS Vector Tile API and OSM tiles, rewriting style URLs and forwarding tiles.
- `server/mcp/resource_catalog.py` declares CSP and permissions for the UI resource.

## Findings (ordered by severity)

### High

1) OSM tile proxy lacks caching and usage safeguards.  
   - `server/maps_proxy.py:315` forwards every OSM tile request to the public tile servers without caching or a contactable user agent string. OSM policy recommends responsible usage, which normally includes caching and an identifying user-agent/contact. [4]
   - Impact: Risk of throttling or policy violation; unpredictable tile load failures.  
   - Recommendation: Add HTTP caching, configurable tile provider, and a UA string with contact URL/email; consider a paid tile provider for heavier use.

2) Sandbox policy allows `allow-same-origin` + `allow-scripts` when requested by the UI resource.  
   - `playground/src/App.svelte:450` enables `allow-same-origin` if the resource asks for it. This combination can weaken iframe isolation and allow the UI to access the host origin.
   - Impact: Elevated XSS/data-leak risk if a UI resource is compromised.  
   - Recommendation: Default to `allow-scripts` only; gate `allow-same-origin` behind explicit user action or dev-mode flag, and document the risk.

### Medium

3) Focus-boundary enrichment is serialized and chatty.  
   - `ui/geography_selector.html:1555` loops addresses and calls `admin_lookup.containing_areas` and `admin_lookup.area_geometry` sequentially.  
   - Impact: Slow UI feedback, repeated network traffic, and susceptibility to rate limits or transient 5xx errors.  
   - Recommendation: Deduplicate by ID earlier, batch requests with `Promise.allSettled`, and cache results per session.

4) Overlay initialization depends on style timing without a queue.  
   - `ui/geography_selector.html:1172` and `:1274` ensure sources/layers on style load, but data updates can still race during style transitions.
   - Impact: Intermittent "missing source" errors and invisible overlays after style reloads.
   - Recommendation: Introduce a small event queue (pending overlay updates) and flush it on `style.load` once `sourcesReady` is true.

5) CSP allowlist is broader than current runtime needs.  
   - `server/mcp/resource_catalog.py:31` still allows direct `tile.openstreetmap.org` even though OSM tiles are now proxied through the server; the allowlist should match actual usage to minimize exposure.  
   - Impact: Over-broad CSP surface area, doc drift.  
   - Recommendation: Remove unused domains or document when direct access is required.

### Low

6) MapLibre worker dependency is pinned to a public CDN.  
   - `ui/geography_selector.html:979` uses a CDN-hosted CSP worker.  
   - Impact: External dependency risk (availability, integrity, CSP drift).  
   - Recommendation: Vendor the worker and serve it locally to reduce CSP allowances.

7) Diagnostics and debug state are split across two update paths.  
   - `updateDebugBadges` and `updateDiagnostics` are both used, but they can drift (timing differences on style transitions).  
   - Recommendation: Centralize diagnostic updates or route both through a single scheduler.

## Documentation validation (README + changelog)

- `CHANGELOG.md` contains the recent UI map/diagnostics work and the CSP worker change; it should include the new map proxy and security notes for sandboxing.
- `README.md` correctly states that the Svelte playground is served by Vite; it does not describe the map proxy or CSP worker usage.
- `docs/mcp_apps_alignment.md` still references direct `tile.openstreetmap.org` access; the runtime now proxies OSM tiles locally.

## Refactoring plan (recommended)

1) Extract a MapLibre adapter module:
   - Owns map init, style loading, and overlay source/layer lifecycle.
   - Exposes a small API: `setStyle`, `setAddresses`, `setBoundaries`, `setSelection`, `setOpacity`.

2) Introduce an async event queue for map mutations:
   - Buffer overlay updates while `style.load` is in-flight.
   - Flush on `style.load` and set `sourcesReady` deterministically.

3) Split UI concerns:
   - Move tool-call logic into a service module (`placesService`, `adminLookupService`).
   - Keep DOM rendering and selection logic in a controller layer.

4) Add tests:
   - Unit tests for style URL rewrite and proxy behavior.
   - Playwright integration for "search -> dots visible -> style switch -> dots still visible".

## Cost analysis (time and token estimate)

### Time (based on git history)

- Commit timeline on 2026-01-28 (UTC):
  - 09:54 -> 10:03 (0:08:45)
  - 10:03 -> 10:22 (0:18:38)
  - 10:22 -> 11:21 (0:58:47)
  - 11:21 -> 12:53 (1:32:02)
  - 12:53 -> 13:42 (0:48:58)
  - 13:42 -> 23:44 (10:02:44) *(uncommitted iteration window)*

- Total elapsed window (first commit -> current time): **13:49:54**.
- Active commit window (first -> last commit): **3:47:10**.

Interpretation:
- The interval after 13:42 suggests additional debugging and iterative attempts that did not land as commits. This is likely where the "failed attempts" were concentrated.

### Tokens (not directly measurable from repo)

- The repository does not contain token telemetry for the coding session.
- To compute token costs, the host must provide API usage logs (e.g., OpenAI usage records) or captured assistant logs with token counts.
- Suggested approach for future sessions:
  - Capture token usage at the client (per request/response) and store alongside the debug/audit log.
  - Record a session ID in the playground and attach it to MCP trace logs.

## Recommendations summary

- Add caching + usage safeguards to the OSM proxy (or swap to a paid tile provider).  
- Gate `allow-same-origin` behind a user-controlled toggle or dev flag.  
- Introduce a map update queue to avoid style/overlay races.  
- Vendor the CSP worker to reduce CSP surface and external dependency.  
- Align docs with the current proxy-based OSM flow.

## References

[1] https://docs.os.uk/mapping/vts/QGIS
[2] https://docs.os.uk/os-apis/accessing-os-apis/os-places-api/technical-specification/find
[3] https://maplibre.org/maplibre-gl-js/docs/guides/csp/
[4] https://operations.osmfoundation.org/policies/tiles/
