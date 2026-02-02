# MCP Geo Progress

This file tracks how the implementation compares to the original proposal and
later documentation as the MCP specification evolved.

Last updated: 2026-02-02

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

## Progress against the original vision

Legend: Done, Partial, Not started

| Area | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Core MCP server (tools/resources/health) | Done | server/main.py, server/mcp/*, docs/Build.md | Includes /tools/list, /tools/call, /resources/read, /mcp JSON-RPC. |
| STDIO adapter | Done | server/stdio_adapter.py, scripts/os-mcp, tests/test_stdio_* | JSON-RPC 2.0 with framing auto-detect. |
| Tool registry + dynamic imports | Done | server/mcp/tools.py, tools/registry.py | Explicit module import loop. |
| OS Places (geocoder) | Done | tools/os_places.py, docs/examples.md | search/by_postcode/by_uprn/nearest/within implemented. |
| OS Names (gazetteer) | Done | tools/os_names.py | find + nearest. |
| OS Linked Identifiers | Done | tools/os_linked_ids.py | UPRN/USRN/TOID resolution. |
| OS Features (NGD / OGC Features) | Partial | tools/os_features.py | Only bbox query exposed; no attribute filters/polygon/collection listing. |
| OS Maps (render) | Partial | tools/os_maps.py, server/maps_proxy.py | Static map proxy URL now available; full rendering/overlays still pending. |
| OS Vector Tiles | Done | tools/os_vector_tiles.py | Descriptor tool present. |
| ONS data query + filters | Partial | tools/ons_data.py, tools/ons_codes.py | Live mode required; ons_codes supports on-disk cache; no streaming/large export pipeline. |
| ONS dataset search | Done | tools/ons_search.py | Live search only; no sample fallback. |
| Admin geography lookup | Partial | tools/admin_lookup.py, server/boundary_cache.py | Live ArcGIS path plus optional PostGIS cache; boundary dataset ingestion still needed. |
| Boundary ingest pipeline | Done | scripts/boundary_pipeline.py, docs/Boundaries.json | Full ingest + validation completes with ArcGIS Hub polling; run report recorded. |
| Static resources (code lists, boundaries) | Partial | server/mcp/resource_catalog.py, resources/ | Boundary manifest + cache status exposed; full boundary packs not yet shipped. |
| Conversational normalization | Done | tools/os_mcp.py, tests/evaluation/* | route_query + descriptor for tool discovery. |
| Evaluation harness / coverage matrix | Done | tests/evaluation/*, docs/evaluation.md | Question suite + rubric + harness; live capture optional. |
| Playground UI for developers | Partial | playground/, server/mcp/playground.py | New Svelte playground scaffold; still needs UI resource rendering + evaluation orchestration. |
| MCP-Apps UI widgets | Done | tools/os_apps.py, docs/mcp_apps_alignment.md | Aligned to MCP Apps extension (no OpenAI Apps SDK fallback). |
| Observability (logs/metrics) | Partial | server/main.py, server/logging.py | JSON log sink and upstream error logging added; metrics remain basic. |
| Rate limiting + error model | Done | server/main.py, server/config.py | 429 handling + uniform error envelope. |
| CI/CD pipeline | Not started | docs/build_initial_version.md | No GitHub Actions pipeline committed. |

## Additional API coverage from the documentation collection task

The documentation collection identifies extra OS and ONS services beyond the
core tools. Current implementation coverage is incomplete for:

- OS Net API (GNSS / RINEX data): not implemented.
- OS Match & Cleanse API: not implemented.
- OS Downloads API: not implemented.
- OAuth2 flow for OS APIs: not implemented (API key only).
- Points of Interest / POI APIs: not implemented.
- Full ONS Open Geography linked data API: not implemented (ArcGIS live lookup is used instead).

## Spec evolution milestones captured in the repo

- Streamable HTTP `/mcp` endpoint added for MCP clients.
- MCP-Apps UI support aligned to finalized ext-apps spec (JSON-RPC `ui/initialize`, no skybridge).
- Tool search (`/tools/search`) plus routing tool (`os_mcp.route_query`).
- Conditional resources with weak ETags and `If-None-Match` support.
- STDIO adapter compatibility adjustments (arguments/params, name normalization).
- OS API auth failures now classified into missing/invalid/expired key errors.

## Outstanding work (from original proposal + newer docs)

High impact
- Implement OS Points of Interest coverage (tool and/or resource).
- Expand OS Features to support attribute filters, polygons, and collection listing.
- Ship real boundary resources (wards, LSOA/MSOA, LAD, etc.) with paging + metadata.
- Finish the playground UI (UI resource rendering + evaluation harness orchestration).
- Provide OAuth2 support for OS APIs where required.

Medium impact
- Add OS Net / Match & Cleanse / Downloads tooling if still in scope.
- Replace map render descriptor stub with a real rendering or proxy service.
- Expand ONS data export (streaming CSV/XLSX) and add more live dataset coverage.
- Improve observability: structured JSON logs, latency histograms, request/response size metrics.
- Add CI pipeline (lint, type, tests, coverage, build image).

Low impact
- Add golden fixtures for canonical postcodes and feature queries.
- Enrich resource catalog with fuller code lists and provenance metadata.
- Expand boundary cache coverage (ingest official datasets at multiple resolutions).

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

## Codex context persistence (2026-02-02)

| Item | Status | Notes |
| --- | --- | --- |
| Add durable repo context template | Done | CONTEXT.md |
| Update agent guidance to read/update repo context | Done | AGENTS.md |
| Persist Codex home across devcontainer rebuilds | Done | .devcontainer/devcontainer.json |

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

## Verification status

Latest full test run: `pytest -q` (90.13% coverage, 386 passed, 1 skipped).

## Claude UI fallback plan (short)

Goal: make Claude reliable by default (non-UI client), while still supporting
MCP-Apps UI for clients that render it.

| Task | Status | Notes |
| --- | --- | --- |
| Gate UI resources by client capability and only emit UI content when supported | Not started | Keep `resource_link` blocks out for non-UI clients; use data-only + fallback guidance. |
| Provide a static map image endpoint/tool | Done | Return a renderable image URL (server-side) for Claude. |
| Provide a browser map viewer that prompts for OS API key when needed | Not started | Local assets only; prompt in-page without logging. |
| Update docs + skills to guide Claude to map fallback flow | Not started | Explicit “use os_maps.render + image link” guidance. |
| Add tests for Claude fallback behavior | Not started | STDIO response shape + tool behavior. |
