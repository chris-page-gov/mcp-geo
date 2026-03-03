# Changelog

All notable changes to this project will be documented in this file.


## [Unreleased]

### Added
- Added a simple map exploration UI resource (`ui://mcp-geo/simple-map-lab`)
  and implementation (`ui/simple_map.html`) for minimal OS Vector vs PMTiles
  trials with basic timing telemetry and deterministic pan-benchmark controls.
- Added `docs/simple_map_lab.md` with a focused runbook for browser bearer auth
  vs API-key fallback tests and PMTiles trial execution.

### Changed
- Hardened MCP interop for search-gated clients by teaching STDIO `tools/list`
  to honor query-style discovery params (`query`/`q`, `mode`, `limit`,
  `category`) and return ranked filtered tool definitions instead of full
  catalog payloads when a query is provided.
- Updated Docker Claude wrapper `scripts/claude-mcp-local` to pass through
  default toolset env controls (`MCP_TOOLS_DEFAULT_TOOLSET`,
  `MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS`,
  `MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS`) and `MCP_STDIO_TOOL_CONTENT_MAX_BYTES`
  into the container so constrained clients do not regress to full-catalog
  startup discovery.
- Updated the Svelte playground UI preview host controls to expose explicit
  compact-window testing mode (`auto` / `force compact` / `force regular`) with
  configurable compact width/height passed via `hostContext.containerDimensions`.
- Refined compact-window UX across playground + geography selector:
  - fixed maximize behavior to preserve compact preview dimensions while
    showing side-by-side host context
  - added adjustable list-pane width control in playground test view
  - reduced playground hero/header vertical footprint
  - consolidated UI preview diagnostics into the Debug tab
  - added map-first compact workflow tabs (`Map/Search/Results/Info/Debug/Help`)
    in `ui/geography_selector.html`
  - moved zoom ladder behind an icon toggle to prevent map obstruction.
- Added root markdownlint config (`.markdownlint.json`) to suppress
  line-length-only noise (`MD013`) and validated `README.md` syntax with fence
  language annotations and ordered-list normalization.
- Updated vendored specification/reference submodules to current upstream
  commits for `modelcontextprotocol`, `ext-apps`, `inspector`, and
  `agentskills` under `docs/vendor/`.
- Updated `/maps/vector/{path}` auth resolution in `server/maps_proxy.py` to
  prefer `Authorization: Bearer ...` from clients, then fall back to key
  query/header and finally server `OS_API_KEY`.
- Extended map proxy test coverage in `tests/test_maps_proxy.py` for bearer,
  key-header, environment-key fallback, and unauthenticated error behavior.
- Updated `docs/getting_started.md` and `docs/troubleshooting.md` with direct
  OS authentication + OAuth2 guidance links and OS Data Hub signup/API-project
  onboarding links.
- Updated `ui/simple_map.html` auth UX for beginners: masked bearer/API key
  fields, explicit account/key acquisition steps, token whitespace cleanup, and
  preflight permission checks before style load to avoid false-positive
  "loaded" status messages.
- Updated simple-map lab runtime compatibility and cache behavior by aligning
  MapLibre runtime/worker versions and serving `/ui/simple-map-lab` with
  `Cache-Control: no-store, max-age=0` to prevent stale browser-cached lab
  builds during debug sessions.
- Updated `ui/simple_map.html` to use an `OS Style` dropdown (OS + OS Open
  presets) and added a novice-focused style chooser writeup in both the UI and
  `docs/simple_map_lab.md`.
- Fixed vector-style proxy routing so `/maps/vector/vts/resources/styles` now
  respects the selected `style` query parameter (instead of always returning
  the default look), and corrected rewritten vector tile templates to
  `{z}/{y}/{x}` ordering.
- Added vendored MCP auth-extension spec submodule
  `docs/vendor/mcp/repos/ext-auth` and recorded the draft auth-spec tracking
  entry in `docs/spec_tracking.md`.
- Added MCP-Apps small-window review and redesign artifacts:
  `docs/reports/mcp_apps_window_constraints_review_2026-03-01.md` plus
  Figma-importable wireframes and handoff notes in `docs/design/figma/`.
- Added Figma MCP setup/capture runbook
  `docs/design/figma/mcp_figma_setup_and_capture_runbook.md`, including
  restart/auth verification, local capture sequence, and SVG-text fidelity
  troubleshooting guidance.
- Expanded compact-window review with an implementation-focused design action
  plan per UI and updated Figma status based on live capture results.
- Added compact-window unattended delivery planning artifacts:
  - implementation + test strategy:
    `docs/reports/compact_windows_unattended_implementation_and_test_plan_2026-03-01.md`
  - strict acceptance checklist (machine-readable):
    `docs/reports/compact_windows_acceptance_checklist_2026-03-01.json`
  - strict baseline run report:
    `docs/reports/compact_windows_acceptance_baseline_run_2026-03-01.md`
  - baseline evidence command run (`3` focused UI tests passed; strict compact
    gate remains `0/6` pre-implementation by policy).
- Added compact Playwright scaffold infrastructure for unattended execution:
  - new configs: `playground/playwright.compact.config.js`,
    `playground/playwright.compact-matrix.config.js`
  - new scripts: `npm --prefix playground run test:compact` and
    `npm --prefix playground run test:compact-matrix`
  - new suite scaffolding under `playground/tests/compact_windows/` with
    deterministic MCP bridge/profile support and passing baseline runs
    (`8 passed` compact smoke, `6 passed` compact matrix).
- Added the shared compact-window contract implementation for all six UIs:
  - new shared assets: `ui/shared/compact_contract.css` and
    `ui/shared/compact_contract.js`
  - all UI pages now wire compact host-context handling and stable
    `data-testid` status/CTA anchors used by unattended compact validation.
- Hardened `ui/boundary_explorer.html` for compact unattended coverage:
  - added explicit UPRN attribute filters (address contains, classification,
    scope, and flag toggles for address/active/residential-like)
  - added deterministic local import status/error reporting for
    GeoJSON/CSV/ZIP flows with test IDs for automation
  - extended `playground/tests/boundary_explorer_local_layers.spec.js` to
    assert filter behavior and import success/failure messaging.
- Hardened `ui/geography_selector.html` for compact unattended coverage:
  - added deterministic search flow-state status (`loading`, `empty`,
    `error`, `success`) and explicit UI hooks for style/opacity/layer controls
  - added stable test IDs for results, diagnostics, layer toggles, and
    selection actions
  - extended `playground/tests/geography_selector.spec.js` to assert flow
    status plus style/opacity/layer behavior under host simulation.
- Hardened `ui/statistics_dashboard.html` for compact unattended coverage:
  - added deterministic dashboard flow-state reporting across dataset search,
    edition/version loading, dimension option loading, and comparison query runs
  - added compact test hooks for dataset search/results and query error output
  - added `playground/tests/statistics_dashboard.spec.js` to verify success,
    empty-field validation, and query-state transitions end to end.
