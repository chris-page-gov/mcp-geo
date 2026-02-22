# MCP Geo Context

Last updated: 2026-02-22
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

- Prioritizing reliable layered map rendering (polygons, lines, points) across
  all clients, with interaction as progressive enhancement where host runtime
  supports MCP-Apps UI; repo-side `LMR-BASE-0` through `LMR-FBK-3` are complete
  (2026-02-21), `LMR-GATE-5` is complete with documented map-quality
  waiver/threshold policy, and external host/runtime risk remains tracked
  explicitly under `LMR-HOST-4`.
- Keeping the completed phased progress program stable with full regression coverage.
- Driving the OS catalog/tooling gap closure plan via parallel workstreams.
- Prioritizing next major gap after gap closure: CI pipeline implementation.
- Maintaining post-remediation safe-by-design/governance compliance against UK
  standards (NCSC/ICO/Data Ethics Framework/ATRS/Five Safes), OWASP LLM
  guidance, W3C provenance/catalog standards, and MCP `2025-11-25`.
- Running map delivery interoperability research focused on reliable rendering across
  MCP clients, browsers, and GIS workflows.
- Executing the map delivery recommendation workstreams in phased delivery
  order (`MDR-I*`, `MDR-N*`, `MDR-M*`, `MDR-E*`) with tracking updates per stage.
- Keeping the completed map-delivery program artifacts synchronized across docs,
  resources, scripts, and trial evidence outputs.
- Driving the new peatland survey reliability hardening program (`PSR-*`) based
  on the 2026-02-19 forensic/deep-research implementation plan.
- Implementing dual-derivation ONS geography caching with `ONSPD` + `ONSUD`
  as primary exact-mode references and `NSPL` + `NSUL` in parallel for
  best-fit/statistical comparability.

## Active Work

- Maintain and monitor the completed layered-map reliability workstreams
  (`LMR-BASE-0`, `LMR-ALL-1`, `LMR-INT-2`, `LMR-FBK-3`, `LMR-GATE-5`) and keep
  the remaining external host-runtime blocker
  (`LMR-HOST-4`) visible.
- Track post-program stabilization and backlog sequencing in `PROGRESS.MD`.
- Coordinate parallel OS gap workstreams and integration gates from
  `docs/reports/os_catalog_gap_implementation_plan_2026-02-13.md`.
- Documentation pack and preparation for workshop/demo.
- Deliver map delivery research package with personas, autonomous trials, and
  evidence capture under `research/map_delivery_research_2026-02/`.
- Track recommendation-delivery workstreams in
  `docs/reports/map_delivery_recommendations_implementation_plan_2026-02-14.md`
  and synchronize statuses in `PROGRESS.MD`.
- Track peatland survey reliability workstreams in
  `docs/reports/peatland_survey_reliability_implementation_plan_2026-02-19.md`
  and synchronize statuses in `PROGRESS.MD`.
- Maintain completed peatland streams (`PSR-INT-0` through `PSR-E2E-10`) and
  keep floor-question contracts (`os_peat.*`, AOI provenance, direct/proxy
  evidence separation) stable across HTTP + STDIO.
- Maintain compatibility-first map docs/contracts and support matrix links in
  `docs/spec_package/06_api_contracts.md`,
  `docs/spec_package/06a_map_delivery_fallback_contracts.md`, and
  `docs/map_delivery_support_matrix.md`.
- Maintain deterministic host-simulation fixtures, latency-budget trial
  reporting, and optional sidecar runbook assets under `playground/trials/`,
  `scripts/map_trials/`, and `scripts/sidecar/`.
- Maintain offline map delivery contracts and scenario-pack resource lifecycle
  artifacts under `tools/os_offline.py`, `resources/offline_map_catalog.json`,
  and `data/map_scenario_packs/`.
- Maintain ecosystem-facing embedding guidance and lightweight style profiles in
  `docs/map_embedding_best_practices.md` and
  `resource://mcp-geo/map-embedding-style-profiles`.
- Maintain presentation story-gallery scenarios, screenshot evidence, and
  slide-ready reporting outputs under `playground/trials/fixtures/`,
  `playground/trials/tests/`, and
  `research/map_delivery_research_2026-02/reports/story_gallery_report.md` +
  `research/map_delivery_research_2026-02/reports/story_gallery_slides.md`.
