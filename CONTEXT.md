# MCP Geo Context

Last updated: 2026-02-13
Owner: @chris-page-gov

## Purpose

This file is the durable, repo-scoped context for Codex across environments.
Read it at the start of a session and update it whenever priorities or key
assumptions change.

## Project Snapshot

- FastAPI MCP server for Ordnance Survey and ONS geospatial tooling.
- Primary entrypoints: `server/main.py` (HTTP) and `server/stdio_adapter.py` (JSON-RPC).
- Tooling and resources live under `tools/` and `resources/`.

## Spec Package Map

- The spec package is the end-to-end prototype specification for test readiness and demos.
- Primary entry: `docs/spec_package/README.md`; roadmap: `docs/spec_package/12_backlog_and_plan.md`.
- Use chapter references for detail: aims (`01_aims_objectives.md`), personas
  (`02_personas_user_stories.md`), architecture (`03_architecture.md`),
  system design (`04_system_design.md`), data flow/cache (`05_data_flow_and_cache.md`),
  API contracts (`06_api_contracts.md`), security (`07_security_privacy.md`),
  observability (`08_observability_ops.md`), testing (`09_testing_quality.md`),
  MCP-Apps UI (`10_mcp_apps_ui.md`), walkthroughs (`11_walkthroughs.md`),
  backlog/plan (`12_backlog_and_plan.md`), screenshots (`screenshots.md`),
  sequence diagrams (`13_sequence_diagrams.md`), export instructions (`export.md`).
- Quick guidance: use `03_architecture.md`/`04_system_design.md` for system understanding,
  `06_api_contracts.md` for interface details, `10_mcp_apps_ui.md` for UI behaviors, and
  `12_backlog_and_plan.md` for delivery sequencing.
- Current scope snapshot: HTTP and STDIO MCP server; OS Places/Names/NGD/linked IDs/maps/
  admin lookup/ONS tools; boundary cache pipeline; MCP-Apps UI resources via `ui://`.

## Codex Usage (Mac App + Devcontainer)

- `CONTEXT.md` is the durable, cross-surface source of truth; read and update it at session start.
- Devcontainer persistence: `CODEX_HOME` is mounted to the named volume `mcp-geo-codex`
  in `.devcontainer/devcontainer.json`, so Codex local state survives rebuilds.
- Spec package exports are ignored in git: `docs/spec_package/build/`.
- External ref (Codex app overview/install): `https://developers.openai.com/codex/app/`.
- External ref (Codex app features): `https://developers.openai.com/codex/app/features`.
- External ref (Codex app announcement): `https://openai.com/index/introducing-the-codex-app/`.
- External ref (VS Code devcontainer mounts): `https://code.visualstudio.com/remote/advancedcontainers/add-local-file-mount`.
- External ref (Docker volumes reference): `https://docs.docker.com/engine/storage/volumes/`.

## Current Focus

- Keeping the completed phased progress program stable with full regression coverage.
- Driving the OS catalog/tooling gap closure plan via parallel workstreams.
- Prioritizing next major gap after gap closure: CI pipeline implementation.

## Active Work

- Track post-program stabilization and backlog sequencing in `PROGRESS.MD`.
- Coordinate parallel OS gap workstreams and integration gates from
  `docs/reports/os_catalog_gap_implementation_plan_2026-02-13.md`.
- Documentation pack and preparation for workshop/demo.

## Status Snapshot (from PROGRESS.MD)

- Done: core server, stdio adapter, tool registry, OS Places/Names/Linked IDs/Vector Tiles,
  route_query tool, baseline tests, boundary cache ingestion pipeline.
- Done: completion program tracker items `C00` through `C16` (dataset-selection gating,
  UI fallback, tool naming/toolsets, OS features/maps overlays, export pipeline, NOMIS workflows,
  admin cache maturity, boundary/code-list cache resources, observability, and POI tools).