- Hardened `ui/simple_map.html` for compact unattended coverage:
  - added explicit auth-mode reporting (`bearer`, `api_key`, `server_env`) and
    surfaced auth/style state in diagnostics output
  - added stable compact test hooks for style selection, auth inputs, status,
    and diagnostics panels
  - added `playground/tests/simple_map.spec.js` to validate browser-token,
    API-key, and server-env fallback auth paths deterministically.
- Promoted `ui/feature_inspector.html` and `ui/route_planner.html` from static
  placeholders to MCP host-aware compact flows:
  - implemented `ui/initialize`, host-context merge, display-mode request
    handling, and fullscreen fallback behavior
  - added deterministic interactive contracts for feature lookup and route
  planning (with structured payload output)
  - added focused regression tests:
    `playground/tests/feature_inspector.spec.js` and
    `playground/tests/route_planner.spec.js`.
- Completed CW-7 unattended compact acceptance hardening:
  - replaced compact scaffold tests with strict acceptance-mapped suites in
    `playground/tests/compact_windows/smoke.spec.js` and
    `playground/tests/compact_windows/compact_matrix.spec.js`
  - added reusable compact harness utilities
    (`playground/tests/compact_windows/support/compact_assertions.js`) and a
    richer argument-aware deterministic MCP bridge
    (`playground/tests/compact_windows/support/mcp_bridge.js`)
  - updated compact contract behavior to provide docked status fallback in
    constrained windows (`ui/shared/compact_contract.{js,css}`)
  - validated with `test:compact` (`18 passed`), `test:compact-matrix`
    (`36 passed`), full Playwright (`29 passed`), and full pytest
    (`930 passed`, `6 skipped`, coverage `90.01%`).

## [0.4.0] - 2026-02-25

### Added
- Added repo extent/complexity analysis capability for `mcp-geo`:
  - analyzer `scripts/repo_extent_complexity_report.py` with dual-scope
    inventory (`git_tracked`, `workspace`), generated/output exclusion policy,
    Python cyclomatic complexity, churn-weighted hotspots, and optional
    GitHub Stats API enrichment
  - skill package `skills/mcp-geo-repo-extent-complexity/` with runbook,
    wrapper script, and source-backed SOTA metric rationale references
  - regression coverage in `tests/test_repo_extent_complexity_report.py`
  - baseline report artifacts in
    `docs/reports/repo_extent_complexity_2026-02-25.{md,json}`.
  - manager-facing report card output
    `docs/reports/repo_extent_complexity_report_card_2026-02-25.md` with
    plain-English terminology, metric basis/source explanations, and practical
    implications for non-technical stakeholders.
- Added Long Horizon-style Codex session summary capability for `mcp-geo`:
  - `scripts/codex_long_horizon_summary.py` to aggregate repo-scoped metrics
    from local Codex `sessions` + `archived_sessions` logs
  - deterministic summary-card template
    `skills/mcp-geo-long-horizon-summary/templates/summary_card.svg.tmpl`
    for slot-based metric rendering
  - skill runbook `skills/mcp-geo-long-horizon-summary/SKILL.md` with wrapper
    runner `skills/mcp-geo-long-horizon-summary/scripts/run_summary.sh`
    now producing image-first markdown plus summary-card SVG output
  - regression coverage in `tests/test_codex_long_horizon_summary.py`
  - baseline report artifacts in
    `docs/reports/mcp_geo_codex_long_horizon_summary_2026-02-25.{md,json,svg}`.
- Added ONS postcode/UPRN geography cache infrastructure for dual-derivation
  lookup workflows:
  - `server/ons_geo_cache.py` (normalization, schema bootstrap, indexed
    lookup, geography field extraction)
  - `tools/ons_geo.py` (`ons_geo.by_postcode`, `ons_geo.by_uprn`,
    `ons_geo.cache_status`)
  - `scripts/ons_geo_cache_refresh.py` (manifest-driven refresh with
    file/URL overrides and provenance hashes)
  - `resources/ons_geo_sources.json` (primary exact-mode `ONSPD`/`ONSUD` plus
    parallel best-fit `NSPL`/`NSUL`)
  - `resources/ons_geo_cache_index.json` (refresh status/index scaffold).
- Added peat evidence-layer integration for survey workflows:
  - `tools/os_peat.py` with `os_peat.layers` and `os_peat.evidence_paths`
  - `resources/peat_layers_england.json`
  - `resource://mcp-geo/peat-layers-england` catalog wiring
  - contract coverage in `tests/test_os_peat.py`.
- Added deterministic floor-question artifacts for peat survey release readiness:
  - fixture `tests/fixtures/psr_peat_floor_question.json`
  - HTTP + STDIO E2E contract tests in `tests/test_psr_peat_e2e.py`
  - harness assertions for `I018` in `tests/test_evaluation_harness_full.py`.
- Added repeatable non-runtime static analysis gate script
  `scripts/check_non_runtime_quality.sh` to enforce strict `ruff` + `mypy`
  checks on reliability-critical non-runtime surfaces.
- Added reproducible full-tool live validation automation:
  `scripts/live_missing_tools_probe.py` (+ `tests/test_live_missing_tools_probe.py`)
  to probe tools not covered by the evaluation harness and classify
  pass/auth-blocked outcomes.
- Added measurable operability-spec coverage generation:
  `scripts/spec_tool_operability_coverage.py`
  (+ `tests/test_spec_tool_operability_coverage.py`) and spec package chapters
  `docs/spec_package/14_tool_operability.feature` +
  `docs/spec_package/14_tool_operability_coverage.md`.
- Added a detailed peatland-survey reliability implementation program at
  `docs/reports/peatland_survey_reliability_implementation_plan_2026-02-19.md`
  to operationalize Section F findings from the forensic/deep-research report.
- Added an Apps-to-Answers presentation deck aligned to the January 2026 UK
  government dataset-readiness guidance and MCP framing:
  `research/Deep Research Report/Apps_to_Answers_MCP_Government_Alignment_Slides.md`.
- Added protected-landscape lookup tooling for survey AOI resolution:
  `tools/os_landscape.py` (`os_landscape.find`, `os_landscape.get`) with
  deterministic Bowland fixture coverage in
  `resources/protected_landscapes_england.json`.
- Added `resource://mcp-geo/protected-landscapes-england` to data resources for
  discoverable protected-landscape provenance and geometry fallback.
- Added a governance-focused safe-by-design review artifact at
  `docs/reports/safe_by_design_review_2026-02-21.md` with a standards-anchored
  citation audit, compliance checklist, rubric, and scored repo assessment.
- Added `safe-by-design.json`, a dependency-tracked remediation backlog with
  explicit acceptance criteria for transitioning governance controls to
  `fully_met`.