- Maintain the dependency-tracked governance remediation log in
  `safe-by-design.json` and keep the compliance score/current state synchronized
  with code and tests.
- Keep the extracted Prism LaTeX brief citation set synchronized with
  authoritative UK/standards anchors and bibliography integrity checks.
- Maintain ONS postcode/UPRN geography cache artifacts and refresh workflow
  (`resources/ons_geo_sources.json`, `scripts/ons_geo_cache_refresh.py`,
  `ons_geo.*` tools) with explicit exact vs best-fit derivation provenance.

## Status Snapshot (from PROGRESS.MD)

- Done (repo-side): layered map reliability workstreams
  `LMR-BASE-0`, `LMR-ALL-1`, `LMR-INT-2`, `LMR-FBK-3`, and `LMR-GATE-5`,
  including
  2026-02-21 matrix evidence (`35 passed`, `20 skipped`, `0 failed`) and
  fallback-contract parity tests plus documented quality policy outcomes
  (`map_quality_report.json`: `fail=0`, `warning=20`).
- Blocked (external): `LMR-HOST-4` Claude host runtime mount/bridge retest.
- Done: core server, stdio adapter, tool registry, OS Places/Names/Linked IDs/Vector Tiles,
  route_query tool, baseline tests, boundary cache ingestion pipeline.
- Done: completion program tracker items `C00` through `C16` (dataset-selection gating,
  UI fallback, tool naming/toolsets, OS features/maps overlays, export pipeline, NOMIS workflows,
  admin cache maturity, boundary/code-list cache resources, observability, and POI tools).
- Done: OS catalog/workstream wave implementation for WS-INT-0, WS-CAT-1, WS-DL-2, WS-SEARCH-3,
  WS-MAP-4, WS-POS-5, WS-QGIS-6, and WS-OBS-7 (OS Downloads, OS Net, OTA discovery, raster/WMTS,
  WFS capabilities, Places radius/polygon, Linked IDs extra paths, QGIS descriptors, and
  delivery-fallback/export-lifecycle observability).
- Partial: OS Maps render, ONS data tooling, admin lookup caching, resources
  population, playground UI.
- Done: ONS dataset selection research pack (taxonomy, datapack schema, linking rules,
  evaluation plan).
- Done: map delivery recommendation implementation program (`MDR-I1` to
  `MDR-E4`) complete across immediate, near-term, medium-term, and ecosystem
  waves.
- Done: peatland survey reliability implementation program (`PSR-*`) including
  `PSR-PEA-9` and `PSR-E2E-10` (peat evidence-layer integration plus
  deterministic floor-question E2E contract coverage).
- Done: strict non-runtime static quality gate restoration for reliability
  surfaces via `scripts/check_non_runtime_quality.sh`
  (`ruff` + `mypy --follow-imports=skip`).
- Done: dual-derivation ONS geography cache baseline (`ONSPD` + `ONSUD` exact,
  `NSPL` + `NSUL` best_fit) with tooling (`ons_geo.*`), refresh automation,
  route-query integration, and focused regression coverage.
- Not started: CI pipeline.

## Backlog Priorities (from spec package)

- High: layered map reliability across all clients (point/line/polygon render
  parity plus deterministic non-UI fallback contracts).
- High: interaction parity in UI-capable hosts and tracked retest/escalation of
  external host runtime gaps.
- High: CI pipeline; MCP-Apps client compatibility validation and docs.
- Medium: pagination for large tool results; structured JSON logging; expanded ONS caching;
  admin cache staleness policy; performance regression tests.
- Medium: near-term map engineering recommendations (deterministic host simulation,
  explicit widget-unsupported guidance fields, mobile viewport/latency trials,
  optional sidecar profile).
- Low: UI polish; CLI/Playground UX; documentation cross-links.
- Low: medium-term and ecosystem map roadmap items (offline PMTiles/MBTiles,
  output quality checks, notebook scenario packs, and external best-practice/style bundles).

## Completion Plan (phased)

- Phase 1 (Reliability and CI, 2-3 weeks): GitHub Actions pipeline; release automation;
  structured JSON logging option.
- Phase 2 (Data correctness, 2-4 weeks): pagination; dataset caching with TTL/invalidation;
  boundary pipeline validation rules.
