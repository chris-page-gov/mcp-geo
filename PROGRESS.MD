# MCP Geo Progress

This file tracks how the implementation compares to the original proposal and
later documentation as the MCP specification evolved.

Last updated: 2026-01-24

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
| OS Maps (render) | Partial | tools/os_maps.py | Returns metadata only; no server-side map rendering. |
| OS Vector Tiles | Done | tools/os_vector_tiles.py | Descriptor tool present. |
| ONS data query + filters | Partial | tools/ons_data.py, tools/ons_codes.py | Live-only mode; filter output formats exist but no streaming/large export pipeline. |
| ONS dataset search | Done | tools/ons_search.py | Live search only; no sample fallback. |
| Admin geography lookup | Partial | tools/admin_lookup.py | Live ArcGIS path only; boundary resources still minimal. |
| Static resources (code lists, boundaries) | Partial | server/mcp/resource_catalog.py, resources/ | Code lists present; full boundary packs not yet shipped. |
| Conversational normalization | Done | tools/os_mcp.py, tests/evaluation/* | route_query + descriptor for tool discovery. |
| Evaluation harness / coverage matrix | Done | tests/evaluation/*, docs/evaluation.md | Question suite + rubric + harness; live capture optional. |
| Playground UI for developers | Partial | playground/, server/mcp/playground.py | New Svelte playground scaffold; still needs UI resource rendering + evaluation orchestration. |
| MCP-Apps UI widgets | Done | tools/os_apps.py, docs/mcp_apps_alignment.md | Dual ext-apps + OpenAI Apps support. |
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
- MCP-Apps UI support expanded to cover ext-apps and OpenAI Apps SDK.
- Tool search (`/tools/search`) plus routing tool (`os_mcp.route_query`).
- Conditional resources with weak ETags and `If-None-Match` support.
- STDIO adapter compatibility adjustments (arguments/params, name normalization).

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
- Expand admin_lookup caching and performance strategy.

## Active implementation plan (2026-01-24)

| Step | Status | Notes |
| --- | --- | --- |
| Audit error handling + logging + live-only behavior | Done | Error taxonomy + upstream logging mapped. |
| Implement error classification, JSON logging, dataset cache scaffolding | Done | JSON log sink + dataset cache in place. |
| Build Svelte + Vite playground (MCP client + logging hooks) | In progress | Initial UI + tool call logging + prompt capture added. |
| Add Playwright + devcontainer updates + docs | Done | Devcontainer installs Playwright deps; docs updated. |
| Run tests + fix regressions | Done | `pytest -q` passed (coverage 91.35%); `npm test` passed after Playwright deps. |

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

Latest full test run: `pytest -q` (92% coverage, 313 passed, 1 skipped).

## Claude UI fallback plan (short)

Goal: make Claude reliable by default (non-UI client), while still supporting
MCP-Apps UI for clients that render it.

| Task | Status | Notes |
| --- | --- | --- |
| Gate UI resources by client capability and only emit UI content when supported | Not started | Keep `resource_link` blocks out for non-UI clients; use data-only + fallback guidance. |
| Provide a static map image endpoint/tool | Not started | Return a renderable image URL (server-side) for Claude. |
| Provide a browser map viewer that prompts for OS API key when needed | Not started | Local assets only; prompt in-page without logging. |
| Update docs + skills to guide Claude to map fallback flow | Not started | Explicit “use os_maps.render + image link” guidance. |
| Add tests for Claude fallback behavior | Not started | STDIO response shape + tool behavior. |