- Added `scripts/check_lmr_host4.py` to automate `LMR-HOST-4` host-runtime
  evidence checks from Claude stdio traces and UI event logs, including
  optional payload-shape and Playwright smoke prechecks, plus
  `tests/test_check_lmr_host4.py` coverage.
- Added a deterministic boundary-explorer host harness test at
  `playground/tests/boundary_explorer_host_harness.spec.js` that validates
  selected-boundary rendering and fullscreen-handshake fallback behavior under
  MCP host simulation.

### Changed
- Hardened boundary variant full-coverage policy and strict resolve gating:
  - `scripts/boundary_pipeline.py` now merges
    `completion_definition.default_variant_policy` with template/family
    overrides, supports deterministic equivalent/derived required-variant
    resolution, and enforces `require_full_variant_availability` at evaluation
    time.
  - Added variant accuracy metadata for non-direct mappings
    (`published_equivalent_variant`, derived classes including
    `derived_from_coarser_source`) so zoom/precision caveats are explicit in
    run evidence.
  - Added focused regression coverage in
    `tests/test_boundary_pipeline_variant_policy.py`.
  - Updated boundary manifest/checklist/report docs
    (`docs/Boundaries.json`, `docs/boundaries_completion_checklist.json`,
    `docs/reports/boundary_variant_coverage_gap_2026-02-23.md`) with explicit
    completion criteria and strict-run evidence.
- Added explicit cache-health degradation signaling for lookup status surfaces:
  `ons_geo.cache_status`, `admin_lookup.get_cache_status`, and
  `resource://mcp-geo/boundary-cache-status` now expose
  `performance.degraded` with reason/impact metadata so clients can detect
  reduced reliability when caches are unavailable or stale.
- Refreshed cache indexes/artifacts for local operability validation:
  `resources/code_list_packs_index.json`, `resources/boundary_packs_index.json`,
  and `resources/ons_geo_cache_index.json` now reflect the latest cache refresh
  run evidence.
- Expanded `docs/tutorial.md` to cover the current full tool-family surface
  (including `ons_geo.*`, peat/landscape, downloads/offline/QGIS/OTA, and
  MCP-Apps status notes) and added a concrete startup-context evaluation section
  for Claude/non-deferred clients with measured `tools/list` footprint and
  mitigation workflow (`starter` + `os_mcp.select_toolsets` + scoped
  `includeToolsets`).
- Updated `server/mcp/tool_search.py` starter toolset to include
  `os_mcp.select_toolsets` so constrained clients can always request scoped
  toolset expansion without loading full schemas; documented the behavior in
  `docs/troubleshooting.md` and added regression assertion in
  `tests/test_tool_search.py`.
- Updated MCP integration/discovery surfaces for ONS geography cache support:
  - registered `tools.ons_geo` in `server/mcp/tools.py`
  - added `ons_geo` categories/keywords/toolsets in
    `server/mcp/tool_search.py`
  - added data resources `resource://mcp-geo/ons-geo-sources` and
    `resource://mcp-geo/ons-geo-cache-index` in
    `server/mcp/resource_catalog.py`.
- Updated `os_mcp.route_query` to recommend `ons_geo.by_postcode` or
  `ons_geo.by_uprn` for explicit postcode/UPRN geography-mapping prompts while
  keeping OS Places recommendations for address retrieval queries.
- Added focused regression coverage for dual-derivation geography caching and
  routing in `tests/test_ons_geo_cache.py`, `tests/test_ons_geo.py`,
  `tests/test_ons_geo_cache_refresh.py`, and route/discovery/resource tests.
- Updated peatland survey routing to include `os_peat.evidence_paths` in
  AOI-first survey plans and alternatives (`tools/os_mcp.py`,
  `tests/test_os_mcp_route_query.py`).
- Updated runbook docs for peat survey execution/troubleshooting with explicit
  AOI provenance + direct/proxy evidence separation expectations and OS key
  dependency notes (`docs/examples.md`, `docs/troubleshooting.md`).
- Updated peatland reliability planning/status trackers to mark
  `PSR-PEA-9` and `PSR-E2E-10` complete (`PROGRESS.MD`, `CONTEXT.md`,
  `docs/reports/peatland_survey_reliability_implementation_plan_2026-02-19.md`,
  `docs/spec_package/09_testing_quality.md`).
- Closed remaining OS/ONS live-evaluation deltas and reached full harness score
  (`6900/6900`, `69/69` passed) by:
  - adding backward-compatible `render.urlTemplate` alias in
    `tools/os_maps.py`
  - returning deterministic `INVALID_INPUT` for unknown/empty postcode results
    in `tools/os_places.py`
  - hardening hierarchy/tool-discovery routing paths in `tools/os_mcp.py`
  - aligning cache-route efficiency budgets in `tests/evaluation/questions.py`
  - fixing expected-error scoring behavior in `tests/evaluation/harness.py`
    with regression coverage in `tests/test_evaluation_expected_errors.py`
  - adding graceful transient-degrade behavior for non-dataset-specific
    `nomis.datasets` upstream failures in `tools/nomis_data.py`.
- Updated MCP-Apps interactive widgets (`ui/boundary_explorer.html`,
  `ui/geography_selector.html`, `ui/statistics_dashboard.html`) to include a
  host-aware fullscreen toggle that uses `ui/request-display-mode` when the host
  advertises `availableDisplayModes` support, with graceful fallback messaging
  when fullscreen is unavailable.
- Updated fullscreen behavior across MCP-Apps widgets to keep the maximise
  control usable in hosts that do not advertise display modes (shows
  `Try maximise` and attempts `ui/request-display-mode` instead of disabling).
- Updated boundary explorer OS-warning handling to classify inventory failures
  by error code (for example `NO_API_KEY`, `MISSING_TOOL`) instead of always
  showing an API-key warning, and to surface toolset-missing guidance when
  `os_map.inventory`/`os_map.export` are not exposed.
- Updated boundary explorer boundary styling with a dedicated selected-outline
  line layer and stronger width/opacity defaults so selected ward boundaries
  remain visible in constrained host panels.
- Updated boundary explorer to expose a read-only runtime probe
  (`window.__MCP_GEO_BOUNDARY_EXPLORER__.getSnapshot()`) for deterministic
  harness assertions of source/rendered boundary counts and host capability
  state.
- Updated `playground/package.json` with a dedicated
  `test:boundary-harness` command for quick boundary explorer regression runs.
- Updated `.vscode/mcp.json` to source `OS_API_KEY` from `${env:OS_API_KEY}`
  (with existing `.env` startup fallback) instead of per-server prompt inputs,
  reducing duplicate prompts and startup-time key race conditions.
- Updated `.vscode/mcp.json` default toolset filters to include
  `features_layers` alongside `starter`, ensuring boundary explorer can invoke
  `os_map.inventory`/`os_map.export` in VS Code MCP sessions.