- Phase 3 (UI fidelity, 2-4 weeks): fix MCP-Apps init flow for Claude/Inspector; produce
  screenshots.
- Phase 4 (Resources and observability, 4-6 weeks): populate resources; add latency/cache
  metrics; alerting guidance.
- Map delivery recommendation waves (planned):
  - Immediate: `MDR-I1` to `MDR-I4`
  - Near-term: `MDR-N1` to `MDR-N4`
  - Medium-term: `MDR-M1` to `MDR-M3`
  - Ecosystem-facing: `MDR-E1` to `MDR-E4`

## Verification Status

- Latest strict test run: `pytest -q` on 2026-02-21
  (`785 passed`, `6 skipped`, coverage gate failed at `86.69%` vs required `>=90%`).
- Latest live harness run: `RUN_LIVE_API_TESTS=1 ./.venv/bin/python -m tests.evaluation.harness --include-os-api --include-ons-live`
  on 2026-02-22 (`6900/6900`, `100%`, `69/69` passed, `rate_limit_429_total=0`).
- Latest full tool operability aggregation:
  `data/spec_tool_operability_coverage_2026-02-22.json` on 2026-02-22
  (`75/76` tools functional, `1/76` blocked by auth entitlement, `0` unresolved).
- Latest playground UI test run: `npm --prefix /Users/crpage/repos/mcp-geo/playground run test` (6 passed) on 2026-02-11.
- Latest container test run: `devcontainer exec --workspace-folder /Users/crpage/repos/mcp-geo bash -lc "pytest -q --cov-report=term-missing:skip-covered"` (90.03% coverage, 703 passed, 6 skipped) on 2026-02-13.

## Key Conventions

- Follow `AGENTS.md` for repo rules.
- Track plan status in `PROGRESS.MD`.
- Track release notes in `CHANGELOG.md`.

## Decisions Log

- 2026-02-22: Implemented ONS geography lookup cache strategy with
  `ONSPD`/`ONSUD` as primary exact-mode products and `NSPL`/`NSUL` in parallel
  as best-fit products, including manifest/index resources, refresh
  automation (`scripts/ons_geo_cache_refresh.py`), lookup tools
  (`ons_geo.by_postcode`, `ons_geo.by_uprn`, `ons_geo.cache_status`), and
  route-query recommendations for explicit postcode/UPRN geography mapping
  prompts.
- 2026-02-22: Closed remaining OS/ONS live-evaluation deltas by implementing
  map-render keyword compatibility (`render.urlTemplate` alias), deterministic
  invalid-postcode handling in `os_places.by_postcode`, hierarchy/tool-discovery
  routing hardening in `os_mcp.route_query`, and expected-error scoring fixes
  in the evaluation harness; full live rerun now scores `6900/6900` (`100%`)
  with `69/69` passed.
- 2026-02-22: Added transient NOMIS dataset-catalog degradation behavior in
  `tools/nomis_data.py` for non-dataset-specific `nomis.datasets` calls
  (`UPSTREAM_CONNECT_ERROR`/`UPSTREAM_INVALID_RESPONSE`/`CIRCUIT_OPEN`),
  preserving graceful responses during upstream instability while keeping
  dataset-specific failures explicit.
- 2026-02-22: Closed remaining live-evaluation P1 ONS observation behavior by
  normalizing `observations: null` payloads in `tools/ons_data.py` to empty
  results (not integration failures) and by expanding single-token quarter/year
  values (with alias-version retry) so `ons_data.get_observation` resolves
  queries like `2023 Q1` against live monthly GDP dimensions. Added regression
  tests in `tests/test_ons_data.py`; focused OS/ONS live rerun
  (`B004,B012,B007,B008,B016,I008,I009,I011`) now scores `800/800` (`100%`).
- 2026-02-22: Closed live-evaluation P1 ONS contract drift by updating
  `tools/ons_data.py` to fetch observations with implicit dimension filters
  first (only escalating to explicit paging when needed) and by accepting live
  option payload codes from `links.code.id` in both `tools/ons_data.py` and
  `tools/ons_codes.py`; added regression coverage in
  `tests/test_ons_data.py` and `tests/test_ons_codes_live.py`.
