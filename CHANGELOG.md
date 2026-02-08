# Changelog

All notable changes to this project will be documented in this file.


## [Unreleased]
### Added
- Added `os_apps.render_ui_probe` to verify MCP-Apps UI rendering and content-mode support.
- Added `scripts/mcp_ui_mode_probe.py` to validate STDIO UI payload content types by mode.
- Added ONS dataset selection research pack under `research/ons_dataset_selection/`.
- Added `ons_select.search` for ranked ONS dataset selection with explainability prompts.
- Added `resource://mcp-geo/ons-catalog` and `resources/ons_catalog.json` as the local catalog index.
- Added `scripts/ons_catalog_refresh.py` to rebuild the ONS catalog index from the live API.
- Added related-dataset linking with comparability gating in `ons_select.search` when `includeRelated=true`.
- Added `resource://mcp-geo/os-catalog` and `resources/os_catalog.json` as the OS API + downloads catalog index.
- Added `scripts/os_catalog_refresh.py` to rebuild the OS catalog index from live OS API discovery.
- Added OS catalog snapshot + live validation tests (`tests/test_os_catalog_snapshot.py`).
- Added OS catalog live validation run report (v1): `docs/reports/os_catalog_live_run_2026-02-07.md` (timeouts observed).
- Added OS catalog live validation run report (follow-up): `docs/reports/os_catalog_live_run_2026-02-08.md`.
- Added `os_features.collections` to list NGD OGC API Features collections and return a latest-by-base mapping.
- Added `os_apps.render_boundary_explorer` (`ui://mcp-geo/boundary-explorer`) for boundary + inventory exploration.
- Added `os_map.inventory` and `os_map.export` to orchestrate bounded inventories and export snapshots as resources.

### Changed
- `nomis.datasets` now returns a bounded dataset summary by default (with `q` and `limit` support) to avoid large unfiltered payloads that can stall MCP clients.
- `nomis.datasets` now returns a compact summary for `dataset=<id>` lookups by default; full definitions require `includeRaw=true` to prevent oversized tool responses in Claude traces.
- `nomis.datasets` multi-term search now uses token scoring (with light synonym expansion for multi-word queries) so terms like `population census 2021` rank relevant datasets instead of relying on exact phrase matches.
- Statistics routing guidance now prioritizes direct `nomis.query`/`ons_data.query` comparison flows and explicitly advises filtered dataset discovery.
- STDIO now uses MCP `elicitation/create` for `os_mcp.stats_routing` comparison queries when clients advertise form elicitation support (`MCP_STDIO_ELICITATION_ENABLED=1` by default).
- `ons_select.search` now uses MCP `elicitation/create` over STDIO and Streamable HTTP when clients advertise form elicitation support (`MCP_STDIO_ELICITATION_ENABLED=1`, `MCP_HTTP_ELICITATION_ENABLED=1`).
- `os_mcp.stats_routing` now accepts optional `comparisonLevel` and `providerPreference` overrides and returns applied `userSelections`.
- Claude Desktop wrapper now keeps `MCP_APPS_RESOURCE_LINK` disabled by default (`0`) so `resource_link` blocks remain opt-in and avoid Claude “unsupported format” failures.
- Claude Desktop wrapper now defaults `MCP_APPS_CONTENT_MODE=embedded` so UI calls emit embedded `resource` blocks by default (safer than `resource_link` in current Claude behavior).
- MCP-Apps tools now support `MCP_APPS_CONTENT_MODE` to control UI content blocks (`resource_link`, embedded `resource`, or `text` only), and UI tool metadata now includes both nested `ui.resourceUri` and flat `ui/resourceUri` keys for compatibility.
- Trace proxy parsing now only attempts JSON decode on client/server JSON-RPC lines, reducing false parse errors from Docker/build stderr noise.
- Troubleshooting docs now include `parent_message_uuid` UUID failures as Claude host/session issues (not MCP server payload errors), with concrete recovery steps.
- Devcontainer PostGIS service now binds host port `5433` (instead of `5432`) to avoid conflicts with local PostgreSQL installs.
- `os_features.query` now returns `numberMatched` (and `numberReturned`) when provided by the upstream NGD features API, so clients can size queries before paging or exporting.