- Updated `os_map.inventory` and `os_map.export` `layers` input schemas to use
  explicit `oneOf` union branches (array+items/minItems, string+minLength, null),
  keeping strict MCP host schema validation compatibility while avoiding mixed
  keyword ambiguity across non-array branches.
- Updated `tools/ons_geo.py` + `server/ons_geo_cache.py` to surface unreadable
  cache failures as `503 CACHE_READ_ERROR` (instead of `404 NOT_FOUND`) when the
  cache file exists but SQLite query/read fails.
- Hardened `scripts/boundary_pipeline.py::_probe_source_url` response lifecycle
  to close `requests` responses via `finally`, preventing leaked open responses
  on JSON parse/runtime exceptions.
- Updated `ui/boundary_explorer.html` OS key warning rendering to construct the
  `OS_API_KEY` token via DOM nodes (no `innerHTML`) for safer future content
  handling.
- Updated `docs/spec_package/09_testing_quality.md`, `CONTEXT.md`, and
  `PROGRESS.MD` to reflect the latest strict + live verification evidence,
  including explicit coverage-gate failure status and MCP-Apps widget
  implementation scope (`feature_inspector` / `route_planner` still static).
- Hardened `os_mcp.route_query` intent classification to reduce live-evaluation
  misclassification penalties: added explicit handling for linked-id phrasing,
  dataset-discovery metadata prompts (dimensions/codes/versions/codelists/
  concepts), widget/probe phrasing, utility/cache operations, and command-word
  false positives in place-name extraction.
- Hardened live ONS observation interoperability in `tools/ons_data.py` by
  switching to implicit filter-only observation fetches (no `limit/page`
  unless truncation detection requires explicit paging), with automatic fallback
  when upstream rejects paging parameters.
- Expanded ONS option-code extraction in `tools/ons_data.py` and
  `tools/ons_codes.py` to accept live payload shape `links.code.id` in
  addition to legacy top-level code fields, preventing false empty option sets
  for datasets like GDP.
- Hardened live ONS observation handling in `tools/ons_data.py` so
  `observations: null` payloads are normalized to empty result sets (instead of
  integration failures), and single-token quarter/year requests now expand to
  concrete time options with alias-version retry for `gdp` prompts.
- Added regression coverage in `tests/test_ons_data.py` for null-observation
  payload handling and single-token time expansion/alias-retry behavior in
  `ons_data.get_observation`.
- Updated live operability release-gate accounting to treat
  `os_features.wfs_archive_capabilities` as optional-by-entitlement while still
  requiring explicit evidence tracking; surfaced this as measurable
  requirement data in `scripts/spec_tool_operability_coverage.py`,
  `tests/test_spec_tool_operability_coverage.py`, and
  `docs/spec_package/14_tool_operability*.{feature,md}`.
- Hardened `ui/boundary_explorer.html` for constrained host windows by moving
  to a map-prioritized responsive layout at narrow widths, and updated boundary name
  search to retry across other admin levels when the selected level returns no
  matches (with explicit UI status messaging rather than silent empty results).
- Updated boundary add/remove UX to surface actionable feedback (button state,
  add/remove confirmation, explicit add-failure reasons when geometry/bbox is
  unavailable), and de-emphasized basemap intensity with a veil layer so
  selected boundary outlines are significantly clearer.
- Extended `admin_lookup.find_by_name` with optional `includeGeometry` support
  (returns per-result bbox metadata), and updated boundary explorer Add/Zoom to
  use search-result bbox first before falling back to `admin_lookup.area_geometry`;
  this keeps Add/Zoom functional in stricter hosts where follow-on tool calls
  may be limited.
- Hardened remaining MCP-Apps widgets against strict tool-result payload shapes:
  `ui/geography_selector.html` and `ui/statistics_dashboard.html` now normalize
  `tools/call` payload extraction across `result.data`, `structuredContent`,
  and JSON `content` blocks to avoid silent no-result behavior when hosts omit
  `data`.
- Advanced layered-map reliability hardening streams (`LMR-BASE-0`,
  `LMR-ALL-1`, `LMR-INT-2`, `LMR-FBK-3`) and moved `LMR-GATE-5` into final
  closure with deterministic non-UI fallback parity and refreshed cross-engine
  validation evidence.
- Updated `server/stdio_adapter.py` static-map fallback contracts to always
  emit `fallbackOrder`, `map_card`, `overlay_bundle`, and `export_handoff`
  payloads derived from render data for no-UI clients.
- Updated trial host simulation and matrix coverage in
  `playground/trials/tests/support/host_simulation.js` and
  `playground/trials/tests/map_delivery_matrix.spec.js` to stabilize
  cross-engine bridge behavior and deterministic point/line/polygon interaction
  checks.
- Updated story-gallery rendering profile in
  `playground/trials/tests/map_story_gallery.spec.js` to reduce map-quality
  hard failures by de-emphasizing basemap texture and limiting non-essential
  overlay labels while preserving layered geometry evidence.
- Updated transport-parity tests (`tests/test_stdio_adapter_direct.py`,
  `tests/test_mcp_http.py`) and host-simulation validation to lock the fallback
  and layered-render contracts.
- Updated quality-check policy handling in
  `scripts/map_trials/map_quality_checks.py` and
  `research/map_delivery_research_2026-02/reports/map_quality_waivers.json` to
  support threshold-policy metadata and browser-scoped waivers, with test
  coverage in `tests/test_map_trials_quality_checks.py`.
- Updated map-delivery validation artifacts and operator docs:
  `research/map_delivery_research_2026-02/reports/trial_summary.md`,
  `research/map_delivery_research_2026-02/reports/story_gallery_report.md`, and
  `docs/map_delivery_support_matrix.md` now reflect the 2026-02-21 matrix run
  (`35 passed`, `20 skipped`, `0 failed`) and updated release-gate checklist
  status, including quality-check outcomes (`fail=0`, `warning=20`) under the
  documented waiver policy.
- Completed safe-by-design remediation implementation streams from
  `safe-by-design.json`:
  - hardened file-backed resource containment and traversal defenses in
    `server/mcp/resource_catalog.py` with expanded regression coverage in
    `tests/test_resource_catalog.py`
  - expanded secret redaction coverage (OS + NOMIS + token-like key masking)
    across logging/exception paths (`server/security.py`, `server/logging.py`,
    `server/main.py`) with verification tests
  - sanitized internal transport errors to generic client-safe messages with
    correlation IDs and exception-type-only server logs (no traceback/raw
    exception text) (`server/stdio_adapter.py`, `server/mcp/http_transport.py`)
  - normalized malformed JSON handling for tools/playground ingest endpoints to
    deterministic HTTP 400 `INVALID_INPUT` envelopes
  - set secure default `RATE_LIMIT_BYPASS=false` and documented
    test/dev overrides; tests now reset in-memory limiter state per test
    instead of globally bypassing rate limiting (`server/config.py`,
    `README.md`, `docs/Build.md`, `docs/tutorial.md`, `.env.example`,
    `tests/conftest.py`)
  - removed raw startup print and `%s`-style loguru calls in `server/main.py`
    and added startup diagnostics through structured logging
  - replaced silent startup import swallowing with warning diagnostics in
    `server/mcp/tools.py`