- 2026-02-22: Hardened `os_mcp.route_query` to improve measurable
  intent-recognition quality against the evaluation bank: added explicit
  handling for linked-id phrasing before UPRN address short-circuiting,
  dataset-discovery metadata prompts, MCP-Apps widget/probe requests, cache and
  utility operations, and reduced command-word false positives in place-name
  extraction.
- 2026-02-22: Updated live operability gating to treat
  `os_features.wfs_archive_capabilities` as optional-by-entitlement in release
  denominator calculations while keeping explicit blocker evidence and
  requirement tracking (`REQ-LIVE-TOOLS-05`) in generated coverage artifacts.
- 2026-02-22: Added an Apps-to-Answers presentation deck aligned to the
  January 2026 UK government dataset-readiness guidance at
  `research/Deep Research Report/Apps_to_Answers_MCP_Government_Alignment_Slides.md`
  to support workshop/demo documentation packaging.
- 2026-02-21: Added reproducible live operability evidence tooling for
  full-tool validation: `scripts/live_missing_tools_probe.py` (covers tools
  missing from harness utilization) and
  `scripts/spec_tool_operability_coverage.py` (aggregates measurable
  requirement outcomes from harness + probe reports).
- 2026-02-21: Added explicit spec coverage artifacts for live operability in
  `docs/spec_package/14_tool_operability.feature` and
  `docs/spec_package/14_tool_operability_coverage.md` to prevent
  documentation drift and make release-readiness claims auditable.
- 2026-02-21: Hardened `ui/boundary_explorer.html` for constrained client
  runtimes by switching responsive layout to map-prioritized placement in
  narrow hosts and adding cross-level fallback search behavior/messages when
  `admin_lookup.find_by_name` returns no matches at the selected level (for
  example, `WARD` + "Westminster").
- 2026-02-21: Documented and mitigated an MCP-host interoperability pattern
  where `tools/call` payloads may arrive via `structuredContent`/`content`
  blocks (without `result.data`) and map-style swaps can hide overlays unless
  source/layer state is replayed on `style.load`. Added payload-shape
  normalization in `ui/geography_selector.html` and
  `ui/statistics_dashboard.html`, and recorded the pattern in
  `AGENTS.md` learnings.
- 2026-02-21: Added `scripts/check_lmr_host4.py` to automate `LMR-HOST-4`
  evidence classification from Claude trace + UI logs, with optional
  prechecks (`scripts/mcp_ui_mode_probe.py`, Playwright `trial-5`) and JSON
  report output at `logs/lmr-host4-report.json`.
- 2026-02-21: Completed repo-side layered-map reliability implementation
  streams `LMR-BASE-0`, `LMR-ALL-1`, `LMR-INT-2`, `LMR-FBK-3`, and
  `LMR-GATE-5` with refreshed cross-engine trial evidence
  (`35 passed`, `20 skipped`, `0 failed`), story-gallery style tuning for
  reduced quality-check failures, and documented waiver/threshold policy
  acceptance (`map_quality_report.json`: `fail=0`, `warning=20`).
- 2026-02-21: Addressed Codex review follow-up on PR #11 by removing raw
  exception trace/text logging from MCP transport internal-error handlers
  (`server/stdio_adapter.py`, `server/mcp/http_transport.py`) and by replacing
  the global rate-limit-bypass test fixture with per-test limiter-state reset
  while preserving secure default `RATE_LIMIT_BYPASS=false`.
- 2026-02-21: Completed safe-by-design remediation implementation streams
  `SBD-REV-001` through `SBD-REV-008` and `SBD-REV-010`, including path
  containment hardening, redaction expansion, transport error sanitization,
  malformed JSON normalization, secure rate-limit defaults, and logging cleanup.
- 2026-02-21: Re-evaluated governance compliance after remediation and updated
  `safe-by-design.json` status to `fully_met` with weighted score `89.6`.
- 2026-02-21: Completed safe-by-design governance/citation review deliverables:
  added `docs/reports/safe_by_design_review_2026-02-21.md` and
  `safe-by-design.json`, patched extracted Prism brief citations under
  `research/From Apps to Answers - Connecting Public Sector Data to AI with MCP/`,
  and refreshed canonical BibTeX metadata/URLs (including replacing dead Five
  Safes reference URL).