### Fixed
- `os_features.query` now uses OS NGD OGC API Features (`features/ngd/ofa/v1/collections/{collection}/items`) and supports basic paging via `limit` + `pageToken` (`nextPageToken` in responses).
- `os_linked_ids.get` now uses OS Linked Identifiers (`search/links/v1/identifierTypes/{identifierType}/{identifier}`) with optional identifier type inference.
- `os_vector_tiles.descriptor` now emits the correct upstream tile template (`/vts/tile/{z}/{y}/{x}.pbf`).
- OS catalog NGD per-collection item probes now use a small bbox to avoid timeouts in dense areas.

### Tests
- Added NOMIS dataset summary/filter/limit coverage and strengthened stats-routing comparison assertions.
- Added STDIO elicitation tests (accept/cancel/unavailable + wire round-trip) and stats-routing input validation coverage.
- Added STDIO + HTTP Streamable elicitation coverage for `ons_select.search`.
- Expanded evaluation coverage for ONS dataset selection and catalog validation.
- Expanded live ONS catalog validation to check all datasets with throttling/backoff controls.
- Live ONS catalog tests now validate entry fields and surface timeout/error summaries.

## [0.2.11] - 2026-02-06
### Added
- Added admin lookup level filtering, match modes, and live fallback for cache search.
- Added NOMIS query error detection for non-JSON and upstream error payloads.
- Added stats routing guidance for comparisons and small-area caveats.
- Added STDIO schema normalization for sanitized tool names and UI fallbacks for stats dashboard.

### Changed
- Prioritized admin lookup search ordering to reduce noisy LSOA matches for town queries.
- Updated tool search prompt guidance to favor `os_mcp.route_query` and level-filtered admin lookups.
- MCP-Apps render tools now include `resourceUri` + `uiResourceUris` + `_meta.ui.resourceUri`; `resource_link` content blocks are now opt-in via `MCP_APPS_RESOURCE_LINK` to avoid unsupported format warnings in Claude.
- Log MCP client capabilities during initialize for UI debugging (stdio + HTTP).

### Tests
- Added coverage for admin lookup level filtering and NOMIS query error handling.
- Expanded evaluation harness coverage for NOMIS tooling and stats routing.
- Added coverage for NOMIS client error handling, admin cache fallback, and stdio UI fallbacks.

## [0.2.10] - 2026-02-05
### Added
- Added `mcp-geo` stdio profile in `mcp.json` with MCP-Apps UI env defaults.
- Added full specification documentation package under `docs/spec_package/`.
- Added OSM-backed static map render endpoint and wiring for `os_maps.render`.
- Added data resources for boundary manifest, cache status, and ONS cache entries.
- Added upstream circuit breaker with jittered retries.
- Added `CONTEXT.md` as the durable Codex context template for this repo.
- Added Codex Mac app guidance and external references in `CONTEXT.md`.
- Added README note for Codex Mac app usage and context.
- Added trace session runner (`scripts/trace_session.py`) and artifact reporter (`scripts/trace_report.py`) for Claude debugging workflows.
- Added Claude Desktop local wrapper script for PostGIS + cached STDIO runs (`scripts/claude-mcp-local`).
- Added OpenAI widget metadata and configurable widget domain for ChatGPT Apps compatibility.
- Added NOMIS tools (`nomis.datasets`, `nomis.concepts`, `nomis.codelists`, `nomis.query`) for labour/census stats.
- Added `os_mcp.stats_routing` to explain NOMIS vs ONS routing decisions.

### Changed
- Relaxed boundary validation to treat pre-repair invalid geometries as warnings.
- Tuned `.dockerignore` to keep large data/logs out of Docker build context.
- Updated `docs/vendor/mcp/repos/ext-apps` submodule.
- Updated README and getting started docs for current ONS cache behavior.
- Updated PROGRESS.MD with documentation refresh.
- Persisted Codex home across devcontainer rebuilds and documented context workflow in AGENTS.
- Updated getting started and README docs for Claude local wrapper and ChatGPT HTTPS tunnel guidance.
- Added WGS84 → British National Grid conversion for `os_names.nearest`.
- `ons_data.query` now supports term-based auto-resolution and expands time ranges into discrete time queries.