- Updated planning trackers to include the new `PSR-*` workstreams in
  `PROGRESS.MD`, synchronized report index links in `docs/reports/README.md`,
  and refreshed execution context in `CONTEXT.md`.
- Updated the extracted Prism LaTeX brief citations and requirements mapping
  under `research/From Apps to Answers - Connecting Public Sector Data to AI with MCP/`
  to strengthen UK governance/standards grounding (NCSC, ICO, Data and AI
  Ethics Framework, ATRS, Five Safes, OWASP LLM, PROV/DCAT, MCP 2025-11-25).
- Updated `research/From Apps to Answers - Connecting Public Sector Data to AI with MCP/references.bib`
  with canonical standards URLs and metadata corrections, including replacement
  of a dead ONS Five Safes URL.
- Updated `.gitignore` to exclude `research/Archive/` raw archive drops from
  version control.
- Updated troubleshooting guidance with one-command `LMR-HOST-4` automation
  instructions and strict precheck mode (`--run-probe`,
  `--run-playwright-smoke`), and updated Playwright trials web-server launch
  fallback to prefer `./.venv/bin/python` before `python3`.
- Completed peatland reliability streams `PSR-INT-0` through `PSR-ROU-8`:
  `os_features.query` now enforces `limit<=100` clamps, deterministic polygon
  validation, structured `hints` metadata (`warnings`, `filterApplied`, `scan`),
  timeout degrade behavior, and `delivery=inline|resource|auto` large-payload
  handoff.
- Hardened `os_mcp.route_query` with `environmental_survey` intent routing for
  peatland-survey prompts and AOI-first/counts-first/geometry-last survey plans
  anchored on `os_landscape.*` + bounded `os_features.query`.
- Updated `CONTEXT.md` and `PROGRESS.MD` with active safe-by-design governance
  review status, standards-alignment scope, and a citation-source dependency
  note for the Prism-authenticated research brief.

## [0.3.2] - 2026-02-17

### Added
- Added devcontainer HTTP auto-start toggle (`MCP_GEO_DEVCONTAINER_START_HTTP`).
- Added devcontainer STDIO registration toggle (`MCP_GEO_DEVCONTAINER_REGISTER_STDIO`).
- Added a map delivery interoperability research pack under
  `research/map_delivery_research_2026-02/` with personas, longlist options,
  trial design/results, external source register, progress journal, and final
  recommendations report.
- Added a detailed, dependency-tracked map delivery recommendations
  implementation plan at
  `docs/reports/map_delivery_recommendations_implementation_plan_2026-02-14.md`
  with workstream IDs `MDR-I1` through `MDR-E4`.
- Added map delivery planning status tracking in `PROGRESS.MD` and context
  alignment updates in `CONTEXT.md` for the new workstream program.
- Added containerized autonomous map trial tooling:
  - `playground/playwright.trials.config.js`
  - `playground/trials/tests/map_delivery_matrix.spec.js`
  - `scripts/run_map_delivery_trials.sh`
  - `scripts/map_trials/summarize_playwright_trials.py`
- Added notebook-based trial tracking starter at
  `research/map_delivery_research_2026-02/notebooks/map_delivery_option_tracker.ipynb`.
- Added a browser/widget capability matrix at `docs/map_delivery_support_matrix.md`
  with verification dates, capability modes, env toggles, and evidence pointers.
- Added map-delivery fallback contract appendix
  `docs/spec_package/06a_map_delivery_fallback_contracts.md` defining
  `map_card`, `overlay_bundle`, and `export_handoff` schemas and conformance checks.
- Added deterministic host-simulation fixtures and utilities for map trials:
  `playground/trials/fixtures/host_capability_profiles.json`,
  `playground/trials/tests/support/host_simulation.js`,
  and `scripts/map_trials/host_simulation_profiles.py` (+ tests).
- Added optional sidecar deployment assets for scaled map delivery:
  `scripts/sidecar/docker-compose.map-sidecar.yml`,
  `scripts/sidecar/smoke_sidecar_profile.sh`,
  and `docs/sidecar_profile.md`.
- Added offline map delivery tooling and resources:
  `tools/os_offline.py` (`os_offline.descriptor`, `os_offline.get`),
  `resources/offline_map_catalog.json`,
  `resource://mcp-geo/offline-map-catalog`,
  and `resource://mcp-geo/offline-packs*`.
- Added map quality-check automation with waiver support:
  `scripts/map_trials/map_quality_checks.py`,
  `research/map_delivery_research_2026-02/reports/map_quality_report.json`,
  and `research/map_delivery_research_2026-02/reports/map_quality_waivers.json`.
- Added notebook scenario-pack export and resources:
  `scripts/map_trials/export_notebook_scenario_pack.py`,
  `data/map_scenario_packs/*`,
  and `resource://mcp-geo/map-scenario-packs*`.
- Added ecosystem map embedding guidance bundle:
  `docs/map_embedding_best_practices.md`.
- Added constrained map embedding style profiles resource:
  `resource://mcp-geo/map-embedding-style-profiles`
  (`resources/map_embedding_style_profiles.json`).
- Added presentation-ready map story gallery assets:
  `playground/trials/fixtures/map_story_scenarios.json`,
  `playground/trials/tests/map_story_gallery.spec.js`,
  `scripts/map_trials/summarize_story_gallery.py`,
  `research/map_delivery_research_2026-02/reports/story_gallery_report.md`,
  and `research/map_delivery_research_2026-02/reports/story_gallery_slides.md`.

### Changed
- Updated devcontainer installs to use `python3 -m pip` and added a post-start loguru check to ensure STDIO deps are present.
- Updated STDIO wrappers to prefer repo code and keep user site-packages behind the repo on `sys.path`.
- Updated VS Code stdio wrapper to re-enable user site-packages when disabled by the host.
- Updated MCP tool-call response shaping (STDIO and Streamable HTTP) to always
  include `structuredContent` for dict payloads when tools do not provide it
  explicitly, improving compatibility with strict clients that validate
  tool-result structure.
- Hardened `ui/boundary_explorer.html` host bootstrap so UI initialization is
  decoupled from MapLibre runtime initialization; map engine failures now enter
  an explicit degraded mode (instead of aborting host init), with `os_apps.log_event`
  telemetry for `host_ready`, `map_init_skipped`, `map_init_failed`, and runtime
  script errors.
- Updated stdio Claude interop for MCP-Apps tools by introducing
  `MCP_STDIO_CLAUDE_APPS_CONTENT_MODE` (default `resource_link` in `scripts/claude-mcp-local`)
  and auto-applying that mode to `os_apps.render_*` calls when the client is
  Claude and no explicit `contentMode` is provided.