- 2026-02-21: Started a full safe-by-design/gov-assurance review and created a
  dependency-tracked remediation log (`safe-by-design.json`) plus a scored
  compliance rubric/report (`docs/reports/safe_by_design_review_2026-02-21.md`).
  Initially identified a source dependency for Prism-authenticated content; this
  was later resolved by using the extracted local LaTeX brief.
- 2026-02-19: Implemented peatland reliability streams `PSR-INT-0` through
  `PSR-ROU-8`:
  - `os_features.query` now applies hard limit clamping (`<=100`), structured
    hints (`warnings`, `filterApplied`, `scan`), deterministic polygon
    validation, timeout degrade behavior, and resource-backed
    `delivery=inline|resource|auto`.
  - Added protected-landscape support via `os_landscape.find`,
    `os_landscape.get`, and
    `resource://mcp-geo/protected-landscapes-england` (Bowland coverage).
  - Hardened `os_mcp.route_query` for peatland survey prompts with
    `environmental_survey` intent and AOI-first survey plan guidance.
- 2026-02-19: Added a dependency-tracked peatland survey reliability
  implementation plan at
  `docs/reports/peatland_survey_reliability_implementation_plan_2026-02-19.md`
  and synchronized tracker entries in `PROGRESS.MD` to drive Section F
  remediation (`PSR-*` workstreams).
- 2026-02-17: Added offline pack binary retrieval endpoint
  (`GET /resources/download?uri=resource://mcp-geo/offline-packs/<file>`) so
  large PMTiles/MBTiles resources no longer require inlined base64 payloads in
  `resources/read` responses while preserving a deterministic download path for
  map handoff workflows.
- 2026-02-17: Hardened `os_offline.get` artifact hash performance by honoring
  declared `sha256` in `resources/offline_map_catalog.json` and caching fallback
  file digests by `(path, mtime, size)` when runtime hashing is needed.
- 2026-02-14: Codex MCP startup can time out when `scripts/claude-mcp-local`
  is configured with `MCP_GEO_DOCKER_BUILD=always` (Docker build exceeds Codex
  handshake window). For Codex MCP registration, keep the same wrapper command
  chain but use `MCP_GEO_DOCKER_BUILD=missing` to allow reliable initialize +
  tool-call negotiation.
- 2026-02-14: Identified `ui://`-relative widget assets (`vendor/maplibre-*`)
  as a host-interop failure mode in Claude and updated geography/boundary
  widgets to use absolute MapLibre CDN URLs with jsDelivr fallback, plus
  proxy-only worker URL wiring and CSP domain updates.
- 2026-02-14: Added Claude-specific stdio widget content-mode coercion in
  `server/stdio_adapter.py` so `os_apps.render_*` defaults to `contentMode=resource_link`
  for Claude clients (unless explicitly overridden), addressing repeated
  sessions where embedded HTML blocks were echoed in transcript while preserving
  a UI-launchable resource block.
- 2026-02-14: Verified residual Claude UI limitation via trace: after
  `resource_link` tool results, Claude performs `resources/read ui://...` but
  widget runtime bridge events (`os_apps.log_event`) still do not appear,
  indicating host-side mount/bridge failure outside MCP server control.
- 2026-02-14: Diagnosed boundary explorer non-render in Claude as a widget
  bootstrap coupling bug in `ui/boundary_explorer.html`: map runtime failures
  (`maplibre` missing/worker init issues) could prevent reliable
  `ui/notifications/initialized` completion. Fixed by decoupling host init from
  map init, adding degraded-mode handling, and emitting `os_apps.log_event`
  diagnostics for host/map runtime states.
- 2026-02-14: Captured two recurring Claude troubleshooting outcomes in docs:
  tool-name namespace hints (`mcp-geo:<tool>`) can be client-side pre-dispatch
  mismatches, and inline-preview `maplibregl is not defined` errors are preview
  runtime limits even when the same HTML works in a full browser.
- 2026-02-14: Hardened MCP tool-call result shape for strict hosts by always
  emitting `structuredContent` when tool handlers return dict payloads (stdio
  and HTTP transports). This was prompted by Claude traces showing `tools/call`
  responses with `status=200` while UI still reported `Tool execution failed`.
- 2026-02-14: Documented macOS startup prompt behavior
  (`"python3.14" would like to access data from other apps`) and clarified it
  as an OS-level permission event for the Python wrapper process, not an MCP
  protocol/server failure.