- Done: OS catalog/workstream wave implementation for WS-INT-0, WS-CAT-1, WS-DL-2, WS-SEARCH-3,
  WS-MAP-4, WS-POS-5, WS-QGIS-6, and WS-OBS-7 (OS Downloads, OS Net, OTA discovery, raster/WMTS,
  WFS capabilities, Places radius/polygon, Linked IDs extra paths, QGIS descriptors, and
  delivery-fallback/export-lifecycle observability).
- Partial: OS Features, OS Maps render, ONS data tooling, admin lookup caching, resources
  population, playground UI.
- Done: ONS dataset selection research pack (taxonomy, datapack schema, linking rules,
  evaluation plan).
- Not started: CI pipeline.

## Backlog Priorities (from spec package)

- High: CI pipeline; MCP-Apps client compatibility validation and docs.
- Medium: pagination for large tool results; structured JSON logging; expanded ONS caching;
  admin cache staleness policy; performance regression tests.
- Low: UI polish; CLI/Playground UX; documentation cross-links.

## Completion Plan (phased)

- Phase 1 (Reliability and CI, 2-3 weeks): GitHub Actions pipeline; release automation;
  structured JSON logging option.
- Phase 2 (Data correctness, 2-4 weeks): pagination; dataset caching with TTL/invalidation;
  boundary pipeline validation rules.
- Phase 3 (UI fidelity, 2-4 weeks): fix MCP-Apps init flow for Claude/Inspector; produce
  screenshots.
- Phase 4 (Resources and observability, 4-6 weeks): populate resources; add latency/cache
  metrics; alerting guidance.

## Verification Status

- Latest full test run: `pytest -q` (90.02% coverage, 708 passed, 6 skipped) on 2026-02-13.
- Latest playground UI test run: `npm --prefix /Users/crpage/repos/mcp-geo/playground run test` (6 passed) on 2026-02-11.
- Latest container test run: `devcontainer exec --workspace-folder /Users/crpage/repos/mcp-geo bash -lc "pytest -q --cov-report=term-missing:skip-covered"` (90.03% coverage, 703 passed, 6 skipped) on 2026-02-13.

## Key Conventions

- Follow `AGENTS.md` for repo rules.
- Track plan status in `PROGRESS.MD`.
- Track release notes in `CHANGELOG.md`.

## Decisions Log

- 2026-02-13: Hardened Claude/STDIO payload sizing for map workflows by adding
  explicit limits to `os_places.search` and `os_names.find`, reducing
  `os_map.inventory` default/max limits to avoid oversized overlay payloads,
  and truncating oversized STDIO tool `content` text with a pointer to
  `result.data` for full structured payloads.
- 2026-02-13: Added initialize-time client support summaries (requested protocol,
  negotiated protocol, and capability booleans) to STDIO and HTTP logs for
  traceable protocol/capability conclusions without increasing tool payloads.
- 2026-02-13: Added `os_mcp.select_toolsets` as a post-init discovery control
  tool with query-driven toolset inference and MCP form-elicitation support in
  both STDIO and Streamable HTTP transports.
- 2026-02-13: Added startup discovery throttling via default toolset filters for
  `tools/list`/`tools/describe`/MCP `tools/list` when clients omit filters.
  New env knobs: `MCP_TOOLS_DEFAULT_TOOLSET`,
  `MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS`, and
  `MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS`; added curated `starter` toolset for
  low-context client initialization.
- 2026-02-13: Applied post-review hardening updates for PR #1: included OS vector
  stylesheet submodule path in Docker build context, removed `EXPOSE 8000` from
  STDIO-default image, aligned getting-started docs with Playwright port
  (`4173`), and made Playwright shpjs route matching resilient to URL variants.
- 2026-02-13: Completed WS-QGIS-6 and WS-OBS-7 by adding `os_qgis.vector_tile_profile`
  and `os_qgis.export_geopackage_descriptor`, plus delivery fallback observability
  metric/export lifecycle logging for OS downloads; full regression now passes at
  90.16% coverage.
- 2026-02-13: Implemented parallel OS catalog gap workstreams WS-INT-0, WS-CAT-1,
  WS-DL-2, WS-SEARCH-3, WS-MAP-4, and WS-POS-5, including new OS Downloads, OS Net,
  OTA, WMTS/ZXY raster, WFS capabilities, and catalog probe coverage; full regression
  now passes at 90.22% coverage.