- Updated map widgets (`ui/geography_selector.html`,
  `ui/boundary_explorer.html`) to load MapLibre via absolute CDN URLs with
  jsDelivr fallback instead of `ui://`-relative `vendor/*` paths, and to set
  MapLibre worker URLs only when `proxyBase` is available. This addresses
  Claude runs where widget HTML loaded but `window.maplibregl` stayed undefined.
- Added troubleshooting evidence that some Claude sessions still fetch
  `ui://...` resources (`resource_link` + `resources/read`) without launching
  widget bridge/runtime (`os_apps.log_event` never emitted), isolating the
  residual issue to host-side UI mount/bridge behavior.
- Updated troubleshooting guidance for Claude/Desktop startup and execution
  failures where UI shows `Tool execution failed` despite trace-confirmed
  `status=200` tool responses, including the macOS `python3.14` permission
  prompt interpretation.
- Updated troubleshooting and support-matrix guidance for two common Claude map
  troubleshooting traps: server-prefixed tool-name hints (for example
  `mcp-geo:os_names_find`) and inline-preview `maplibregl is not defined`
  errors caused by preview sandbox constraints rather than MCP server failures.
- Hardened devcontainer setup for map validation workflows:
  - Added forwarded ports for Playwright test server, Inspector, and Jupyter.
  - Added Jupyter extension and post-create install of `jupyterlab` and `ipykernel`.
  - Added container env defaults for trial workspace and expanded CORS dev origins.
  - Expanded base image packages (`jq`, `postgresql-client`, `libspatialindex-dev`).
- Updated map and onboarding docs to make `os_maps.render` the canonical
  compatibility baseline and standardize lean `starter`-first discovery guidance:
  `README.md`, `docs/getting_started.md`, `docs/examples.md`,
  `docs/tutorial.md`, `docs/ChatGPT_setup_chat.md`, and `docs/troubleshooting.md`.
- Updated map-delivery alignment docs and research index links to reference the
  fallback contract definitions and support matrix:
  `docs/mcp_apps_alignment.md`,
  `docs/spec_package/06_api_contracts.md`,
  `research/map_delivery_research_2026-02/README.md`.
- Updated map trial matrix execution to include mobile projects, deterministic
  host-profile replay, and latency-budget assertions with per-observation
  telemetry.
- Updated trial summary reporting to include latency percentiles (`p50/p90/p95`)
  and budget-compliance rollups.
- Updated non-UI fallback payloads (STDIO + HTTP) to include explicit
  widget-unsupported guidance fields and deterministic next-step tool hints.
- Updated architecture/design/walkthrough spec docs with optional Martin +
  pg_tileserv sidecar deployment guidance.
- Updated resources catalog and retrieval handlers to expose offline pack and
  notebook scenario-pack index/file resources with path-traversal guards.
- Updated trial runner orchestration to include scenario-pack export and map
  quality checks in the standard map-delivery run sequence.
- Updated map trial orchestration/docs to generate a story-gallery report for
  slide production workflows.
- Updated getting-started docs with VS Code Playwright extension considerations
  for devcontainer runs (extension context, browser install verification,
  OS key/env requirements, port overrides, and demo smoke command).
- Updated docs/examples/tutorial/troubleshooting/architecture with deterministic
  progressive fallback guidance for full UI, partial UI, and no-UI hosts.
- Updated the full evaluation harness specialist-tool whitelist to include
  `os_offline.descriptor` and `os_offline.get`, avoiding false coverage-gap
  failures after adding offline map delivery tools.
- Updated tool-name resolution to accept display-style aliases (for example
  `Os names find`) by normalizing case/spacing/punctuation to canonical MCP
  tool identifiers before dispatch.
- Updated `os_poi.search|nearest|within` to use the OS Places-supported
  dataset parameter `DPA,LPI` (instead of rejected `POI`) so Claude map flows
  no longer fail on POI-first discovery attempts.
- Updated tool-name resolution to accept server-prefixed aliases like
  `mcp-geo:os_places_search` and `mcp-geo/os_places_search` in addition to
  canonical dotted/sanitized forms.

## [0.3.1] - 2026-02-13
### Added
- Added a curated `starter` toolset to discovery metadata for lean MCP startup
  capability exposure.
- Added default toolset discovery knobs:
  `MCP_TOOLS_DEFAULT_TOOLSET`,
  `MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS`, and
  `MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS`.
- Added `os_mcp.select_toolsets`, a post-init tool that resolves
  `tools/list` filter parameters (`toolset`, `includeToolsets`,
  `excludeToolsets`) with optional query-based inference.
- Added VS Code toolset configuration template at
  `.vscode/mcp-geo.toolsets.jsonc` plus setup guidance in VS Code docs/README.
- Added troubleshooting guidance for OS VTS custom-label rendering limits and
  the HTML/DOM marker overlay workaround.

### Changed
- Updated STDIO/MCP and HTTP discovery handlers so `tools/list` and
  `/tools/list`/`/tools/describe` apply default toolset filters when clients do
  not pass explicit toolset parameters.
- Updated initialize logging for STDIO and Streamable HTTP to emit a compact
  client capability/protocol support summary suitable for audit traces.
- Added MCP form-elicitation support for `os_mcp.select_toolsets` in both
  STDIO and Streamable HTTP transports (post-init flow).
- Tightened large-payload behavior for Claude/STDIO map flows:
  `os_places.search` and `os_names.find` now enforce explicit result limits,
  `os_map.inventory` defaults/max limits are reduced to transport-safe values,
  and STDIO tool `content` text is truncated with a clear pointer to
  `result.data` for full payloads.

## [0.3.0] - 2026-02-13
### Added
- Added phased completion tracker in `PROGRESS.MD` for the open work program
  (`C00`–`C16`) covering dataset selection, UI fallback, tool naming/toolsets,
  OS features/maps expansion, exports, resources, observability, and POI.
- Added stricter `ons_select.search` comparability gating over geography/time/revision/denominator
  plus typed related-dataset edges with explainable `linkReason`, comparability notes,
  revision/release context, and provenance metadata.
- Added `tools/ons_catalog_validator.py` and `scripts/ons_catalog_validate.py` for reusable
  ONS catalog schema/comparability metadata validation.
- Added evaluation coverage for ONS catalog resource metadata and comparability explainability
  checks in `tests/evaluation/questions.py`.
- Added shared client capability/fallback helpers in `server/mcp/client_capabilities.py`
  so stdio and HTTP transports apply identical MCP-Apps UI gating decisions.
- Added Playwright host-render end-to-end tests for UI-capable host rendering,
  deterministic non-UI fallback payloads, and sanitized/dotted tool-name behavior.
- Added sanitized-first HTTP tool discovery output (`/tools/list`, `/tools/describe`,
  `/tools/search`) with `annotations.originalName` alias mapping metadata.
