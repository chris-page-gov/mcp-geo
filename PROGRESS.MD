# MCP Geo Progress

This file tracks how the implementation compares to the original proposal and
later documentation as the MCP specification evolved.

Last updated: 2026-02-14

## Sources reviewed

Original proposal and supporting notes:
- docs/Mapping Ordnance Survey & ONS APIs to the Model Context Protocol (MCP).docx
- docs/Mapping Ordnance Survey & ONS APIs to the Model Context Protocol (MCP).pdf
- docs/Documentation collection task.docx
- docs/Working with MCP Servers.docx

Evolving spec and repo-aligned docs:
- docs/build_initial_version.md
- docs/Build.md
- docs/spec_tracking.md
- docs/mcp_apps_alignment.md
- docs/tutorial.md
- docs/evaluation.md
- docs/tool_catalog.md
- docs/examples.md
- docs/client_trace_strategy.md
- docs/ChatGPT_setup_chat.md
- docs/review_codex_in_container.md
- docs/troubleshooting.md
- README.md

## Active implementation plan (2026-02-13)

Reference plan:
- `/Users/crpage/repos/mcp-geo/docs/reports/os_catalog_gap_implementation_plan_2026-02-13.md`

Legend: pending, in_progress, done

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| WS-INT-0 Contract freeze + shared scaffolding | done | none | Added shared delivery contract/config and resource scaffolding (`os_delivery`, OS cache/exports resources). |
| WS-CAT-1 Catalog gap closure | done | none | Added OFA/OS Net/Downloads roots, OFA queryables, and explicit Road+Outdoor ZXY probes in refreshed catalog. |
| WS-DL-2 OS Downloads tool family | done | WS-INT-0 | Implemented `os_downloads.*` with inline/resource/auto delivery and export lifecycle support. |
| WS-SEARCH-3 Places + Linked IDs closure | done | none | Added `os_places.radius`, `os_places.polygon`, and linked identifier extra paths. |
| WS-MAP-4 Raster + WFS capabilities | done | WS-INT-0 | Added WMTS/ZXY raster tools and WFS/WFS archive capabilities with delivery controls. |
| WS-POS-5 OTA + OS Net tooling | done | WS-INT-0 | Added NGD OTA discovery tools and OS Net station/log/RINEX tools. |
| WS-QGIS-6 QGIS linkage tools | done | WS-MAP-4, WS-POS-5 | Added `os_qgis.vector_tile_profile` and `os_qgis.export_geopackage_descriptor` with inline/resource/auto delivery and QGIS style/export descriptors. |
| WS-OBS-7 Observability coverage | done | WS-DL-2, WS-MAP-4 or WS-POS-5 | Added auto-delivery resource-fallback metric and structured OS download export lifecycle logs (`requested`, `queued`, `completed`, `failed`). |
| WS-DOC-8 Documentation closure | done | WS-CAT-1 and feature streams | Updated planning/status docs and endpoint coverage notes to match implemented streams. |
| WS-INT-9 Final integration + regression | done | all workstreams | Integrated registrations/resources and passed full regression (`pytest -q --cov-report=term-missing:skip-covered`: 683 passed, 6 skipped, 90.16% coverage). |

## Map delivery interoperability research (2026-02-13)

Legend: pending, in_progress, done

| Step | Status | Notes |
| --- | --- | --- |
| MDR-01 Define personas and journey requirements for map delivery | done | Added research persona/journey pack covering public, analyst, GIS, engineering, and accessibility-first users. |
| MDR-02 Build containerized autonomous trial harness | done | Added `scripts/run_map_delivery_trials.sh`, multi-browser Playwright trial config/specs, and structured evidence logs/screenshots. |
| MDR-03 Validate MCP server connectivity in devcontainer | done | Captured in-container baseline (`/health`, `initialize`, `os_maps.render`, `os_vector_tiles.descriptor`) with reproducible logs. |
| MDR-04 Execute and evaluate map rendering trials | done | Final clean run: 8 passed, 4 skipped; generated trial summary report and artifacts. |
| MDR-05 Produce detailed report and external source register | done | Added full report set in `research/map_delivery_research_2026-02/` including options, trial methodology/results, recommendations, and source register. |