- 2026-02-13: Revised OS catalog gap implementation plan into dependency-gated
  parallel workstreams suitable for separate threads/subagents, with shared-file
  ownership and integration checkpoints documented in
  `docs/reports/os_catalog_gap_implementation_plan_2026-02-13.md`.
- 2026-02-12: Added OS catalog usage and delivery analysis report (`docs/reports/os_catalog_repo_usage_and_delivery_plan_2026-02-12.md`) covering catalog-to-runtime coverage, NGD overlap analysis, large-payload delivery patterns, cache/storage options, and QGIS linkage recommendations.
- 2026-02-11: Removed the dedicated Warwick/Leamington 3D MCP-Apps tool/resource and added a response-size guard to keep UI tool payloads below the 1MB transport limit.
- 2026-02-11: Closed phased completion program tracker item `C16` after full regression (`pytest -q`, 90.26% coverage) and playground Playwright verification (`6 passed`).
- 2026-02-02: Added persistent Codex context file and devcontainer Codex home mount.
- 2026-02-02: Expanded CONTEXT.md with PROGRESS and spec package summary to preserve context.
- 2026-02-06: Added legacy `uiResourceUris` fields in MCP-Apps tool responses to improve Claude Desktop compatibility.
- 2026-02-06: Added `resource_link` content blocks in MCP-Apps tool responses for UI host compatibility.
- 2026-02-06: Defaulted `resource_link` content to opt-in (`MCP_APPS_RESOURCE_LINK=0` by default; set `1` to opt in) to avoid unsupported format warnings in Claude.
- 2026-02-06: Bounded `nomis.datasets` responses with `q`/`limit` discovery controls and updated stats routing guidance to avoid unfiltered dataset listing loops.
- 2026-02-06: Added STDIO form elicitation for comparison-style `os_mcp.stats_routing` calls when client capability negotiation includes `elicitation.form`.
- 2026-02-06: Extended `os_mcp.stats_routing` with `comparisonLevel`/`providerPreference` overrides and returned `userSelections` for traceable routing behavior.
- 2026-02-06: Claude Desktop reports “unsupported format” when tool responses include `content` blocks of type `resource_link` (MCP-Apps UI), so treat `resource_link` as unsupported in Claude until proven otherwise.
- 2026-02-06: Claude transcript captured at `docs/Claude_opus_4-6_failed_convo_1.md` shows MCP-Apps UI still failing to render; follow up with raw stdio trace for capabilities and content blocks.
- 2026-02-06: Claude stdio trace (`logs/claude-trace.jsonl`) confirms `os_apps.render_statistics_dashboard` returns a `resource_link` content block, which aligns with the “unsupported format” error in Claude.
- 2026-02-06: Added `MCP_APPS_CONTENT_MODE` and `os_apps.render_ui_probe` to control UI content blocks and test client rendering without `resource_link`.
- 2026-02-06: Updated `scripts/claude-mcp-local` to default `MCP_APPS_RESOURCE_LINK=0` so Claude sessions do not emit `resource_link` unless explicitly enabled.
- 2026-02-06: Updated `nomis.datasets` dataset-definition path to return a compact summary by default and require `includeRaw=true` for full upstream definition payloads.
- 2026-02-06: Claude `parent_message_uuid` UUID validation errors were confirmed as host/session-state failures (not MCP tool payload failures); troubleshooting docs updated with recovery steps.
- 2026-02-06: Updated `scripts/claude-mcp-local` to default `MCP_APPS_CONTENT_MODE=embedded` so Claude receives embedded UI resources instead of `resource_link` by default.
- 2026-02-06: Added flat `ui/resourceUri` metadata alongside nested `ui.resourceUri` in UI tool metadata for broader MCP-Apps host compatibility.
- 2026-02-06: `nomis.datasets` query filtering now applies multi-token scoring for better dataset ranking on compound prompts (for example `population census 2021`).
- 2026-02-06: `scripts/mcp_stdio_trace_proxy.py` now avoids JSON parse attempts for stderr/non-RPC lines to reduce noisy parse-error entries in trace logs.
- 2026-02-07: Added ONS dataset selection research pack under `research/ons_dataset_selection/` to guide dataset ranking, elicitation, and explainability.
- 2026-02-07: Added Agent Skills vendor submodule and tracking entry to align Codex skill usage with the Agent Skills spec.
- 2026-02-08: VS Code MCP server launch can fail after restart if the launcher doesn’t expand `${workspaceFolder}`; prefer repo-root relative paths + `cwd` repo root (see `.vscode/mcp.json`).
- 2026-02-08: Fixed `mcp-geo-trace` proxy crash (`TypeError: unhashable type: 'bytearray'`) in `scripts/mcp_stdio_trace_proxy.py`; added regression test.
- 2026-02-07: Added `ons_select.search` + `resource://mcp-geo/ons-catalog` with a catalog refresh script to improve ONS dataset selection.
- 2026-02-07: Added related-dataset linking with comparability gating to `ons_select.search` (opt-in via `includeRelated`).
- 2026-02-07: Wired `ons_select.search` missing-context prompts into MCP form elicitation (`elicitation/create`) for STDIO and Streamable HTTP transports.
- 2026-02-07: Fixed `os_features.query` to use the NGD OGC API Features items endpoint; fixed `os_linked_ids.get` to use OS search/links identifierTypes.
- 2026-02-07: Added OS API + downloads catalog snapshot (`resource://mcp-geo/os-catalog`) with refresh script and live validation run report.
- 2026-02-08: Added VS Code workspace MCP config at `.vscode/mcp.json` (including a trace profile) and removed legacy `mcp.servers` config from `.vscode/settings.json`.
- 2026-02-08: Devcontainer PostGIS host port is now random by default to avoid conflicts; set `MCP_GEO_POSTGIS_HOST_PORT` to pin.
- 2026-02-09: MCP-Apps UI widgets now retry tool calls using sanitized (underscore) tool names when dotted names are rejected by the host; tool naming strategy updated to treat sanitized names as first-class for restricted clients.
- 2026-02-11: Normalized invalid upstream JSON handling across OS/ONS/admin clients to `502` + `UPSTREAM_INVALID_RESPONSE` and added regression tests.
- 2026-02-11: Added endpoint matrix and upstream URL-contract tests to catch route/endpoint regressions across HTTP endpoints and tool families.
- 2026-02-11: Added `scripts/rate_limit_assessor.py` to calibrate `RATE_LIMIT_PER_MIN` against observed 429 ratio/latency and output a recommendation JSON report.
- 2026-02-11: Evaluation audit records now summarize per-task `429` hits (including a by-tool breakdown) to track backoff reliance.
- 2026-02-11: Core protocol negotiation now prefers MCP `2025-11-25` with compatibility for `2025-06-18`, `2025-03-26`, and `2024-11-05`; HTTP now validates `MCP-Protocol-Version` against negotiated session version.
- 2026-02-11: Playground setup now includes a version matrix showing MCP core + MCP Apps + client/SDK versions; Playwright playground tests now run on port `4173` to avoid local `5173` collisions.
- 2026-02-10: Added `scripts/vscode_mcp_stdio.py` and updated `.vscode/mcp.json` to use it so VS Code can start stdio servers on macOS without requiring global Python deps (it prefers the repo venv at `.venv/`).
- 2026-02-10: Added `scripts/vscode_trace_snapshot.py` to convert VS Code trace artifacts into a `logs/sessions/` directory that can be summarized by `scripts/trace_report.py`.

## Open Questions

- Should we formally deprecate dotted tool names and standardize on sanitized names across HTTP + STDIO (and how do we surface `originalName` mappings consistently)?
- Does Claude Desktop actually render MCP-Apps UI from `_meta.ui.resourceUri` or `uiResourceUris` without `resource_link`, or is it currently ignoring MCP-Apps UI entirely?

## Run and Test Notes

- `uvicorn server.main:app --reload`
- `pytest -q`