- Added named toolsets (Google toolkit-style grouping) with `toolset`,
  `includeToolsets`, and `excludeToolsets` filters across HTTP and MCP
  tool discovery/search surfaces.
- Added `os_features.query` expansion for polygon geometry input, attribute filters,
  projection/sort controls, `resultType=hits`, and optional queryables metadata.
- Added overlay-ready `os_maps.render` contract with explicit input overlays
  (points/lines/polygons/local layers), overlay collection summaries, and optional
  `os_map.inventory` hydration for buildings/road links/path links/UPRNs.
- Added playground orchestration APIs (`GET/DELETE /playground/orchestration`)
  with session-aware transcript/event summaries and evaluation snapshot wiring.
- Added shared observability counters and `/metrics` export lines for per-tool
  latency histograms, input/output payload bytes, cache-hit counts, fallback
  counts, and playground event/orchestration counters.
- Added OS POI tooling: `os_poi.search`, `os_poi.nearest`, and `os_poi.within`
  with OS Places-backed POI queries and normalized outputs.
- Added POI-aware routing guidance in `os_mcp.route_query` (`poi_lookup`
  intent) and expanded tool-search metadata/toolsets to include `os_poi.*`.
- Added release-readiness closure updates in `PROGRESS.MD`/`CONTEXT.md` with
  completion of tracker item `C16` and refreshed verification status.
- Added shared OS delivery helpers in `tools/os_delivery.py` and new OS cache/export
  config keys (`OS_EXPORT_INLINE_MAX_BYTES`, `OS_DATA_CACHE_DIR`, `OS_DATA_CACHE_TTL`,
  `OS_DATA_CACHE_SIZE`) for consistent `inline|resource|auto` payload handling.
- Added OS Downloads MCP tools in `tools/os_downloads.py`:
  `os_downloads.list_products`, `os_downloads.get_product`,
  `os_downloads.list_product_downloads`, `os_downloads.list_data_packages`,
  `os_downloads.prepare_export`, and `os_downloads.get_export`.
- Added OS Net MCP tools in `tools/os_net.py`:
  `os_net.rinex_years`, `os_net.station_get`, and `os_net.station_log`.
- Added NGD OTA MCP discovery tools in `tools/os_tiles_ota.py`:
  `os_tiles_ota.collections`, `os_tiles_ota.tilematrixsets`, and
  `os_tiles_ota.conformance`.
- Added raster/feature capability tools:
  `os_maps.wmts_capabilities`, `os_maps.raster_tile`,
  `os_features.wfs_capabilities`, and `os_features.wfs_archive_capabilities`.
- Added missing search-path tools:
  `os_places.radius`, `os_places.polygon`,
  `os_linked_ids.identifiers`, `os_linked_ids.feature_types`,
  and `os_linked_ids.product_version_info`.
- Added OS cache/export resources:
  `resource://mcp-geo/os-cache-index`,
  `resource://mcp-geo/os-cache/{file}`,
  `resource://mcp-geo/os-exports-index`,
  and `resource://mcp-geo/os-exports/{file}`.
- Added QGIS linkage tools in `tools/os_qgis.py`:
  `os_qgis.vector_tile_profile` and `os_qgis.export_geopackage_descriptor`
  with `delivery=inline|resource|auto` support and OS VTS style artifact hints.

### Changed
- Removed the dedicated `os_apps.render_warwick_leamington_3d` tool and
  corresponding `ui://mcp-geo/warwick-leamington-3d` resource from discovery.
- Added an MCP-Apps payload size guard in `tools/os_apps.py` so oversized
  embedded HTML is downgraded to URI/text delivery before crossing the 1MB
  transport ceiling.
- Removed legacy Warwick/Leamington 3D artifacts from the repo:
  `ui/warwick_leamington_3d.html` and
  `scripts/build_warwick_leamington_wards_premises_3d.py`.
- Expanded `scripts/os_catalog_refresh.py` coverage to include OFA root,
  OFA queryables probes, OS Downloads root, OS Net root, and explicit
  Road/Outdoor raster style probes; refreshed `resources/os_catalog.json`.
- Updated MCP tool registration/search metadata in `server/mcp/tools.py` and
  `server/mcp/tool_search.py` for new OS families and discovery coverage.
- Extended observability with `mcp_tool_delivery_resource_fallback_total`
  and wired OS Downloads export lifecycle structured logging for
  `requested`, `queued`, `completed`, and `failed` states.

### Fixed
- Hardened `os_poi` source-entry extraction to safely ignore non-object rows
  instead of raising when malformed payloads are encountered.
- Restored coverage gate after OS catalog/tooling wave additions with focused
  branch tests for delivery, downloads, capabilities, OS client branches, and
  resource-catalog path guards.
- Fixed STDIO `resources/read` handling so `resource://mcp-geo/*` data resources
  are now resolvable (matching HTTP resource delivery behavior).
- Fixed `/tools/call` request validation to return `400 INVALID_INPUT` for
  non-object JSON bodies instead of surfacing `500 INTERNAL_ERROR`.
- Fixed `/tools/search` request validation to return `400 INVALID_INPUT` for
  non-object JSON bodies instead of surfacing `500 INTERNAL_ERROR`.
- Fixed `/maps/static/osm` large-size rendering to stitch multiple OSM tiles so
  outputs honor requested sizes above 256px.
- Fixed QGIS GeoPackage descriptor resource prefix generation to sanitize
  user-provided `layerName` components before filesystem/resource URI use.
- Fixed Docker build packaging to include the OS vector style submodule path
  (`submodules/os-vector-tile-api-stylesheets`) while still ignoring other
  submodule content.
- Fixed Docker runtime intent clarity by removing `EXPOSE 8000` from the
  default STDIO image configuration.
- Fixed Playwright local-layer test network stubbing to match `shpjs` script
  URLs using a resilient wildcard pattern instead of one exact CDN URL.

### Tests
- Added POI evaluation harness scenarios (`B011A`/`B011B`/`B011C`) so full-tool
  coverage checks include `os_poi.search`, `os_poi.nearest`, and `os_poi.within`.
- Added branch-coverage tests for `os_poi` parser/normalization edges,
  `os_maps` helper/validation paths, playground event pruning/invalid payload
  handling, and `server/main`/`server/observability` edge paths.
- Updated UI tool/resource and evaluation tests to remove
  Warwick/Leamington-specific widget expectations and assert size-guard
  behavior for embedded content delivery.
- Re-ran full regression and coverage gate (`pytest -q`) plus playground
  Playwright suite (`npm --prefix playground run test`).
- Added test suites for new OS capability/delivery work:
  `tests/test_os_downloads_tools.py`, `tests/test_os_new_capability_tools.py`,
  `tests/test_os_places_new_tools.py`, and `tests/test_os_delivery.py`.