## Map delivery recommendations implementation plan (2026-02-14)

Reference plan:
- `/Users/crpage/repos/mcp-geo/docs/reports/map_delivery_recommendations_implementation_plan_2026-02-14.md`

Legend: pending, in_progress, done

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| MDR-I1 Canonical `os_maps.render` baseline docs | done | none | Updated README/getting-started/examples/tutorial docs to lead map workflows with `os_maps.render` and explicit fallback ordering. |
| MDR-I2 Standard fallback skeleton contracts | done | MDR-I1 | Added `map_card`, `overlay_bundle`, and `export_handoff` schemas plus conformance checklist in spec package + alignment docs. |
| MDR-I3 Lean startup tool discovery guidance | done | MDR-I1 | Standardized `starter`-first startup guidance and post-init scoped discovery in onboarding/troubleshooting docs. |
| MDR-I4 Browser/widget support matrix | done | MDR-I1 | Published `docs/map_delivery_support_matrix.md` with capability modes, env toggles, verification dates, and evidence links. |
| MDR-N1 Deterministic host simulation utilities | done | MDR-I2, MDR-I4 | Added deterministic host-capability fixtures + reusable simulation utilities and replay-matrix script for multi-engine trial runs. |
| MDR-N2 Widget-unsupported guidance fields | done | MDR-I2 | Extended fallback payloads with explicit guidance keys (`widgetUnsupported`, reason, degradation mode, preferred next tools) and transport-parity tests. |
| MDR-N3 Mobile viewport + latency trial budgets | done | MDR-N1 | Added mobile Playwright trial projects and latency-budget assertions with percentile/compliance reporting in trial summaries. |
| MDR-N4 Optional sidecar deployment profile | done | MDR-I2 | Added Martin/pg_tileserv optional sidecar compose/smoke assets and architecture/system/walkthrough runbook updates. |
| MDR-M1 PMTiles/MBTiles offline delivery | done | MDR-N4 | Added `os_offline.descriptor`/`os_offline.get`, offline pack catalog/resources, and offline handoff contracts for PMTiles/MBTiles paths. |
| MDR-M2 Map output quality checks | done | MDR-N3 | Added automated map quality checker (contrast, label-density proxy, accessibility metadata, waiver handling) with report artifacts. |
| MDR-M3 Notebook scenario pack resources | done | MDR-N3 | Added notebook scenario-pack export script and `resource://mcp-geo/map-scenario-packs*` resources with provenance/hash metadata. |
| MDR-E1 MCP/AI-host best-practice bundle | pending | MDR-I4 | Publish worker/CSP-safe client-side best-practice patterns for embedded map contexts. |
| MDR-E2 Lightweight embedding style profiles | pending | MDR-E1 | Provide normalized lightweight style profiles for constrained AI-client embedding. |
| MDR-E3 Progressive fallback official examples | pending | MDR-E1, MDR-E2 | Publish examples showing deterministic full-vector to static-card fallback progression. |
| MDR-E4 Mixed UI/no-UI host guidance | pending | MDR-E1 | Publish predictable degradation guidance for mixed host fleets. |

## Progress against the original vision

Legend: Done, Partial, Not started