### Fixed
- `os_names.nearest` now accepts WGS84 lat/lon and converts to British National Grid.
- `admin_lookup.area_geometry` now computes bbox from ArcGIS geometry when extent is missing.

### Tests
- Added coverage for map proxy, data resources, and circuit breaker behavior.

## [0.2.9] - 2026-02-01
### Added
- Cache audit tools (`admin_lookup.get_cache_status`, `admin_lookup.search_cache`) to inspect PostGIS boundary coverage.
- Latest report helper script (`scripts/latest_reports.py`) for boundary pipeline + cache status.
- Boundary run effectiveness tracker (`scripts/boundary_run_tracker.py`) with summary output and docs.
- Boundary pipeline selective retry flags (`--family`, `--variant`) and tracker baseline comparison.
- Post-run checklist mapping boundary pipeline validation errors to next actions in `docs/Boundaries.md`.
- Boundary cache status now reports dataset freshness metadata (`fresh`, `ageDays`).
- Boundary status ticker (`scripts/boundary_status_ticker.py`) for progress + error counts.
- Boundary validation triage helper (`scripts/boundary_triage.py`) with cause/fix mapping.
- Boundary auto-fix loop (`scripts/boundary_autofix.py`) to rerun failing families until stable.

### Changed
- Geography selector diagnostics now surface admin lookup status (live/partial/cache/all failed) and cache status panel.
- Boundary pipeline now retries multiple download candidates per variant and surfaces schema validation failures in pipeline status.
- Boundary manifest refreshed with NISRA download URLs and BUASD direct downloads; glossary added to boundary docs.
- Boundary manifest validation regex updated to match observed column names across ONS/NRS/NISRA/OS datasets.
- Boundary pipeline reports download/extract/table sizes; tracker summary now totals byte counts.
- Boundary manifest validation overrides updated for NI LGD fallback + TTWA duplicate codes.

### Fixed
- Admin lookup live calls now tolerate per-source failures and return partial results when available.
- latest_reports helper now warns when lowercase boundary cache env vars are set.
- latest_reports helper now emits cache-disabled guidance and suppresses noisy loguru warnings.
- latest_reports helper now reports cache query failures with a clear hint.
- latest_reports helper now prints cache status hints inline.
- Boundary cache optional deps now include psycopg for PostGIS connectivity.

### Tests
- (none)

## [0.2.8] - 2026-01-30
### Added
- PostGIS boundary cache module with schema + ingestion helper for admin boundaries.
- Boundary cache documentation and environment configuration guidance.
- Boundary ingestion pipeline script driven by `docs/Boundaries.json` + completion checklist.
- Optional `boundaries` dependency set for ingest tooling (pyogrio/pandas/pyproj/shapely).

### Changed
- admin_lookup now prefers local boundary cache when enabled and accepts an optional zoom hint.
- Geography selector now sends map zoom for boundary fetches and handles GeoJSON boundaries.
- Boundary ingest pipeline now refines CKAN title searches and filters to geospatial resources.

### Fixed
- Map proxy now adds CORS headers for map assets to support ui:// (null-origin) fetches.
- Boundary ingest pipeline now handles multi-file archives, ArcGIS Hub pending downloads, and skips non-polygon layers safely.

### Tests
- Fixed Playwright geography selector spec ESM path handling.
- Added admin_lookup boundary cache coverage.

## [0.2.7] - 2026-01-29
### Added
- Playground debug tab with runtime snapshot, HMR status, and redacted logs.
- MCP prompts list/get backed by evaluation prompt examples.
- Geography selector diagnostics panel with source/render counts and coordinate ranges.
- Geography selector diagnostics now include map/tile loaded state and in-view counts.
- Map handling review report at `docs/map_handling_review.md`.