- Extended existing suites (`tests/test_os_common.py`, `tests/test_resource_catalog.py`,
  `tests/test_resources_data_catalog.py`, `tests/test_tool_upstream_endpoint_contracts.py`,
  `tests/test_os_catalog_snapshot.py`) for new endpoint/resource contracts and error paths.
- Added `tests/test_os_qgis_tools.py` and expanded observability/downloads
  branch tests for delivery fallback metrics and export lifecycle logging.

## [0.2.12] - 2026-02-11
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
- Added `os_apps.render_warwick_leamington_3d` (`ui://mcp-geo/warwick-leamington-3d`) for a 3D wards + premises types view.
- Added `os_map.inventory` and `os_map.export` to orchestrate bounded inventories and export snapshots as resources.
- Added `scripts/vscode_trace_snapshot.py` to snapshot VS Code trace logs into `logs/sessions/` and generate a report via `scripts/trace_report.py`.
- Added `scripts/rate_limit_assessor.py` to probe traffic levels and recommend `RATE_LIMIT_PER_MIN` from observed 429 ratio/latency behavior.

### Changed
- VS Code workspace MCP config now lives in `.vscode/mcp.json` (stdio/http + trace profiles); removed legacy `mcp.servers` registration from `.vscode/settings.json`.
- VS Code stdio servers now launch via `scripts/vscode_mcp_stdio.py` so host VS Code sessions can use the repo venv (`.venv/`) instead of relying on global Python deps.
- Updated `mcp.json` STDIO entries to run via `python3 scripts/os-mcp` (works even if the wrapper script is not marked executable).
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
- Devcontainer PostGIS now defaults to a random free host port (instead of pinning `5433`) to avoid port conflicts; set `MCP_GEO_POSTGIS_HOST_PORT` to pin it.
- `os_features.query` now returns `numberMatched` (and `numberReturned`) when provided by the upstream NGD features API, so clients can size queries before paging or exporting.
- Raised default `RATE_LIMIT_PER_MIN` from 120 to 207 after local calibration on `POST /tools/call` traffic profile.
- Evaluation audit logs now include per-task `429` summaries (`429 Rate-limit hits` and `429 by tool`) to expose backoff reliance.
- Updated MCP core protocol default from `2025-06-18` to `2025-11-25` and added explicit
  version negotiation (`2025-11-25`, `2025-06-18`, `2025-03-26`, `2024-11-05`) in stdio/http
  initialize flows.
- Streamable HTTP now validates `MCP-Protocol-Version` against supported and negotiated
  session versions, and returns `mcp-protocol-version` on responses.
- `os_mcp.descriptor` now reports `supportedProtocolVersions` and
  `mcpAppsProtocolVersion` (`2026-01-26`) for client diagnostics.
- Playground setup now shows a version matrix (server package, active/supported MCP core
  versions, MCP Apps protocol server/host, playground client version, MCP SDK dependency)
  and sources client version from `playground/package.json` instead of hardcoded values.
- Playground Playwright config now uses port `4173` with `--strictPort` to avoid flaky
  collisions on the default Vite port during local test runs.

### Fixed
- `os_features.query` now uses OS NGD OGC API Features (`features/ngd/ofa/v1/collections/{collection}/items`) and supports basic paging via `limit` + `pageToken` (`nextPageToken` in responses).
- `os_linked_ids.get` now uses OS Linked Identifiers (`search/links/v1/identifierTypes/{identifierType}/{identifier}`) with optional identifier type inference.
- `os_vector_tiles.descriptor` now emits the correct upstream tile template (`/vts/tile/{z}/{y}/{x}.pbf`).
- OS catalog NGD per-collection item probes now use a small bbox to avoid timeouts in dense areas.
- `os_map.inventory`/`os_map.export` schemas now declare `layers` with a strict array `items` shape (via `anyOf`) to avoid strict tool schema validation failures.
- Settings now ignore empty env var values so VS Code MCP `${env:VAR}` expansions don't clobber defaults with empty strings.
- NOMIS concept and codelist definition tools now use the correct `.def.sdmx.json` endpoints and `nomis.query` resolves common Census GSS geography codes (OA/LSOA/MSOA/ward) via NOMIS `geography/TYPE*` lookups.
- Upstream JSON parse failures are now normalized consistently across OS, ONS, and admin lookup clients as `502` + `UPSTREAM_INVALID_RESPONSE`.
- Initialize handlers no longer echo unsupported client protocol versions; they now return
  a negotiated supported version.

### Tests
- Added NOMIS dataset summary/filter/limit coverage and strengthened stats-routing comparison assertions.
- Added STDIO elicitation tests (accept/cancel/unavailable + wire round-trip) and stats-routing input validation coverage.
- Added STDIO + HTTP Streamable elicitation coverage for `ons_select.search`.
- Expanded evaluation coverage for ONS dataset selection and catalog validation.
- Expanded live ONS catalog validation to check all datasets with throttling/backoff controls.
- Live ONS catalog tests now validate entry fields and surface timeout/error summaries.
- Added endpoint matrix coverage for `/health`, `/tools/*`, `/resources/*`, `/playground/*`, and `/metrics`.
- Added upstream URL contract tests across OS, ONS, NOMIS, and admin lookup tools to catch endpoint-shape regressions.
- Added invalid-JSON regression tests for `tools/os_common.py`, `tools/ons_common.py`, and `tools/admin_lookup.py`.
- Added `tests/test_rate_limit_assessor.py` for rate-limit probe recommendation and metric parsing logic.
- Added `tests/test_evaluation_audit_rate_limits.py` to verify per-task `429` audit summaries and result/utilization reporting.
- Added protocol negotiation coverage (`tests/test_protocol_versions.py`) plus stdio/http
  initialize and header-validation regression tests.
- Extended playground smoke coverage to assert version matrix and MCP Apps protocol labels.
- Added `os_maps.render` overlay/inventory alignment coverage in
  `tests/test_os_map_tools.py`.
- Added Playwright `boundary_explorer_local_layers` coverage for local
  GeoJSON + Shapefile.zip imports and polygon-driven selection behavior.
- Added ONS filter-output streaming/resource pipeline: `ons_data.get_filter_output`
  now supports `delivery=inline|resource|auto` and writes large exports to
  `resource://mcp-geo/ons-exports/*` with index resource `resource://mcp-geo/ons-exports-index`.
- Added NOMIS workflow profiles resource (`resource://mcp-geo/nomis-workflows`)
  and linked NOMIS-routed `os_mcp.route_query` guidance to that profile catalog.
- Added boundary-cache maturity/staleness reporting (`maturity` + `staleness`)
  across cache status surfaces, and explicit fallback-reason metadata for
  `admin_lookup.search_cache` live fallback paths.
- Added hybrid boundary/code-list pack resources and refresh pipeline:
  source manifests + pack indexes are now exposed as resources, with
  `scripts/pack_cache_refresh.py` generating checksum/cache metadata.

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