- 2026-02-14: Extended tool-name alias resolution to accept client/server
  namespaced forms (for example `mcp-geo:os_places_search`) after Claude
  surfaced a mismatch between prefixed discovery names and unprefixed call names.
- 2026-02-14: Updated `os_poi.search|nearest|within` to use `dataset=DPA,LPI`
  after Claude trace replay showed OS Places rejecting `dataset=POI` with a
  hard 400, causing early map-workflow failures despite healthy map tools.
- 2026-02-14: Hardened tool-name alias resolution in
  `server/tool_naming.py` to accept display-style names (case/spacing/
  punctuation variants such as `Os names find`) after a Claude map-flow trace
  showed repeated unknown-tool failures presented as generic `Tool execution failed`.
- 2026-02-14: Added `os_offline.descriptor` and `os_offline.get` to the
  evaluation harness specialist-tool allowlist in
  `tests/test_evaluation_harness_full.py` to prevent false missing-coverage
  failures after MDR-M1 offline tool registration.
- 2026-02-14: Completed ecosystem map-delivery recommendation wave
  (`MDR-E1` to `MDR-E4`) by publishing an MCP/AI-host best-practice bundle,
  constrained style profiles, progressive fallback examples, and mixed host
  degradation guidance.
- 2026-02-16: Hardened devcontainer MCP startup so STDIO uses repo code instead
  of site-packages (`scripts/os-mcp` file-based import), keeps repo root ahead
  of user site-packages (`scripts/os_mcp.py`), and forces user site visibility
  in the VS Code stdio wrapper (`scripts/vscode_mcp_stdio.py`).
- 2026-02-16: Made devcontainer installs align with the STDIO interpreter
  (`python3 -m pip` in post-create) and added a post-start loguru check to
  auto-install repo deps when missing.
- 2026-02-16: Added devcontainer HTTP auto-start toggle and documented STDIO
  dependency recovery steps in `docs/getting_started.md`.
- 2026-02-17: Added a presentation-focused map story gallery with six
  real-world layered scenarios, automated screenshot capture in Playwright
  trials, and a generated story-gallery report mapping map-tool coverage to
  slide-ready evidence artifacts.
- 2026-02-17: Added `story_gallery_slides.md` with one slide per scenario and
  speaker notes to speed Wednesday presentation assembly.
- 2026-02-14: Completed medium-term map-delivery recommendation wave
  (`MDR-M1` to `MDR-M3`) by adding offline PMTiles/MBTiles handoff tooling and
  resources, automated map quality checks with waiver support, and
  notebook-derived scenario-pack resources with provenance metadata.
- 2026-02-14: Completed near-term map-delivery recommendation wave
  (`MDR-N1` to `MDR-N4`) by adding deterministic host simulation fixtures,
  explicit fallback guidance fields, mobile latency budgets/reporting, and an
  optional Martin/pg_tileserv sidecar deployment profile.
- 2026-02-14: Completed immediate map-delivery recommendation wave
  (`MDR-I1` to `MDR-I4`) by promoting `os_maps.render` as canonical baseline,
  documenting stable fallback skeleton contracts, standardizing `starter`-first
  startup guidance, and publishing `docs/map_delivery_support_matrix.md`.
- 2026-02-14: Ratified a detailed, dependency-tracked map delivery
  recommendations implementation plan in
  `docs/reports/map_delivery_recommendations_implementation_plan_2026-02-14.md`
  and seeded `PROGRESS.MD` tracking (`MDR-I1` to `MDR-E4`) without feature
  implementation in this planning branch.
- 2026-02-13: Added a containerized map-delivery trial harness (Playwright
  multi-browser config + runner + JSONL/PNG evidence capture) with
  compatibility-first focus on static route and tool-driven render contracts.
- 2026-02-13: Established map delivery layering policy for MCP Geo:
  static map contract first, resource-backed overlays second, MCP-App widgets
  as progressive enhancement, and GIS descriptors for professional workflows.
- 2026-02-13: Captured OS VTS label rendering constraint from Claude/Desktop
  validation: custom symbol-layer text should use HTML/DOM marker overlays
  rather than glyph-backed symbol text on OS VTS basemaps.
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