### Changed
- Documented that the Svelte playground is served by Vite and `playground/app.py` is legacy.
- Playground request logging now records redacted summaries for debugging.
- Playground audit history now scrubs secrets from URLs and headers.
- Playground debug tab now surfaces a secret audit indicator.
- Geography selector debug badges now show card counts, layer visibility, and MapLibre status.
- Geography selector overlay initialization now waits for style readiness.
- Geography selector now uses MapLibre CSP worker for sandboxed hosting.
- Geography selector now reports the active MapLibre worker URL in diagnostics.
- Geography selector diagnostics now include source load status and last source event.
- Geography selector now proxies OSM raster tiles through the server for CSP-safe loading.
- Geography selector no longer adds the unused highways overlay layer.
- Geography selector now guards against missing overlay sources after style reloads.
- Geography selector overlay checks now include the selected-addresses layer.
- Geography selector diagnostics now update on map load and style load events.
- Geography selector address selection now fly-to centers on the clicked address.
- Geography selector redacts secrets from MapLibre error messages and avoids adding OS keys to non-vector proxy requests.
- OSM tile proxy now caches tiles and supports configurable base URL + contactable user agent settings.
- Playground sandbox now requires explicit allow-same-origin opt-in outside dev mode.
- Geography selector now batches focus-boundary lookups and caches admin results per session.
- Geography selector now queues overlay updates during style transitions to avoid missing sources.
- Geography selector CSP allowlist now removes unused direct OSM tile domains.
- Geography selector now serves the MapLibre CSP worker locally via the map proxy.
- Geography selector diagnostics now refresh through a single scheduled updater.
- Geography selector map operations now route through a MapLibre adapter module.
- Geography selector now flushes map overlay mutations through an async queue after style loads.
- Geography selector now routes tool calls through places/admin lookup service helpers.

### Fixed
- Playground connect button now disables when connected.
- Playground UI bridge now honors JSON-RPC id `0` and logs unsupported methods.
- Playground tool-call logging failures no longer mask successful tool responses.
- MCP prompts/list no longer returns method-not-found for the playground.
- Geography selector boundary fallback now retries without geometry on 5xx.

### Tests
- Added prompt and tool-search validation coverage to restore 90% gate.
- Added map proxy unit coverage and a geography selector style-switch Playwright flow.

## [0.2.6] - 2026-01-27
### Added
- Archived the original build backlog in `docs/build_initial_version.md`.
- Devcontainer image now bundles `ngrok` for HTTPS tunneling during ChatGPT connector setup.
- MCP Apps alignment note at `docs/mcp_apps_alignment.md`.
- Live API capture test with PostgreSQL/PostGIS logging for upstream responses.
- Devcontainer now provides a PostGIS service for live API capture runs.
- Claude UI fallback plan tracking in `PROGRESS.MD`.
- Inspector setup and getting started guide at `docs/getting_started.md`.
- Protocol helper for exposing MCP protocol version/transport metadata.
- HTTP/STDIO support for `resources/templates/list` (empty list for now).
- Dataset cache scaffolding for full ONS responses (`ONS_DATASET_CACHE_*`).
- JSON logging config with redaction-aware sink + upstream error classification.
- Svelte + Vite playground UI scaffold with MCP SDK client.
- Playground event + evaluation endpoints (`/playground/events`, `/playground/evaluation/latest`).
- Playwright smoke test for the playground UI.
- CORS configuration for browser clients (playground).
- OS Vector Tile API Stylesheets git submodule for map style references.
- Evaluation questions for `ons_data.editions` and `ons_data.versions`.
- Coverage config to omit the map proxy module from unit coverage.
- OS API key auth error classification (missing/invalid/expired).

### Changed
- `docs/Build.md` now documents the current install/run/test workflow and endpoints.
- `docs/review_codex_in_container.md` now references the Python toolchain and `pytest -q` for verification.
- Devcontainer base packages now include `curl` to support installing tunnel helpers.
- Docker image defaults `ONS_LIVE_ENABLED=true` so live ONS calls are available without extra flags.
- MCP-Apps UI negotiation now uses the `io.modelcontextprotocol/ui` extension only; skybridge/OpenAI Apps fallback removed.
- MCP-Apps HTML views now use the JSON-RPC `ui/initialize` handshake and notifications.
- STDIO/HTTP tool results no longer inject `uiResourceUris` or UI resource links; hosts read `_meta.ui.resourceUri` from tool metadata.
- OS Names and OS Places requests now ask for WGS84 output to improve coordinate availability.
- admin_lookup tools now query live ONS Open Geography (ArcGIS) services by default.
- ons_search now targets the live ONS beta dataset search API when enabled.
- os_apps tool descriptors now use `_meta.ui.resourceUri` only; tool responses keep structured content fields for MCP Apps hosts.
- MCP descriptor now reports protocol version and current transport (http/stdio).
- Live-only ONS/admin tools now require live mode; sample resources removed from MCP resource list.
- Devcontainer now installs playground dependencies (Svelte app).
- Devcontainer now installs Playwright browsers for playground tests.
- Playground build docs now include Playwright dependency install step.
- ONS codes tool paginates live options and persists cached snapshots on disk.
- Vector tile style selection now uses OS VTS style names (OS_VTS_3857_*) via the `style` query parameter.
- OS-backed tools now return explicit auth errors for missing/invalid/expired keys.