| Area | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Core MCP server (tools/resources/health) | Done | server/main.py, server/mcp/*, docs/Build.md | Includes /tools/list, /tools/call, /resources/read, /mcp JSON-RPC. |
| STDIO adapter | Done | server/stdio_adapter.py, scripts/os-mcp, tests/test_stdio_* | JSON-RPC 2.0 with framing auto-detect. |
| Tool registry + dynamic imports | Done | server/mcp/tools.py, tools/registry.py | Explicit module import loop. |
| OS Places (geocoder) | Done | tools/os_places.py, docs/examples.md | search/by_postcode/by_uprn/nearest/within implemented. |
| OS Names (gazetteer) | Done | tools/os_names.py | find + nearest. |
| OS Linked Identifiers | Done | tools/os_linked_ids.py | Supports identifier lookups plus `identifiers`, `feature_types`, and `product_version_info` surfaces. |
| OS Features (NGD / OGC Features) | Partial | tools/os_features.py | Supports bbox or polygon queries, attribute filters, resultType hits, field projection, sorting, queryables fetch, collections listing/latest mapping, plus WFS and WFS archive capabilities. Feature-by-id and CRS options still pending. |
| OS Maps (render) | Partial | tools/os_maps.py, server/maps_proxy.py | Static map proxy URL plus overlay-ready render contract delivered, with WMTS capabilities and raster ZXY tile retrieval. Full end-to-end client rendering orchestration still pending. |
| OS NGD Tiles (OTA) | Done | tools/os_tiles_ota.py | Added OTA discovery surfaces: collections, tilematrixsets, conformance. |
| OS Downloads API | Done | tools/os_downloads.py | Added product/download listing plus export prepare/get with resource-backed delivery. |
| OS Net API | Done | tools/os_net.py | Added RINEX years, station metadata, and station log retrieval with delivery controls. |
| OS Vector Tiles | Done | tools/os_vector_tiles.py | Descriptor tool present. |
| ONS data query + filters | Partial | tools/ons_data.py, tools/ons_codes.py | Live mode required; ons_codes supports on-disk cache; `ons_data.get_filter_output` now supports resource-backed export delivery for large outputs (`delivery=resource|auto`) with `resource://mcp-geo/ons-exports/*` artifacts. |
| ONS dataset search | Done | tools/ons_search.py | Live search only; no sample fallback. |
| NOMIS statistics | Partial | tools/nomis_data.py, tests/test_nomis_data.py, resources/nomis_workflows.json | Discovery/query tools working; fixed concept/codelist endpoints and improved GSS→NOMIS geography resolution (OA/LSOA/MSOA/ward). Added dataset-specific workflow profiles resource and routing guidance link-up; broader profile depth can still be expanded. |
| Admin geography lookup | Partial | tools/admin_lookup.py, server/boundary_cache.py | Live ArcGIS path plus optional PostGIS cache; level filtering + match modes added; cache search fallback transparency now includes fallback reasons and cache maturity snapshots, and cache status exposes staleness metadata. |
| Boundary ingest pipeline | Done | scripts/boundary_pipeline.py, docs/Boundaries.json | Full ingest + validation completes with ArcGIS Hub polling; run report recorded. |
| Static resources (code lists, boundaries) | Partial | server/mcp/resource_catalog.py, resources/, scripts/pack_cache_refresh.py | Boundary/code-list hybrid fetch-cache manifests + indexes are now exposed (`boundary-pack-sources`, `code-list-pack-sources`, `boundary-packs-index`, `code-list-packs-index`); full pack acquisition depends on refresh runs and source availability. |
| Conversational normalization | Done | tools/os_mcp.py, tests/evaluation/* | `route_query` + descriptor for tool discovery, plus `os_mcp.select_toolsets` for post-init discovery filter selection. |
| Stats routing diagnostics | Done | tools/os_mcp.py | Added stats routing explainer tool. |
| Evaluation harness / coverage matrix | Done | tests/evaluation/*, docs/evaluation.md | Question suite + rubric + harness; live capture optional. |
| Playground UI for developers | Partial | playground/, server/mcp/playground.py | New Svelte playground scaffold; still needs UI resource rendering + evaluation orchestration. |
| MCP-Apps UI widgets | Done | tools/os_apps.py, docs/mcp_apps_alignment.md | Aligned to MCP Apps extension (no OpenAI Apps SDK fallback). |
| Observability (logs/metrics) | Partial | server/main.py, server/logging.py | JSON log sink and upstream error logging added; metrics remain basic. |
| Rate limiting + error model | Done | server/main.py, server/config.py | 429 handling + uniform error envelope. |
| CI/CD pipeline | Not started | docs/build_initial_version.md | No GitHub Actions pipeline committed. |

## Additional API coverage from the documentation collection task

The documentation collection identifies extra OS and ONS services beyond the
core tools. Current implementation coverage is:

- OS Net API (GNSS / RINEX data): implemented via `os_net.rinex_years`, `os_net.station_get`, and `os_net.station_log`.
- OS Downloads API: implemented via `os_downloads.*` list/get/export tools.
- OS Match & Cleanse API: not implemented.
- OAuth2 flow for OS APIs: not implemented (API key only).
- Points of Interest / POI APIs: implemented via `os_poi.search`, `os_poi.nearest`, and `os_poi.within`.
- Full ONS Open Geography linked data API: not implemented (ArcGIS live lookup is used instead).

## Spec evolution milestones captured in the repo

- Streamable HTTP `/mcp` endpoint added for MCP clients.
- MCP-Apps UI support aligned to finalized ext-apps spec (JSON-RPC `ui/initialize`, no skybridge).
- Tool search (`/tools/search`) plus routing tool (`os_mcp.route_query`).
- Default startup toolset filters for discovery (`MCP_TOOLS_DEFAULT_*`) so
  clients that call `tools/list` without filters can receive a curated subset
  (for example `starter`) instead of the full tool schema set.
- Initialize-time capability/protocol summaries now emit in STDIO/HTTP logs for
  auditability, and `os_mcp.select_toolsets` can use MCP form elicitation as a
  post-init discovery step in both transports.
- Conditional resources with weak ETags and `If-None-Match` support.
- STDIO adapter compatibility adjustments (arguments/params, name normalization).
- OS API auth failures now classified into missing/invalid/expired key errors.

## Outstanding work (from original proposal + newer docs)

High impact
- Expand OS Features to support attribute filters, polygons, and collection listing.
- Ship real boundary resources (wards, LSOA/MSOA, LAD, etc.) with paging + metadata.
- Finish the playground UI (UI resource rendering + evaluation harness orchestration).
- Provide OAuth2 support for OS APIs where required.

Medium impact
- Add OS Match & Cleanse tooling if still in scope.
- Replace map render descriptor stub with a real rendering or proxy service.
- Expand ONS data export (streaming CSV/XLSX) and add more live dataset coverage.
- Implement ONS dataset selection optimization (catalogue index, ranking, explainability, elicitation).
- Improve observability: structured JSON logs, latency histograms, request/response size metrics.
- Add CI pipeline (lint, type, tests, coverage, build image).

Low impact
- Add golden fixtures for canonical postcodes and feature queries.
- Enrich resource catalog with fuller code lists and provenance metadata.
- Expand boundary cache coverage (ingest official datasets at multiple resolutions).

## Completion program tracker (2026-02-11)

Legend: pending, in_progress, done

| Seq | Commit | Status | Notes |
| --- | --- | --- | --- |
| C00 | `chore(program): add phased completion tracker for open progress items` | done | Tracker added and unreleased changelog seeded. |
| C01 | `feat(ons-select): implement full comparability gating rules` | done | Added strict geography/time/revision/denominator gating and richer related-dataset explainability/provenance fields. |
| C02 | `test(ons-select): add catalog validation harness coverage` | done | Added reusable catalog validator script/module, validator tests, and evaluation questions for catalog/comparability assertions. |
| C03 | `feat(ui-fallback): centralize client capability gating across transports` | done | Shared capability/fallback helpers now drive both stdio and HTTP, including consistent statistics-dashboard fallback selection. |
| C04 | `test(ui-fallback): add end-to-end host render verification` | done | Added Playwright host-render tests for UI-capable host, non-UI fallback payloads, and sanitized/dotted tool-name render calls. |
| C05 | `feat(tool-naming): complete sanitized-only naming policy with alias resolution` | done | HTTP discovery endpoints now emit sanitized names first, include `annotations.originalName`, and accept sanitized+dotted aliases for calls/describe. |
| C06 | `feat(toolsets): expose named toolsets and include/exclude filters` | done | Added named toolsets (Google toolkit-style grouping) plus include/exclude filters across HTTP `/tools/*` and MCP `tools/list|search`. |
| C07 | `feat(os-features): add polygon and attribute-filter query expansion` | done | `os_features.query` now supports polygon geometry, property filters, sort/projection, `resultType=hits`, and optional queryables metadata. |
| C08 | `feat(os-maps): complete overlays and interactive layer wiring` | done | `os_maps.render` now accepts overlay inputs/local layers, can hydrate from `os_map.inventory`, and returns overlay summaries + feature collections aligned to boundary explorer layer semantics. |
| C09 | `test(boundary-explorer): verify local GeoJSON and Shapefile.zip layer import` | done | Added Playwright coverage for GeoJSON and Shapefile.zip local-layer import plus polygon-driven selection highlighting against inventory UPRNs. |
| C10 | `feat(ons-export): implement streaming export pipeline` | done | Added `delivery=inline|resource|auto` on `ons_data.get_filter_output`, with resource-backed exports and stream metadata for large payload handling via `resource://mcp-geo/ons-exports/*`. |
| C11 | `feat(nomis): add dataset-specific workflow coverage and routing guidance` | done | Added `resource://mcp-geo/nomis-workflows` workflow profiles and surfaced this URI in NOMIS-routed `os_mcp.route_query` responses/guidance. |
| C12 | `feat(admin-cache): harden cache maturity and freshness behavior` | done | Boundary cache status now includes maturity/staleness sections; dataset freshness states are explicit, and admin cache fallback responses expose `fallbackReason` + cache maturity context. |
| C13 | `feat(resources): ship real boundary and code-list packs via hybrid fetch cache` | done | Added hybrid cache source manifests, pack index resources, and `scripts/pack_cache_refresh.py` to fetch/checksum/update cache-backed boundary/code-list pack indexes. |
| C14 | `feat(playground-observability): complete playground orchestration and richer metrics` | done | Added orchestration summary/reset endpoints, session-aware playground event/transcript tracking, and Prometheus metrics for per-tool latency/payload bytes/cache-hit/fallback plus playground counters. |
| C15 | `feat(os-poi): add OS POI tools and finalize backlog closure` | done | Added `os_poi.search`, `os_poi.nearest`, and `os_poi.within` with entitlement-safe OS error passthrough, toolset/category integration, route-query POI intent routing, and endpoint-contract test coverage. |
| C16 | `chore(release-readiness): final progress closure and full regression run` | done | Completed docs/status closure and full regression: `pytest -q` (90.26% coverage, 634 passed, 6 skipped) plus `npm --prefix playground run test` (6 passed). |

## Active implementation plan (2026-01-27)

| Step | Status | Notes |
| --- | --- | --- |
| Classify OS API key failures (missing/invalid/expired) | Done | OS client + map proxy now map auth errors. |
| Refresh docs + changelog for MCP-Apps alignment + key requirements | Done | README, Build, tutorial, troubleshooting, and release notes updated. |
| Cut 0.2.7 release | Done | Release cut on 2026-01-29 with map handling follow-ups. |

## Boundary cache rollout (2026-01-30)

| Item | Status | Notes |
| --- | --- | --- |
| Add PostGIS boundary cache + ingestion scaffolding | Done | server/boundary_cache.py, scripts/boundary_cache_* |
| Wire admin_lookup to cache with zoom-aware geometry | Done | tools/admin_lookup.py, ui/geography_selector.html |
| Document cache setup + validation | Done | docs/boundary_cache.md, docs/getting_started.md |
| Add post-run checklist for pipeline validation errors | Done | docs/Boundaries.md |

## Documentation refresh (2026-02-02)

| Item | Status | Notes |
| --- | --- | --- |
| Add full specification package | Done | docs/spec_package/* |
| Align README + getting_started with ONS cache behavior | Done | README.md, docs/getting_started.md |

## ONS dataset selection research (2026-02-07)

| Item | Status | Notes |
| --- | --- | --- |
| Add research pack under `research/ons_dataset_selection/` | Done | Includes report, taxonomy options, datapack schema, samples, linking rules, roadmap, evaluation plan. |
| Normalize SeeLinks references to MCP Geo | Done | Research pack now framed for MCP Geo usage. |
| Link research in README + changelog | Done | README section added; changelog updated. |

## Dataset selection optimization plan (2026-02-07)

| Step | Status | Notes |
| --- | --- | --- |
| Build cached ONS/Nomis catalogue resource | Done | Added `resource://mcp-geo/ons-catalog` with refresh script; placeholder catalog stored in `resources/ons_catalog.json`. |
| Build cached OS API/downloads catalogue resource | Done | Added `resource://mcp-geo/os-catalog` with refresh script; snapshot stored in `resources/os_catalog.json`. |
| Add selection ranking tool with explainability | Done | Added `ons_select.search` with scored candidates and elicitation prompts. |
| Add elicitation integration for ambiguous queries | Done | `ons_select.search` now uses MCP `elicitation/create` in stdio + Streamable HTTP when clients advertise form elicitation support. |
| Add comparability gating + related-dataset linking | Done | `ons_select.search` now enforces geography/time/revision/denominator safety gates, typed links, and provenance-rich related dataset edges. |
| Extend evaluation harness with selection tasks | Done | Added catalog-resource and comparability-focused `ons_select.search` evaluation scenarios plus validator-backed catalog coverage. |
| Add OS catalog live validation and run report | Done | Added `tests/test_os_catalog_snapshot.py` and report `docs/reports/os_catalog_live_run_2026-02-07.md` (notes timeouts/entitlement gaps). |

## Codex context persistence (2026-02-02)

| Item | Status | Notes |
| --- | --- | --- |
| Add durable repo context template | Done | CONTEXT.md |
| Update agent guidance to read/update repo context | Done | AGENTS.md |
| Persist Codex home across devcontainer rebuilds | Done | .devcontainer/devcontainer.json |
| Add Mac App guidance + external references | Done | CONTEXT.md |
| Add README note for Codex Mac app usage | Done | README.md |

## Map handling review follow-ups (2026-01-28)

| Item | Status | Notes |
| --- | --- | --- |
| Add OSM tile proxy caching + UA/contact + configurable base | Done | server/maps_proxy.py, server/config.py, .env.example |
| Gate allow-same-origin in playground sandbox | Done | playground/src/App.svelte |
| Parallelize + cache focus boundary enrichment | Done | ui/geography_selector.html |
| Add overlay update queue for style transitions | Done | ui/geography_selector.html |
| Tighten CSP allowlist for geography selector | Done | server/mcp/resource_catalog.py, docs/mcp_apps_alignment.md |
| Vendor MapLibre CSP worker locally | Done | ui/vendor, server/maps_proxy.py, ui/geography_selector.html |
| Centralize diagnostics + debug badge updates | Done | ui/geography_selector.html |
| Extract MapLibre adapter module | Done | ui/geography_selector.html |
| Introduce async map mutation queue | Done | ui/geography_selector.html |
| Split UI tool-call services from controller | Done | ui/geography_selector.html |
| Add map proxy + UI style switch tests | Done | tests/, playground/tests/ |

## Playground UI gap map (focus on MCP-Apps tools)

The Inspector covers tool discovery and execution, but it does not replace a
purpose-built playground for UI widgets. The table below captures what is still
missing if we want a dedicated playground experience.

| UI tool | What exists now | Playground gaps | Notes |
| --- | --- | --- | --- |
| os_apps.render_geography_selector | MCP-Apps widget resource and tool | Embed UI resource, capture selection context, and show how to pass selections into follow-on tool calls | Needs a state panel for selected areas. |
| os_apps.render_statistics_dashboard | MCP-Apps widget resource and tool | Embed UI, allow user to wire dataset/filters, show resulting `ons_data.*` calls | Needs read/write sync between UI and tool calls. |
| os_apps.render_feature_inspector | MCP-Apps widget resource and tool | Embed UI, show selected feature JSON and source tool calls | Needs GeoJSON preview and result drill-down. |
| os_apps.render_route_planner | MCP-Apps widget resource and tool | Embed UI, show chosen route geometry and parameters | Needs map viewport + geometry preview. |
| os_apps.log_event | Logs UI events to file | Surface events in a live panel with correlation to tool calls | Would unify with evaluation audit logs. |

Common playground capabilities still required:
- UI resource renderer that can load `ui://` resources with correct MIME type.
- Tool call builder with schema-driven forms (request + response panels).
- Context panel to track selections (areas, features, routes) across calls.
- Audit/log view to correlate tool calls with UI events and trace logs.

## Stats routing elicitation rollout (2026-02-06)

| Item | Status | Notes |
| --- | --- | --- |
| Add stdio MCP elicitation support for comparison stats routing | Done | `server/stdio_adapter.py` now issues `elicitation/create` when clients advertise form elicitation capability and query looks comparative. |
| Apply elicitation selections to routing guidance | Done | `tools/os_mcp.py` accepts `comparisonLevel` and `providerPreference`, returns `userSelections`, and adjusts recommendations accordingly. |
| Add direct + round-trip tests | Done | Added helper-path coverage and stdio wire round-trip tests in `tests/test_stdio_adapter_direct.py` plus stats-routing validation in `tests/test_os_mcp_route_query.py`. |

## Reliability hardening (2026-02-11)

| Item | Status | Notes |
| --- | --- | --- |
| Normalize upstream invalid JSON errors across HTTP clients | Done | `tools/os_common.py`, `tools/ons_common.py`, and `tools/admin_lookup.py` now return `502` + `UPSTREAM_INVALID_RESPONSE`. |
| Add API endpoint matrix test coverage | Done | Added `tests/test_http_endpoint_matrix.py` for `/health`, `/tools/*`, `/resources/*`, `/playground/*`, and `/metrics`. |
| Add upstream endpoint contract regression tests | Done | Added `tests/test_tool_upstream_endpoint_contracts.py` to validate URL/params for OS, ONS, NOMIS, and admin lookup tool families. |
| Add rate-limit calibration script | Done | Added `scripts/rate_limit_assessor.py` and `tests/test_rate_limit_assessor.py` to recommend `RATE_LIMIT_PER_MIN` from probe results. |
| Apply calibrated default rate limit | Done | Calibrated on local `POST /tools/call` profile; updated default `RATE_LIMIT_PER_MIN` to 207 in `server/config.py`. |
| Add per-task 429 audit summaries | Done | Audit logs now include `429 Rate-limit hits` and `429 by tool`; harness result/utilization exports include 429 counts (`tests/test_evaluation_audit_rate_limits.py`). |
| Harden protocol negotiation to latest MCP + MCP-Apps era | Done | Core default bumped to `2025-11-25`; stdio/http now negotiate supported versions and HTTP validates `MCP-Protocol-Version`; descriptor exposes `supportedProtocolVersions` + `mcpAppsProtocolVersion`. |

## Playground version visibility (2026-02-11)

| Item | Status | Notes |
| --- | --- | --- |
| Show version matrix in setup descriptor card | Done | `playground/src/App.svelte` now surfaces server/core/MCP Apps/client/SDK versions (with `n/a` fallbacks when disconnected). |
| Remove hardcoded playground client version | Done | Client/host now use `playground/package.json` version metadata (`0.1.0`). |
| Stabilize playground Playwright port usage | Done | `playground/playwright.config.js` now uses `4173` + `--strictPort`; smoke test asserts version matrix labels. |

## Verification status

Latest full test run: `pytest -q --cov-report=term-missing:skip-covered` (90.22% coverage, 675 passed, 6 skipped) on 2026-02-13.
Latest playground UI test run: `npm --prefix playground run test` (6 passed) on 2026-02-11.

## Claude UI fallback plan (short)

Goal: make Claude reliable by default (non-UI client), while still supporting
MCP-Apps UI for clients that render it.

| Task | Status | Notes |
| --- | --- | --- |
| Gate UI resources by client capability and only emit UI content when supported | Done | Capability gating now uses shared stdio/http helpers and consistent fallback mode selection for `os_apps.render_*` tools. |
| Add UI content-mode switch for MCP-Apps render tools | Done | `MCP_APPS_CONTENT_MODE` supports `resource_link`, embedded `resource`, or text-only content blocks; `os_apps.render_ui_probe` added for verification. |
| Provide a static map image endpoint/tool | Done | Return a renderable image URL (server-side) for Claude. |
| Provide a browser map viewer that prompts for OS API key when needed | Not started | Local assets only; prompt in-page without logging. |
| Update docs + skills to guide Claude to map fallback flow | Not started | Explicit “use os_maps.render + image link” guidance. |
| Add tests for Claude fallback behavior | Done | Added end-to-end host render verification for UI-capable/non-UI hosts plus sanitized-name behavior in Playwright. |
| Handle sanitized tool names in UI widgets | Done | UI widgets now retry tool calls with the sanitized (underscore) tool name when the host rejects dotted names. |
| Add trace session + artifact bundle workflow | Done | `scripts/trace_session.py` + `scripts/trace_report.py` and docs update. |

## Tool naming compatibility plan (2026-02-09)

Context: some MCP clients (notably Claude) require tool names matching
`^[a-zA-Z0-9_-]{1,64}$`, which means dotted tool names (for example `os_places.by_postcode`)
can be rejected or silently sanitized.

Our STDIO adapter already sanitizes names for list/search, but MCP-Apps UI widgets were
calling dotted names directly, causing “Tool not found” errors under dot-disallowing hosts.

Plan:
- Treat the sanitized form (dot → underscore, plus collision handling) as the primary client-facing name for restricted clients.
- Preserve dotted names as canonical internal IDs for backward compatibility (HTTP callers + internal code), while accepting sanitized aliases.
- Implement shared tool-name mapping helpers and use them consistently across STDIO + HTTP + UI widgets.

Implementation status:
1. Done: shared sanitize/resolve/schema-rewrite logic is centralized in `server/tool_naming.py` and consumed by STDIO + HTTP routers.
2. Done: HTTP discovery endpoints are sanitized-first and `/tools/call` + `/tools/describe` accept sanitized aliases.
3. Done: UI widgets keep sanitized retry behavior when hosts reject dotted names.
4. Done: HTTP/STDIO tests plus Playwright host-render regression cover sanitized-name behavior.
5. Done: README guidance now documents sanitized names and `annotations.originalName`.

## Toolset grouping review (Google MCP toolkit style)

Implemented named toolsets and filters in `server/mcp/tool_search.py` with
exposure via `/tools/list`, `/tools/describe`, `/tools/search`, and MCP
`tools/list` + `tools/search` (`toolset`, `includeToolsets`, `excludeToolsets`).

| Toolset | Coverage status |
| --- | --- |
| `core_router` | Done |
| `places_names` | Done |
| `features_layers` | Done |
| `maps_tiles` | Done |
| `admin_boundaries` | Done |
| `ons_selection` | Done |
| `ons_data` | Done |
| `nomis_data` | Done |
| `apps_ui` | Done |