### Fixed
- Docker MCP config no longer suppresses live ONS mode when `ONS_LIVE_ENABLED` is unset.
- admin_lookup hints now surface when the bundled sample has no matching area names.
- Vector tile style proxy now resolves OS VTS style endpoints and rewrites style JSON beyond `.json` paths.

### Tests
- Added coverage for MCP-Apps UI capability detection defaults (stdio/http).
- Added live admin lookup + ArcGIS client branch coverage.
- Added ONS search fallback/live edge-case coverage and cache eviction tests.
- Added evaluation harness coverage test that exercises every registered tool.
- Updated resource and ONS tool tests to match live-only behavior and new descriptor metadata.
- Added ons_data live filter/get_observation coverage.
- Added resource, tool search, and stdio adapter tests to meet coverage gates.
- Added OS API key auth classification coverage.

## [0.2.5] - 2026-01-21
### Added
- Native `/mcp` Streamable HTTP JSON-RPC endpoint for MCP clients (ChatGPT, Inspector).
- HTTP trace proxy `scripts/mcp_http_trace_proxy.py` for capturing /mcp traffic.
- Vendor snapshot tooling (`scripts/vendor_fetch.sh`, `scripts/vendor_html_nojs.py`, `scripts/vendor_package.sh`) and storage policy (`docs/vendor/README.md`).
- Placeholder OpenAI doc stash under `docs/vendor/openai/` for ChatGPT connector references.
- HTTP MCP tests covering initialize, tools/list, tools/call, and resources/read.
- Local OS map demo server `scripts/claude_serve_map.py`.

### Changed
- README/tutorial/ChatGPT setup updated for `/mcp` usage and HTTP trace proxy flow.
- Vendor docs now keep snapshots out of git and recommend release artifacts for HTML bundles.

### Fixed
- (none)
- Settings now ignore unexpected environment keys to avoid startup failures when stray vars are present.

## [0.2.4] - 2026-01-21
### Added
- Preview spec tracking log (`docs/spec_tracking.md`) and enforcement in agent instructions.
- Static map fallback metadata for `os_apps.render_geography_selector` when UI is unsupported (stdio).

### Changed
- README notes MCP spec preview tracking and MCP-Apps fallback behavior.

### Fixed
- (none)

## [0.2.3] - 2026-01-21
### Added
- MCP stdio trace proxy `scripts/mcp_stdio_trace_proxy.py` for JSON-RPC traffic capture.
- UI interaction logging tool `os_apps.log_event` with `UI_EVENT_LOG_PATH`.
- Client tracing guide `docs/client_trace_strategy.md` covering MCP + UI logs.
- Dockerfile + `.dockerignore` for containerized STDIO usage, plus Docker client config docs.

### Changed
- Geography selector MCP-App emits UI interaction events for tracing.

### Fixed
- STDIO adapter auto-detects JSON line framing vs Content-Length to avoid client parse errors.
- STDIO initialize response now includes protocol version and server info with spec-style capabilities.
- STDIO tool names normalized to Claude-compatible pattern while still accepting original dotted names.
- `ons_data.create_filter` no longer marked read-only in tool annotations.
- STDIO adapter now accepts `arguments` payloads for `tools/call` (MCP spec compatibility).

## [0.2.2] - 2026-01-20
### Breaking
- Health check endpoint renamed to `/health` (was `/healthz`).

### Added
- Evaluation framework (question suite, rubric, harness, audit logs) and `docs/evaluation.md`.
- Tool search endpoint `/tools/search` and stdio `tools/search` with annotations and `deferLoading`.
- `os_mcp.descriptor` and `os_mcp.route_query` for tool discovery and routing.
- MCP-Apps UI resources with MapLibre geography selector and progressive disclosure UI.
- Skills resource `skills://mcp-geo/getting-started`.
- Tool catalog generator and `docs/tool_catalog.md`.
- Troubleshooting guide and expanded examples.
- ONS filter output CSV/XLSX formats.
- Tutorial expanded with multi-client setup and MCP-Apps/tool search walkthrough.

### Changed
- STDIO adapter moved to `server/stdio_adapter.py` with legacy wrapper retained.
- OS Places tools now request WGS84 output; `os_places.within` supports oversized bbox tiling/clamping.
- `mcp.json` server entries renamed to `mcp-geo-stdio` / `mcp-geo-http`.

### Fixed
- OS Places WGS84 coordinate handling for `nearest`/`within` to avoid BNG coverage errors.
- Non-200 OS API responses normalized to 501 error envelopes for consistency.
- JSON-RPC invalid params handling for non-dict `params`.

### Tests
- Added routing, MCP-Apps, tool search, and STDIO error branch coverage.
- Added OS Places bbox tiling/clamping tests and evaluation harness coverage.

## [0.2.1] - 2025-09-17

### Added
- STDIO adapter: `resources/read` parity enhancements (pagination + filtering retained) now include weak ETag generation and conditional `ifNoneMatch` support returning `{ "notModified": true }` short result.
- STDIO adapter: `resources/describe` method returning resource metadata (name, description, license).
- Client: REPL mode (`--repl`) and generic JSON param parsing for any method.
- Client: Skips initial log notifications automatically.
- Client: `--if-none-match <etag>` convenience flag for conditional `resources/read`.

### Changed
- Resource responses over STDIO now include `etag` field when not modified conditions are not met.
- Internal refactor: centralized ETag computation helper in adapter.

### Fixed
- STDIO tests updated to tolerate initial log frames preventing spurious KeyError on first read.

## [0.2.0] - 2025-09-17

### Added
- Epic A: Core MCP server (health, tools list/call/describe, resources list, transcript endpoint, error handler, logging with correlation IDs, devcontainer & Docker setup).
- Epic B: OS tooling with real handlers (conditional on `OS_API_KEY`):
  - `os_places`: search, by_postcode, by_uprn, nearest, within
  - `os_names`: find, nearest
  - `os_features.query`
  - `os_linked_ids.get`
  - `os_maps.render` (descriptor stub)
  - `os_vector_tiles.descriptor`
- Epic C (partial): `admin_lookup.containing_areas`, `admin_lookup.reverse_hierarchy`, `admin_lookup.area_geometry`, `admin_lookup.find_by_name` using bundled sample boundary resource.
- Dynamic tool import mechanism in `server/mcp/tools.py` ensuring registry population in all execution contexts.
- High coverage (>90%) test suite including validation, success, and upstream error normalization paths.
- Epic D: statistical integration foundations:
  - `ons_data.query` tool with sample observations + filters + pagination.
  - `ons_observations` resource (pagination + ETag + provenance + filters geography/measure with variant ETag).
  - ONS client scaffold (`ONSClient`) with TTL caching and pagination helper.
  - Live ONS integration path for `ons_data.query` (dataset/edition/version) gated by `ONS_LIVE_ENABLED`.
  - `ons_data.dimensions` tool (sample & live modes) including live version metadata fetch + per-dimension options and single-dimension optimization.

### Changed
- Unified retry + error normalization via shared OS client (`os_common.OSClient`).
- Settings migrated to Pydantic v2 style (removed deprecated inner `Config`).
- README overhauled with testing & contributing guidance.

### Fixed
- Upstream TLS / connect / timeout failures for `os_places.by_postcode` mapped to explicit codes (`UPSTREAM_TLS_ERROR`, `UPSTREAM_CONNECT_ERROR`).
- Added certificate bundle assurance in container for reliable SSL.
- Removed duplicate Epic listings & inconsistent changelog categories.

## [0.1.0] - 2025-08-20
- Project bootstrapped with core MCP endpoints and infra
