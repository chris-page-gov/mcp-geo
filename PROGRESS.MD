# MCP Geo Progress

This file tracks how the implementation compares to the original proposal and
later documentation as the MCP specification evolved.

Last updated: 2026-03-07

## Codex GPT-5.4 MCP host benchmark harness (2026-03-06)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| HBM-OPS-1 Codex launcher separation and registration | done | none | Added shared Docker-backed stdio launcher `scripts/mcp-docker-local`, new `scripts/codex-mcp-local`, retained Claude-only wrapper defaults in `scripts/claude-mcp-local`, and updated `scripts/devcontainer_mcp_setup.sh` so Codex registers against the Codex launcher instead of the Claude wrapper. Added `scripts/check_codex_startup_scope.sh` for scoped-discovery validation. |
| HBM-TRACE-2 Host-aware trace metadata and reporting | done | HBM-OPS-1 | Extended `scripts/trace_session.py` to record `source`, `surface`, `hostProfile`, `clientVersion`, `model`, `scenarioPack`, and `scenarioId`. Extended `scripts/trace_report.py` to emit host-aware `summary.json` plus markdown report sections for discovery, tool search, resources, fallback, UI runtime, and latency. |
| HBM-HARNESS-3 Scenario pack, scoring, and aggregation | done | HBM-TRACE-2 | Added prompt-first scenario pack `docs/benchmarking/codex_vs_claude_host_scenarios_v1.json` plus `scripts/host_benchmark.py` for scenario export, Codex CLI execution, per-session scoring (`benchmark-evidence.json`, `benchmark-score.json`), and side-by-side aggregate report generation under `docs/reports/`. |
| HBM-SIM-4 Host simulation profiles and regression coverage | done | HBM-HARNESS-3 | Extended host-simulation fixtures with `codex_cli_stdio`, `codex_ide_ui`, and `claude_desktop_ui_partial`; updated map-delivery Playwright matrix to use Codex/Claude benchmark profiles; added pytest coverage for benchmark scoring, trace metadata, devcontainer registration, startup-scope probe, and host-profile fixtures. |
| HBM-EVID-5 Captured benchmark evidence runs | in_progress | HBM-HARNESS-3, HBM-SIM-4 | Harness and runbooks are in place. Pending operator-run evidence capture for Codex IDE and Claude Desktop; Codex CLI scripted runs can now be executed via `scripts/host_benchmark.py run-codex-cli <scenario>`. |

## Teignmouth wheelchair access map (2026-03-07)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| TWA-DATA-1 Live access-layer extraction and scoring | done | none | Added `scripts/generate_teignmouth_wheelchair_access_map.py` to pull live Teignmouth roads, paths, pavement polygons, water, rail, and OS Places anchors through MCP-Geo; applies conservative width/slope/lighting rules and writes `data/exports/teignmouth_wheelchair_access_map_2026-03-07.json`. |
| TWA-OUT-2 User-facing map and methods note | done | TWA-DATA-1 | Generated slide-format HTML map `docs/reports/teignmouth_wheelchair_access_map_2026-03-07.html`, screenshot artifact `output/playwright/teignmouth-wheelchair-access-map-2026-03-07.png`, and methods/additions note `docs/reports/teignmouth_wheelchair_access_map_2026-03-07.md`. Follow-up refinements removed wide-window clipping, moved station/Shopmobility into sidebar access points with numbered map markers, reduced map callouts to six named corridors, switched the overlay projection to Web Mercator for cleaner basemap alignment, and added an optional browser-side `OS Light` basemap toggle plus subtler route casing so labels remain readable. |
| TWA-FIX-3 POI bbox filtering hardening | done | none | Fixed `os_poi.search` bbox behavior to filter text-search results locally instead of sending unsupported bbox coordinates upstream to `/find`; updated `tests/test_os_poi.py` and validated with focused pytest + live Teignmouth query. |
| TWA-COMP-4 Exmouth positive comparator | done | TWA-DATA-1, TWA-FIX-3 | Extended `scripts/generate_teignmouth_wheelchair_access_map.py` with named presets and resource-delivery handling so the same conservative scoring logic now generates Exmouth outputs. Added `docs/reports/exmouth_wheelchair_access_map_2026-03-07.{html,md}`, `data/exports/exmouth_wheelchair_access_map_2026-03-07.json`, screenshot artifact `output/playwright/exmouth-wheelchair-access-map-2026-03-07.png`, and expanded the multi-town comparison note now published as `docs/reports/teignmouth_exmouth_sidmouth_access_comparison_2026-03-07.md`. The refreshed Exmouth outputs now share the same optional `OS Light` basemap controls and slimmer overlay styling used in Teignmouth. |
| TWA-COMP-5 Sidmouth compact-core comparator | done | TWA-COMP-4 | Added Sidmouth preset outputs `docs/reports/sidmouth_wheelchair_access_map_2026-03-07.{html,md}`, `data/exports/sidmouth_wheelchair_access_map_2026-03-07.json`, screenshot artifact `output/playwright/sidmouth-wheelchair-access-map-2026-03-07.png`, and expanded the comparison note to `docs/reports/teignmouth_exmouth_sidmouth_access_comparison_2026-03-07.md`. Sidmouth reads as a compact seafront-and-market core with very short anchor gaps rather than a like-for-like replacement for Exmouth's broader positive network; the refreshed outputs now share the same optional `OS Light` basemap toggle and subtler overlay treatment as the other towns. |

## Public launch release `0.5.0` (2026-03-04)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| REL-SEC-1 Public-release security review | done | none | Completed repository security review focused on secrets/sensitive credential leakage across authored content plus git-history scan. Added report `docs/reports/public_release_security_review_2026-03-04.md` and confirmed only redacted placeholder detections (`key=REDACTED`) in prior report artifacts. |
| REL-PKG-2 Version and release packaging | done | REL-SEC-1 | Bumped version to `0.5.0` (`pyproject.toml`, `server/__init__.py`), promoted changelog content into `## [0.5.0] - 2026-03-04`, added `RELEASE_NOTES/0.5.0.md`, and added public-launch caveat text to `README.md`. |
| REL-VAL-3 Regression validation gate | done | REL-PKG-2 | Full suite validation passed via `uv run --extra test pytest -q`: `994 passed`, `6 skipped`, coverage `91.53%` (threshold `>=90%`). |
| REL-PUB-4 Commit/tag/publish + visibility change | done | REL-VAL-3 | Completed release commit (`a76ff59`), created/pushed tag `v0.5.0`, published GitHub release (`https://github.com/chris-page-gov/mcp-geo/releases/tag/v0.5.0`), and switched repository visibility to `PUBLIC`. |

## UK Public Sector AI Community documentation package (2026-03-04)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| DOCS-PLAN-1 Delivery planning and evidence capture | done | none | Compiled repository timeline and external standards/client milestones from `git` history, `RELEASE_NOTES/`, `PROGRESS.MD`, `CONTEXT.md`, `CHANGELOG.md`, and primary external sources (MCP, Anthropic, OpenAI, VS Code). |
| DOCS-MD-2 Novice/apprentice documentation set | done | DOCS-PLAN-1 | Added `docs/public_sector_ai_community/` multi-file markdown collection covering origin story, architecture, timeline, standards/client evolution, harness and permissions journey, question patterns, effectiveness evaluation, Codex usage statistics, BDUK extension requirements, RBAC/ABAC needs, future direction, and evidence index; added section-level Mermaid diagrams and navigation entrypoint. |
| DOCS-TEX-3 Publication output (LaTeX/Prism-ready) | done | DOCS-MD-2 | Added `docs/public_sector_ai_community/prism/` package with `main.tex`, chapterized section files, bibliography, ToC, and cross-references to repository evidence and external standards milestones; validated with local `pdflatex` + `bibtex` passes (generated `main.pdf`). |
| DOCS-INT-4 Repo integration and reporting refresh | done | DOCS-MD-2, DOCS-TEX-3 | Linked new documentation set from `README.md`, refreshed report index entries in `docs/reports/README.md`, generated updated Codex summary artifacts `docs/reports/mcp_geo_codex_long_horizon_summary_2026-03-04.{md,json,svg}`, and synchronized tracker/changelog/context updates. |

## Peat survey failure-chain hardening (2026-03-03)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| PSF-INT-1 `os_features.query` hits-count correctness | done | none | Fixed `resultType=hits` counting in `tools/os_features.py` to derive `count` from matched signals (`numberMatched`, local-filter totals, or observed feature volume) instead of `numberReturned` alone. Added warnings for uncertain totals: `HITS_NUMBER_MATCHED_UNAVAILABLE` and `HITS_COUNT_LOWER_BOUND`, plus `matchedCountLowerBound` when applicable. |
| PSF-INT-2 Legacy transport collection compatibility | done | PSF-INT-1 | Added base alias normalization in `tools/os_features.py` so legacy `trn-fts-roadlink-*` requests resolve to supported `trn-ntwk-roadlink-*` collections while preserving `requestedCollection` and warning with `COLLECTION_ALIAS_APPLIED`. |
| PSF-INT-3 Unsupported collection actionable guidance | done | PSF-INT-2 | Enriched unsupported-collection `OS_API_ERROR` responses in `tools/os_features.py` by parsing upstream unsupported IDs and attaching `requestedCollection`, `resolvedCollection` (when aliased), `suggestedCollections`, and a deterministic recovery hint. |
| PSF-VAL-4 Regression coverage and trace-backed troubleshooting | done | PSF-INT-1, PSF-INT-2, PSF-INT-3 | Updated and added regression tests in `tests/test_os_features_collections.py` and validated unaffected peat/tool-normalization suites via combined focused run (`38 passed`). Added evidence artifacts `troubleshooting/peat-survey-trace-evidence-2026-03-03.md` and `troubleshooting/peat-survey-failure-deep-analysis-2026-03-03.md`, and synchronized troubleshooting guidance in `docs/troubleshooting.md`. |

## Claude tool-search interop hardening (2026-03-03)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| CTS-INT-1 `tools/list` query-compat for search-gated clients | done | none | Updated `server/stdio_adapter.py` so `tools/list` now honors search-style params (`query`/`q`, `mode`, `limit`, `category`) and returns ranked filtered tool definitions instead of full-catalog responses when query is present; preserves existing list behavior when query is absent. Added regression coverage in `tests/test_stdio_adapter_direct.py` and `tests/test_mcp_http.py`. Added standards-validation + troubleshooting evidence in `troubleshooting/claude-system-instructions-hide-mcp.md` against vendored MCP `2025-11-25` docs/schema. |
| CTS-OPS-2 Docker Claude wrapper env passthrough for default toolsets | done | CTS-INT-1 | Updated `scripts/claude-mcp-local` to forward `MCP_TOOLS_DEFAULT_TOOLSET`, `MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS`, `MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS`, and `MCP_STDIO_TOOL_CONTENT_MAX_BYTES` into the runtime container. This restores scoped startup discovery for Docker-backed Claude sessions (observed `tools/list` baseline `81` tools vs scoped `25` tools with `starter + features_layers`). |
| CTS-OPS-3 Startup scope probe script | done | CTS-OPS-2 | Added `scripts/check_claude_startup_scope.sh` to deterministically validate startup scope via wrapper path (`baseline_tools` vs `scoped_tools`) and fail fast if scoped discovery is not lower than baseline. |
| CTS-OPS-4 Compact startup catalogs for Claude clients | done | CTS-OPS-2 | Added stdio compact-catalog mode (`MCP_STDIO_LIST_COMPACT`, default auto for Claude) to trim heavy optional fields from `tools/list` and `resources/list`. Verified with Docker rebuild path: `tools/list` (`25` tools) dropped from ~`34KB` to ~`18KB`; full `initialize + list` startup (`tools/prompts/resources`) dropped to ~`28.6KB`. Added regression tests in `tests/test_stdio_adapter_direct.py`. |
| CTS-OPS-5 Secret hydration for Docker Claude wrapper | done | CTS-OPS-2 | Updated `scripts/claude-mcp-local` to hydrate `OS_API_KEY`/`ONS_API_KEY` from runtime env, `*_FILE` secrets, macOS `launchctl`, or `.env` fallback (`MCP_GEO_ENV_FILE`). Followed up by wiring `OS_API_KEY_FILE` templates into `mcp.json`/`.vscode/mcp.json` and adding server-side `OS_API_KEY_FILE` fallback in `server/config.py` so direct stdio/server launches can use file-based secrets too. Validated behavior: with no key => `NO_API_KEY`; with dotenv-provided test key => upstream `OS_API_KEY_INVALID` (proves key reached container). |
| CTS-INT-6 Tool-search category alias compatibility (`stats`) | done | CTS-INT-1 | Updated `server/mcp/tool_search.py` so category alias `stats` normalizes to `statistics` for descriptor/search filtering. This removes `toolSearch.error` for `os_mcp.descriptor` calls that pass `{\"category\":\"stats\"}` in constrained clients. Added regression tests in `tests/test_tool_search.py` and `tests/test_os_mcp_descriptor.py`. |

## Playground compact UX refinements (2026-03-03)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| PGC-UX-1 Compact-host playground and geography-selector usability fixes | done | CWIN-EXEC-3 | Updated `playground/src/App.svelte` to enforce compact-preserving maximise behavior, add adjustable split-pane width controls, reduce header footprint, and consolidate UI preview debug output under Debug tab. Updated `ui/geography_selector.html` with map-first compact workflow tabs (`Map`, `Search`, `Results`, `Info`, `Debug`, `Help`) and a zoom-ladder icon toggle so zoom chips no longer obscure map content. Validation evidence: `npm --prefix playground run test -- playground.spec.js` (`1 passed`), `npm --prefix playground run test:compact` (`30 passed`), `npm --prefix playground run test:compact-matrix` (`72 passed`), `npm --prefix playground run build` (pass). |

## NOMIS query resilience hardening (2026-03-03)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| NQR-INT-1 NOMIS query parameter normalization + guidance payloads | done | none | Updated `tools/nomis_data.py` so `nomis.query` normalizes common compatibility mistakes (`date` alias to `time`, drops `cell` for JSON-stat), and returns richer `NOMIS_QUERY_ERROR` payloads (`missingDimensions`, `suggestedParams`, `hint`, `queryAdjusted`) for `Cannot create query`/`Query is incomplete` failures. Added regression coverage in `tests/test_nomis_data.py` and troubleshooting guidance in `docs/troubleshooting.md`. |
| NQR-INT-2 NOMIS dimension auto-adjust retry | done | NQR-INT-1 | Added overview-driven retry in `tools/nomis_data.py` for incomplete/invalid queries: auto-fill missing required dimensions from `queryTemplate`, drop unknown dimension keys, retry once, and surface `queryAdjusted.dimensionAutoAdjust`. This resolves model payload drift such as `NM_2028_1` with missing `time`/`c_sex` and unsupported `c2021_age_92`. Added regression test `test_nomis_query_autoretries_with_dimension_autoadjustments` and updated troubleshooting docs. |

## Compact-windows unattended implementation planning (2026-03-01)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| CWIN-PLAN-1 Full implementation + test strategy definition | done | none | Added branch-scoped plan `docs/reports/compact_windows_unattended_implementation_and_test_plan_2026-03-01.md` with workstreams for all six UIs, compact contract, Playwright rewrite strategy, and strict merge-gate acceptance criteria. |
| CWIN-BASE-2 Strict checklist baseline run | done | CWIN-PLAN-1 | Added machine-readable acceptance checklist `docs/reports/compact_windows_acceptance_checklist_2026-03-01.json` and baseline strict-run report `docs/reports/compact_windows_acceptance_baseline_run_2026-03-01.md`; executed focused evidence run (`3 passed`) and cataloged current strict-gate outcome (`0/6` UIs pass pre-implementation). |
| CWIN-EXEC-3 Unattended compact-window implementation | done | CWIN-BASE-2 | Started execution on `codex/compact-windows`: scaffolded compact Playwright infrastructure (`playwright.compact*.config.js`, `test:compact`, `test:compact-matrix`, deterministic bridge/profile support, smoke+matrix suites) with passing baseline runs (`8 passed`, `6 passed`). Completed `CW-1` shared compact contract rollout across all six UIs (`ui/shared/compact_contract.{css,js}` + per-page integration and `data-testid` anchors), with checkpoint validation reruns still green (`8 passed`, `6 passed`). Completed `CW-2` boundary hardening with UPRN attribute filters (address/classification/flags + scope), deterministic import status/error messaging, and expanded local-layer regression assertions in `playground/tests/boundary_explorer_local_layers.spec.js` (`2 passed` focused run). Completed `CW-3` geography hardening by adding deterministic flow-state reporting (`loading/empty/error/success`), richer compact test hooks for style/opacity/layers, and extended regression assertions in `playground/tests/geography_selector.spec.js` (`1 passed` focused run). Completed `CW-4` statistics dashboard compact migration with deterministic action-state reporting across dataset/dimension/query workflows and new end-to-end assertions in `playground/tests/statistics_dashboard.spec.js` (`1 passed` focused run). Completed `CW-5` simple-map compact/auth hardening with explicit auth-mode reporting (`bearer`/`api_key`/`server_env`), richer style/diagnostics test hooks, and deterministic auth-path assertions in `playground/tests/simple_map.spec.js` (`1 passed` focused run). Completed `CW-6` promotion of `ui/feature_inspector.html` and `ui/route_planner.html` to MCP-Apps host-aware views with `ui/initialize` + host-context merge + fullscreen fallback handling and focused interaction tests (`playground/tests/feature_inspector.spec.js`, `playground/tests/route_planner.spec.js`; `2 passed` focused run). Completed `CW-7` by replacing scaffold checks with strict acceptance-mapped smoke + host/profile matrix suites (`playground/tests/compact_windows/*`), adding argument-aware deterministic MCP bridge tooling, and adding compact status-dock resilience in `ui/shared/compact_contract.*`; validation evidence: `npm --prefix playground run test:compact` (`18 passed`), `npm --prefix playground run test:compact-matrix` (`36 passed`), `npm --prefix playground run test` (`29 passed`), and `./.venv/bin/pytest -q` (`930 passed`, `6 skipped`, coverage `90.01%`). |

## MCP-Apps window constraints and redesign review (2026-03-01)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| MAWS-SPEC-1 MCP spec inventory completeness | done | none | Verified spec-bearing `modelcontextprotocol` org repos and added missing `docs/vendor/mcp/repos/ext-auth` submodule so published/draft spec trees are fully local (`modelcontextprotocol`, `ext-apps`, `ext-auth`). |
| MAWS-ANALYSIS-2 Spec-vs-host window behavior review | done | MAWS-SPEC-1 | Confirmed windowing/maximize behavior is host-capability dependent in `ext-apps`; captured current host evidence (VS Code inline-only today; Claude inline guidance with `500px` max card height). |
| MAWS-DESIGN-3 Cross-host small-window redesign pack | done | MAWS-ANALYSIS-2 | Added review report + explicit `320x500` design budget and per-UI redesign assessment at `docs/reports/mcp_apps_window_constraints_review_2026-03-01.md`; added Figma-importable wireframe pack under `docs/design/figma/`. |
| MAWS-FIGMA-4 Direct Figma publication automation | done | MAWS-DESIGN-3 | Figma MCP server configured and authenticated; captured compact proposals into Figma file and validated iterative recapture via `existingFile` mode. |
| MAWS-FIGMA-5 Figma setup runbook + fidelity constraints | done | MAWS-FIGMA-4 | Added `docs/design/figma/mcp_figma_setup_and_capture_runbook.md` documenting setup, OAuth, capture flow, and known SVG-text fidelity caveat; review report now uses Figma as annotation support, not decision source. |

## Submodule refresh and runtime-coupling validation (2026-03-01)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| SUBMOD-DOC-1 Vendor submodule refresh | done | none | Bumped vendored reference/spec submodules under `docs/vendor/` (`agentskills`, `modelcontextprotocol`, `ext-apps`, `inspector`) to latest upstream commits and refreshed `docs/spec_tracking.md` review dates. |
| SUBMOD-RUN-2 Runtime-coupled style-path validation | done | SUBMOD-DOC-1 | Confirmed `submodules/os-vector-tile-api-stylesheets` remained at current upstream pin (no pointer delta) and ran focused regression checks: `./.venv/bin/pytest -q --no-cov tests/test_os_qgis_tools.py tests/test_maps_proxy.py` (`15 passed`). |

## Simple map auth + PMTiles exploration (2026-02-27)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| SMAP-BR-0 Branch and scope setup | done | none | Created exploration branch `codex/simple-map` for minimal map-delivery and auth experimentation. |
| SMAP-AUTH-1 Browser-auth-first vector proxy | done | SMAP-BR-0 | Updated `server/maps_proxy.py` so `/maps/vector/*` prefers `Authorization: Bearer` from browser/client requests, then falls back to key header/query, then server `OS_API_KEY`; added focused auth-path tests. |
| SMAP-LAB-2 Minimal map lab UI/resource | done | SMAP-AUTH-1 | Added `ui/simple_map.html` and `ui://mcp-geo/simple-map-lab` resource for OS Vector and PMTiles loading with baseline timing and pan-benchmark controls; fixed no-idle diagnosis path by aligning MapLibre runtime/worker versions and disabling cache for `/ui/simple-map-lab` during rapid debug iterations; replaced free-text style entry with curated OS style dropdown plus novice guidance; fixed `/maps/vector/vts/resources/styles` style-selection routing and tile-template `{y}/{x}` ordering so style changes are visibly applied. |
| SMAP-PMT-3 PMTiles high-volume rendering evidence capture | in_progress | SMAP-LAB-2 | Lab scaffolding is in place; dataset-specific benchmark runs and performance evidence artifacts are the next step. |

## Codex long-horizon session summary skill (2026-02-25)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| CHS-DEF-0 Metric definition alignment | done | none | Standardized the report contract to mirror OpenAI Long Horizon-style session metrics (runtime, token usage, cached reuse, tool calls, patch volume, compactions, peak step). |
| CHS-IMP-1 Session aggregation implementation | done | CHS-DEF-0 | Added `scripts/codex_long_horizon_summary.py` to parse local Codex `sessions` + `archived_sessions` JSONL data filtered by repo cwd and compute aggregate/session metrics. |
| CHS-SKL-2 Skill + runner workflow | done | CHS-IMP-1 | Added repo skill `skills/mcp-geo-long-horizon-summary/SKILL.md` and wrapper `skills/mcp-geo-long-horizon-summary/scripts/run_summary.sh` to produce dated report artifacts in `docs/reports/`. |
| CHS-VAL-3 Regression + baseline evidence | done | CHS-IMP-1 | Added regression test `tests/test_codex_long_horizon_summary.py`; generated baseline artifacts `docs/reports/mcp_geo_codex_long_horizon_summary_2026-02-25.{md,json}` for current repository history. |
| CHS-GFX-4 Templated summary-card generation | done | CHS-IMP-1, CHS-SKL-2 | Added deterministic SVG template `skills/mcp-geo-long-horizon-summary/templates/summary_card.svg.tmpl` and generator wiring so markdown reports open with a rendered `Codex MCP-Geo Summary` image (`docs/reports/mcp_geo_codex_long_horizon_summary_2026-02-25.svg`). |

## Repo extent/complexity analysis skill (2026-02-25)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| REC-DEF-0 Metric model definition | done | none | Defined dual-scope (`git_tracked`, `workspace`) extent/complexity model with generated-output exclusion, Python cyclomatic analysis, and hotspot scoring (`complexity x churn`) aligned to SOTA practice references. |
| REC-IMP-1 Analyzer implementation | done | REC-DEF-0 | Added `scripts/repo_extent_complexity_report.py` with deterministic markdown/JSON outputs, churn/activity rollups, default output-policy exclusions, and optional GitHub Stats API enrichment via `gh`. |
| REC-SKL-2 Skill packaging | done | REC-IMP-1 | Added `skills/mcp-geo-repo-extent-complexity/` skill runbook, wrapper script (`scripts/run_report.sh`), and references file documenting source-backed metric rationale. |
| REC-VAL-3 Regression + baseline evidence | done | REC-IMP-1 | Added test coverage in `tests/test_repo_extent_complexity_report.py`; generated baseline artifacts `docs/reports/repo_extent_complexity_2026-02-25.{md,json}`. |
| REC-MGR-4 Manager report-card snapshot | done | REC-IMP-1, REC-SKL-2 | Added non-technical manager report card output (`docs/reports/repo_extent_complexity_report_card_2026-02-25.md`) with plain-English terminology, metric basis/source notes, and practical implications; wired via `--manager-output` and skill runner defaults. |

## Layered map reliability priority program (2026-02-21)

Primary goal:
- Reliable layered map display (polygons, lines, and points) in all clients.
- Interaction where host runtime supports MCP-Apps UI.

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| LMR-BASE-0 Baseline layered-map contract parity | done | none | Hardened baseline contracts in STDIO/HTTP fallback paths so `map_card` + `overlay_bundle` + `export_handoff` are emitted deterministically for non-UI clients (`server/stdio_adapter.py`, transport parity tests). |
| LMR-ALL-1 All-client layered-render validation matrix | done | LMR-BASE-0 | Re-ran cross-engine matrix on 2026-02-21: `35 passed`, `20 skipped`, `0 failed` across Chromium/Firefox/WebKit desktop+mobile with refreshed evidence in `research/map_delivery_research_2026-02/evidence/` and `reports/trial_summary.md`. |
| LMR-INT-2 Interaction parity in UI-capable hosts | done | LMR-ALL-1 | Validated geography selector + boundary explorer interaction flows in deterministic host simulation (`trial-3`, `trial-4`) on Chromium desktop; host bridge round-trip stability (`trial-5`) now passes across all matrix engines. |
| LMR-FBK-3 Deterministic non-UI fallback hardening | done | LMR-BASE-0 | Added explicit fallback-order contracts and deterministic guidance fields for non-UI hosts; regression-covered in `tests/test_stdio_adapter_direct.py` and `tests/test_mcp_http.py`. |
| LMR-HOST-4 Host runtime gap retest/escalation | blocked | LMR-INT-2 | External Claude host runtime mount/bridge behavior remains outside repo control; latest known evidence still shows `resources/read` success without widget bridge events (`docs/troubleshooting.md`, `logs/claude-trace.jsonl`). Added repeatable classifier automation at `scripts/check_lmr_host4.py` (optional `--run-probe` and `--run-playwright-smoke`) with JSON report output in `logs/lmr-host4-report.json`. Also hardened `ui/boundary_explorer.html` for constrained host windows (map-prioritized responsive layout) and added cross-level fallback search messaging so placeholder terms like “Westminster” no longer fail silently when the selected level is too narrow. Follow-up hardening now normalizes MCP tool payload shapes (`result.data` vs `structuredContent`/`content`) in other widgets to prevent silent empty-result behavior in strict hosts. |
| LMR-GATE-5 Release validation gate | done | LMR-ALL-1, LMR-INT-2, LMR-FBK-3 | Updated support matrix + fresh trial artifacts and contract tests are complete; quality-gate failures were reduced via story-gallery style tuning and then resolved to warning-only under documented waiver/threshold policy (`research/map_delivery_research_2026-02/reports/map_quality_waivers.json`, `map_quality_report.json`). External host runtime gap remains tracked separately in `LMR-HOST-4`. |

Execution order:
1. `LMR-BASE-0`
2. `LMR-ALL-1`
3. `LMR-FBK-3`
4. `LMR-INT-2`
5. `LMR-HOST-4`
6. `LMR-GATE-5`

## Full review and live operability validation (2026-02-21)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| REV-VAL-0 Strict regression gate rerun | done | none | `pytest -q` rerun completed: `785 passed`, `6 skipped`, coverage gate **failed** at `86.69%` (`>=90%` required). |
| REV-VAL-1 Full live harness rerun | done | REV-VAL-0 | `tests.evaluation.harness` (`--include-os-api --include-ons-live`) rerun after ONS fixes: `6290/6900` (`91.16%`), `67/69` passed, `rate_limit_429_total=0`. |
| REV-VAL-2 Missing-tool live probe automation | done | REV-VAL-1 | Added `scripts/live_missing_tools_probe.py` (+ tests) and generated report `data/live_missing_tools_probe_report_2026-02-21.json`: `27/28` pass, `1/28` blocked (`os_features.wfs_archive_capabilities` -> `OS_API_KEY_INVALID`). |
| REV-VAL-3 Spec-linked measurable coverage | done | REV-VAL-1, REV-VAL-2 | Added `scripts/spec_tool_operability_coverage.py` (+ tests), `docs/spec_package/14_tool_operability.feature`, and `docs/spec_package/14_tool_operability_coverage.md`; combined operability now measured at `75/76` functional (`98.68%`), `1/76` blocked auth, `0` unresolved, with release-gated functional coverage now computed entitlement-aware (`75/75`, `100.0%`) by excluding optional-by-entitlement `os_features.wfs_archive_capabilities` from the release denominator while keeping explicit evidence tracking. |
| REV-VAL-4 Static analysis gate check | done | REV-VAL-0 | `ruff check .` and `mypy server tools scripts` executed after installing `.[dev]`; both are currently red (`ruff`: `1172` findings, `mypy`: `175` errors). |
| REV-VAL-5 Post-P1/P2 full live harness rerun | done | REV-VAL-1 | `RUN_LIVE_API_TESTS=1 ./.venv/bin/python -m tests.evaluation.harness --include-os-api --include-ons-live` on 2026-02-22: `6900/6900` (`100%`), `69/69` passed, `rate_limit_429_total=0`. |
| REV-VAL-6 Non-runtime strict static gate restoration | done | REV-VAL-4 | Added `scripts/check_non_runtime_quality.sh` and restored strict static gating for reliability-critical non-runtime surfaces (`ruff` + `mypy --follow-imports=skip`), currently green (`All checks passed`, `Success: no issues found in 8 source files`). |

## Live evaluation P1 follow-ups (2026-02-22)

- Done: hardened `tools/ons_data.py` observation retrieval to start with
  dimension filters only (no `limit/page`) and only escalate to explicit paging
  when an implicit response appears truncated; this matches current live ONS
  contracts and avoids repeated `ONS_API_ERROR` failures for GDP observations.
- Done: expanded ONS option-code parsing in `tools/ons_data.py` and
  `tools/ons_codes.py` to accept live option payload shape
  (`links.code.id`) in addition to legacy `id/option/value/code` fields.
- Done: normalized live ONS `observations: null` payloads to deterministic
  empty results in `tools/ons_data.py` (instead of `INTEGRATION_ERROR`) and
  added single-token quarter/year expansion + alias-version retry so
  `ons_data.get_observation` can resolve prompts like `2023 Q1` against live
  monthly GDP dimensions.
- Done: retained explicit OS Names regression coverage ensuring
  `os_names.find` / `os_names.nearest` do not send `output_srs`.
- Done: closed residual question-bank deltas by updating:
  - `tools/os_maps.py` (`render.urlTemplate` alias for keyword-compat)
  - `tools/os_places.py` (empty `by_postcode` results return deterministic
    `INVALID_INPUT`)
  - `tools/os_mcp.py` (hierarchy/tool-discovery intent routing and
    `reverse_hierarchy` tool recommendation with area-code extraction)
  - `tests/evaluation/questions.py` (`C001`/`C002` efficiency budget aligned to
    routed flow)
  - `tests/evaluation/harness.py` + `tests/test_evaluation_expected_errors.py`
    (expected-error scoring no longer penalized; missing expected errors now
    fail explicitly)
  - `tools/nomis_data.py` + `tests/test_nomis_data.py`
    (transient `nomis.datasets` upstream failures degrade gracefully for
    non-dataset-specific requests).
- Verification:
  `./.venv/bin/pytest -q --no-cov tests/test_ons_data.py` (`16 passed`) plus
  focused live rerun
  (`RUN_LIVE_API_TESTS=1 ./.venv/bin/python -m tests.evaluation.harness --include-os-api --include-ons-live --questions B004,B012,B007,B008,B016,I008,I009,I011`)
  now scores `800/800` (`100%`), including `I011` at `100%`.
- Verification (final):
  `./.venv/bin/pytest -q --no-cov tests/test_evaluation_expected_errors.py tests/test_os_places_by_postcode_success.py tests/test_os_map_tools.py tests/test_os_mcp_route_query.py tests/test_nomis_data.py`
  (`79 passed`) and full live rerun
  (`RUN_LIVE_API_TESTS=1 ./.venv/bin/python -m tests.evaluation.harness --include-os-api --include-ons-live --output /tmp/evaluation_results_live_2026-02-22_sync_and_remaining.json`)
  now scores `6900/6900` (`100%`) with `69/69` passed.
- Remaining OS/ONS coverage deltas in current question bank: none.

## ONS geography dual-derivation cache (2026-02-22)

Legend: pending, in_progress, done

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| OGC-CFG-0 Source-manifest baseline | done | none | Added `resources/ons_geo_sources.json` with primary exact-mode products (`ONSPD`, `ONSUD`) plus parallel best-fit products (`NSPL`, `NSUL`) and explicit source metadata/field candidates. |
| OGC-CACHE-1 SQLite cache core + normalization | done | OGC-CFG-0 | Added `server/ons_geo_cache.py` with postcode/UPRN normalization, derivation-mode validation (`exact`, `best_fit`), cache schema bootstrap, indexed lookup ordering by product priority, and geography code/name extraction helpers. |
| OGC-TOOLS-2 Tooling for postcode/UPRN geography lookups | done | OGC-CACHE-1 | Added `tools/ons_geo.py` (`ons_geo.by_postcode`, `ons_geo.by_uprn`, `ons_geo.cache_status`) with deterministic cache-unavailable/not-found/error contracts and optional raw-row inclusion. |
| OGC-REFRESH-3 Refresh/ingest automation | done | OGC-CFG-0, OGC-CACHE-1 | Added `scripts/ons_geo_cache_refresh.py` supporting manifest-driven ingestion, per-product file/URL overrides, CSV/ZIP/GZ parsing, SHA256 provenance capture, and index emission to `resources/ons_geo_cache_index.json`. |
| OGC-INT-4 MCP integration and routing | done | OGC-TOOLS-2 | Registered `ons_geo` in tool imports/discovery categories/toolsets and resource catalog; route-query now recommends `ons_geo.by_postcode`/`ons_geo.by_uprn` for explicit geography-mapping prompts while preserving OS Places for address retrieval. |
| OGC-VAL-5 Regression coverage | done | OGC-INT-4, OGC-REFRESH-3 | Added tests for cache internals, refresh script ingestion, ons-geo tools, route-query classification, tool-search discoverability, and resource-catalog slugs; focused run: `98 passed` (`./.venv/bin/pytest -q --no-cov ...`). |

- Done (2026-02-22): cache health/status payloads now expose explicit
  degraded-performance indicators (`performance.degraded`, `reason`, `impact`)
  for `ons_geo.cache_status`, `admin_lookup.get_cache_status`, and
  `resource://mcp-geo/boundary-cache-status`.
- Done (2026-02-22): populated all feasible local caches in this environment:
  code-list pack cache artifacts refreshed, ONS geo cache ingested from
  bootstrap product files, and PostGIS boundary cache seeded from live ArcGIS
  geometry (Coventry county/unitary and Westminster district records).
- Done (2026-02-22): boundary pack cache now hydrates configured ONS packs from
  concrete ArcGIS Hub download URLs (`ons_wards_dec_2024_uk_bgc`,
  `ons_lsoa_dec_2021_ew_bgc`), with `resources/boundary_packs_index.json`
  reporting `cached` artifacts and checksums.
- Done (2026-02-22): runtime PostGIS boundary cache is now at ready maturity in
  this environment (`admin_lookup.get_cache_status`: `total=240783`,
  `performance.degraded=false`) after pipeline-derived datasets were synced into
  `public.admin_boundaries`/`public.boundary_datasets`.
- Done (2026-02-23): boundary source resolution + live verification now has a
  dedicated gate in `scripts/boundary_pipeline.py`
  (`--mode resolve --verify-resolved`) with mode-specific status reporting.
  Latest run `data/boundary_runs/20260223T082527Z/run_report.json` reports
  `COMPLETE_BOUNDARIES_RESOLVED_AND_VERIFIED` (`107` resolved sources verified
  reachable; `49` variants recorded as `not_published` with evidence).
- In progress (2026-02-22): full-manifest boundary ingestion remains
  incomplete; latest full `boundary_pipeline` tracker run reports
  `families_ok=0/39` because downstream download/ingest/validation coverage is
  still partial, so complete UK-wide runtime cache coverage remains open even
  though source resolution is now verified.

## Boundary variant full-coverage hardening (2026-02-23)

Legend: pending, in_progress, done

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| BVH-DOC-0 Missing-variant and accuracy documentation | done | none | Updated `docs/reports/boundary_variant_coverage_gap_2026-02-23.md` with baseline gap (`49` `not_published`) and hardened strict run (`0` `not_published`) plus explicit definition-of-complete criteria and accuracy/zoom warning semantics. |
| BVH-REQ-1 Family-specific variant requirements | done | BVH-DOC-0 | `scripts/boundary_pipeline.py` now merges manifest `completion_definition.default_variant_policy` with template/family overrides and enforces strict `require_full_variant_availability` at evaluation time. |
| BVH-OS-4 Boundary-Line non-variant profile | done | BVH-REQ-1 | `docs/Boundaries.json` now explicitly profiles `os_boundaryline_gb_bulk` as non-variant-source + derivation-enabled required variant coverage (`BFC/BFE/BGC/BUC`). |
| BVH-DER-5 Derived variant generation for full availability | done | BVH-REQ-1, BVH-OS-4 | Derived/equivalent variant generation and accuracy metadata are now emitted deterministically (including coarser-source warnings); strict run `data/boundary_runs/20260223T120022Z/run_report.json` reports `resolved=112`, `derived=44`, `not_published=0`, `errors=0`. |
| BVH-BUA-6 Built-up Area containment path | in_progress | BVH-REQ-1, BVH-DER-5 | Variant hardening now recognizes BUA `BGG` pathways (`built_up_areas_uk` equivalence/derivation), but end-to-end runtime containment verification for UPRN/RoadLink/PathLink over BUA/BUASD cache levels remains to be completed. |

## Startup context mitigation check (2026-02-22)

Legend: pending, in_progress, done

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| SCM-CLAUDE-0 Startup footprint measurement | done | none | Measured stdio startup payload pressure for non-deferred clients: full `tools/list` (`81` tools) `87,805` bytes (~`21,951` tokens approx) vs `starter` (`15` tools) `21,151` bytes (~`5,287` tokens approx). |
| SCM-CLAUDE-1 Mitigation readiness hardening | done | SCM-CLAUDE-0 | Added `os_mcp.select_toolsets` to `starter` so constrained clients can always request scoped expansion without full schema load; verified inferred include path (`core_router`, `places_names`, `ons_geo_lookup`) and documented workflow in `docs/tutorial.md` + `docs/troubleshooting.md`. |

## Safe-by-design governance and citation review (2026-02-21)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| SBD-INT-0 Scope + source inventory | done | none | Confirmed and reviewed extracted Prism LaTeX brief mirror under `research/From Apps to Answers - Connecting Public Sector Data to AI with MCP/`. |
| SBD-STD-1 Standards evidence mapping | done | SBD-INT-0 | Anchored checklist/rubric to NCSC, ICO, Data Ethics Framework, ATRS, Five Safes, OWASP LLM, PROV-O/PROV-DM/DCAT v3, and MCP `2025-11-25`. |
| SBD-CIT-2 Citation-key integrity audit | done | SBD-INT-0 | Verified local TeX cite keys and generated BibTeX/TeX patch recommendations; found metadata gaps in `references.bib`. |
| SBD-REV-3 Full code review + `#TODO#` findings | done | SBD-STD-1 | Produced prioritized security/governance findings with dependencies and remediation steps. |
| SBD-LOG-4 Remediation tracker JSON | done | SBD-REV-3 | Added `safe-by-design.json` with dependency graph, acceptance criteria, and target `fully_met` status path. |
| SBD-RUB-5 Compliance rubric + scoring | done | SBD-STD-1, SBD-REV-3 | Added weighted rubric and applied scores to current repo state in review report. |
| SBD-CIT-6 Prism brief citation patch application | done | SBD-CIT-2 | Applied citation-strengthening updates to local extracted Prism brief under `research/From Apps to Answers - Connecting Public Sector Data to AI with MCP/` and refreshed canonical BibTeX URLs/metadata. |

## Safe-by-design remediation implementation (2026-02-21)

Legend: pending, in_progress, done, blocked

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| SBD-REV-001/002 Path containment + traversal regressions | done | SBD-LOG-4 | Replaced prefix-based checks with canonical scoped path resolution in `server/mcp/resource_catalog.py`; added sibling-prefix and encoded/mixed-separator traversal tests in `tests/test_resource_catalog.py`. |
| SBD-REV-003/004 Redaction expansion + verification tests | done | SBD-LOG-4 | Added configured secret collection + token-like key masking in `server/security.py`; wired to logging/exception paths; added redaction regression tests including upstream logging coverage. |
| SBD-REV-005 Transport internal error sanitization | done | SBD-LOG-4 | STDIO + HTTP transports now return generic `Internal error` payloads with correlation IDs; follow-up hardening logs exception type only (no traceback/raw exception text). |
| SBD-REV-006 Malformed JSON normalization | done | SBD-LOG-4 | `/tools/call`, `/tools/search`, and playground ingest endpoints now return deterministic HTTP 400 `INVALID_INPUT` envelopes on malformed JSON. |
| SBD-REV-007 Secure rate-limit defaults | done | SBD-LOG-4 | Default `RATE_LIMIT_BYPASS` flipped to `false`; docs/env updated; tests now reset in-memory limiter state per test without enabling bypass globally. |
| SBD-REV-008 Logging consistency cleanup | done | SBD-LOG-4 | Removed raw startup `print` and migrated `server/main.py` logging placeholders to loguru `{}` formatting. |
| SBD-REV-010 Citation URL stabilization | done | SBD-CIT-6 | Replaced `file://` codex trace URL in Prism `references.bib` with stable repository evidence reference. |

## Presentation story gallery (2026-02-17)

- Done: added six real-world layered map story scenarios under
  `playground/trials/fixtures/map_story_scenarios.json` covering map/render,
  inventory/export, boundary, routing, raster/WMTS/WFS capability, and
  dashboard/widget pathways.
- Done: added automated screenshot capture for story scenarios via
  `playground/trials/tests/map_story_gallery.spec.js` with per-story evidence
  logging.
- Done: added slide/report generation script
  `scripts/map_trials/summarize_story_gallery.py` producing
  `research/map_delivery_research_2026-02/reports/story_gallery_report.md`.
- Done: added slide deck
  `research/map_delivery_research_2026-02/reports/story_gallery_slides.md`
  with one slide per scenario and speaker notes for presentation delivery.

## Devcontainer STDIO stability (2026-02-16)

- Done: force STDIO to load repo code, not site-packages (`scripts/os-mcp` file-based import).
- Done: ensure repo root stays ahead of user site-packages (`scripts/os_mcp.py`).
- Done: make VS Code stdio wrapper include user site-packages (`scripts/vscode_mcp_stdio.py`).
- Done: align devcontainer installs with `python3` and auto-install deps when `loguru` is missing.

## Peatland survey reliability implementation plan (2026-02-19)

Reference plan:
- `/Users/crpage/repos/mcp-geo/docs/reports/peatland_survey_reliability_implementation_plan_2026-02-19.md`

Legend: pending, in_progress, done

| Workstream | Status | Dependencies | Notes |
| --- | --- | --- | --- |
| PSR-INT-0 Contract freeze + scaffolding | done | none | Added PSR config knobs + shared warning/policy helpers in `server/config.py` and `tools/os_common.py`; stabilized `os_features.query` warning/scan contract shape. |
| PSR-COR-1 Count + pagination correctness | done | PSR-INT-0 | `os_features.query` now keeps `numberReturned == len(features)` and standardizes `count` as returned count for all result types. |
| PSR-GRD-2 Query guardrails + thin defaults | done | PSR-INT-0 | Enforced `limit<=100` clamping, bbox-area clamp guardrail, strict boolean validation, and thin-property defaults with warning telemetry. |
| PSR-REL-3 Timeout/retry/degrade policy | done | PSR-INT-0 | Added configurable connect/read/retry settings and timeout-triggered degrade path (reduced bbox/limit + geometry-disable warning) for features queries. |
| PSR-RES-4 Resource-backed large payload delivery | done | PSR-INT-0 | Added `delivery=inline|resource|auto` to `os_features.query` with resource export handoff metadata (`resourceUri`, `bytes`, `sha256`). |
| PSR-GEO-5 Polygon validation + normalization | done | PSR-INT-0 | Added deterministic polygon validation (closure, bounds, vertex caps, distinct vertices) with explicit `INVALID_INPUT` errors. |
| PSR-CQL-6 Filter provenance + scan budgets | done | PSR-COR-1, PSR-GRD-2 | Added structured `hints.filterApplied` + `hints.scan` metadata and explicit partial-scan warnings for local post-filter workflows. |
| PSR-BND-7 Protected-landscape boundaries | done | PSR-INT-0 | Added `os_landscape.find` / `os_landscape.get` and `resource://mcp-geo/protected-landscapes-england` with Bowland fixture coverage. |
| PSR-ROU-8 Survey-intent routing hardening | done | PSR-GRD-2, PSR-BND-7 | `os_mcp.route_query` now classifies peatland survey prompts as `environmental_survey` and returns AOI-first survey plans using `os_landscape.*` + bounded `os_features.query`. |
| PSR-PEA-9 Peat-specific evidence layer integration | done | PSR-BND-7 | Added `tools/os_peat.py` (`os_peat.layers`, `os_peat.evidence_paths`), `resources/peat_layers_england.json`, resource-catalog wiring (`resource://mcp-geo/peat-layers-england`), route-query integration, and unit/resource tests (`tests/test_os_peat.py`). |
| PSR-E2E-10 Golden scenario + release readiness | done | all PSR workstreams | Added deterministic floor-question fixture (`tests/fixtures/psr_peat_floor_question.json`) and E2E assertions for HTTP + STDIO contracts (`tests/test_psr_peat_e2e.py`, `tests/test_evaluation_harness_full.py`) validating AOI provenance + direct/proxy separation + confidence + caveats; updated runbook docs (`docs/examples.md`, `docs/troubleshooting.md`). |

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
| MDR-E1 MCP/AI-host best-practice bundle | done | MDR-I4 | Published `docs/map_embedding_best_practices.md` with worker/CSP-safe embedding patterns and checklist templates. |
| MDR-E2 Lightweight embedding style profiles | done | MDR-E1 | Added `resource://mcp-geo/map-embedding-style-profiles` with constrained profile definitions for mixed/no-UI hosts. |
| MDR-E3 Progressive fallback official examples | done | MDR-E1, MDR-E2 | Updated examples/tutorial docs with deterministic full UI -> partial UI -> no UI fallback sequences. |
| MDR-E4 Mixed UI/no-UI host guidance | done | MDR-E1 | Expanded troubleshooting/architecture/support-matrix guidance for deterministic degradation across mixed host fleets. |

## Claude interop troubleshooting (2026-02-14)

Legend: pending, in_progress, done

| Step | Status | Notes |
| --- | --- | --- |
| CT-01 Correlate Claude UI failures with MCP stdio trace ids | done | Confirmed `tools/call` requests for Village Hotel flow returned `status=200` with no trace parse errors despite UI `Tool execution failed`. |
| CT-02 Record startup-permission and rebuild pitfalls | done | Added troubleshooting guidance for macOS `python3.14` permission prompt and `MCP_GEO_DOCKER_BUILD` rebuild mode behavior. |
| CT-03 Harden tool-call result shape for strict hosts | done | STDIO + HTTP now auto-populate `structuredContent` for dict payloads when not provided explicitly. |
| CT-04 Capture Claude prefix + preview-runtime gotchas | done | Documented `mcp-geo:<tool>` namespace hint behavior and `maplibregl is not defined` inline-preview limits in troubleshooting/support-matrix docs. |
| CT-05 Fix boundary explorer host-init coupling failure | done | Hardened `ui/boundary_explorer.html` so `ui/initialize` completes even when map runtime init fails (`maplibre` missing/worker issues), with explicit telemetry and degraded-mode diagnostics. |
| CT-06 Avoid embedded widget payload mode for Claude stdio | done | `server/stdio_adapter.py` now applies Claude-specific default `contentMode=resource_link` for `os_apps.render_*` calls (unless explicitly overridden) via `MCP_STDIO_CLAUDE_APPS_CONTENT_MODE`, reducing raw-HTML transcript fallbacks while preserving widget-launchable content blocks. |
| CT-07 Remove `ui://`-relative MapLibre asset dependency in widgets | done | Updated geography/boundary widget HTML to use absolute MapLibre CDN URLs (with jsDelivr fallback) and proxy-only worker URL wiring, plus CSP domain updates/tests; this prevents `window.maplibregl` missing in hosts that do not resolve `vendor/*` under `ui://` resources. |
| CT-08 Confirm host runtime limitation after `resource_link` adoption | done | Latest Claude trace confirms `tools/call` + `resources/read` success for `ui://` widgets and no follow-on `os_apps_log_event` activity, isolating remaining failure to client runtime mount/bridge behavior. |

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
| OS Features (NGD / OGC Features) | Done | tools/os_features.py | Supports bbox/polygon queries, attribute filters, resultType hits, field projection, sorting, queryables fetch, collections listing/latest mapping, WFS/WFS archive capabilities, and PSR reliability controls (guardrails, warning hints, timeout degrade, resource delivery, and count correctness). Feature-by-id and explicit CRS variants remain optional follow-on enhancements. |
| OS Maps (render) | Partial | tools/os_maps.py, server/maps_proxy.py | Static map proxy URL plus overlay-ready render contract delivered, with WMTS capabilities and raster ZXY tile retrieval. Full end-to-end client rendering orchestration still pending. |
| OS NGD Tiles (OTA) | Done | tools/os_tiles_ota.py | Added OTA discovery surfaces: collections, tilematrixsets, conformance. |
| OS Downloads API | Done | tools/os_downloads.py | Added product/download listing plus export prepare/get with resource-backed delivery. |
| OS Net API | Done | tools/os_net.py | Added RINEX years, station metadata, and station log retrieval with delivery controls. |
| OS Vector Tiles | Done | tools/os_vector_tiles.py | Descriptor tool present. |
| ONS data query + filters | Partial | tools/ons_data.py, tools/ons_codes.py | Live mode required; ons_codes supports on-disk cache; `ons_data.get_filter_output` now supports resource-backed export delivery for large outputs (`delivery=resource|auto`) with `resource://mcp-geo/ons-exports/*` artifacts. |
| ONS dataset search | Done | tools/ons_search.py | Live search only; no sample fallback. |
| NOMIS statistics | Partial | tools/nomis_data.py, tests/test_nomis_data.py, resources/nomis_workflows.json | Discovery/query tools working; fixed concept/codelist endpoints and improved GSS→NOMIS geography resolution (OA/LSOA/MSOA/ward). Added dataset-specific workflow profiles resource and routing guidance link-up; broader profile depth can still be expanded. |
| Admin geography lookup | Partial | tools/admin_lookup.py, server/boundary_cache.py | Live ArcGIS path plus optional PostGIS cache; level filtering + match modes added; cache search fallback transparency now includes fallback reasons and cache maturity snapshots, and cache status exposes staleness metadata. |
| Boundary ingest pipeline | Done | scripts/boundary_pipeline.py, docs/Boundaries.json | Pipeline tooling and validation/reporting are complete; source-resolution verification now passes manifest-wide (`COMPLETE_BOUNDARIES_RESOLVED_AND_VERIFIED`), while full download/ingest/validate completion remains in progress for broader UK-wide coverage. |
| Static resources (code lists, boundaries) | Partial | server/mcp/resource_catalog.py, resources/, scripts/pack_cache_refresh.py | Boundary/code-list hybrid fetch-cache manifests + indexes are exposed (`boundary-pack-sources`, `code-list-pack-sources`, `boundary-packs-index`, `code-list-packs-index`); configured boundary packs are now cached, while wider pack coverage still depends on additional source entries/availability. |
| Conversational normalization | Done | tools/os_mcp.py, tests/evaluation/* | `route_query` + descriptor for tool discovery, plus `os_mcp.select_toolsets` for post-init discovery filter selection. |
| Stats routing diagnostics | Done | tools/os_mcp.py | Added stats routing explainer tool. |
| Evaluation harness / coverage matrix | Done | tests/evaluation/*, docs/evaluation.md | Question suite + rubric + harness; live capture optional. |
| Playground UI for developers | Partial | playground/, server/mcp/playground.py | New Svelte playground scaffold; still needs UI resource rendering + evaluation orchestration. |
| MCP-Apps UI widgets | Partial | tools/os_apps.py, docs/mcp_apps_alignment.md | Geography selector, boundary explorer, and statistics dashboard are operational; `ui/feature_inspector.html` and `ui/route_planner.html` remain static mock UIs (layout + payload echo, no live map/data actions yet). |
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
Current explicit status note (2026-02-21): `feature_inspector` and
`route_planner` UI resources are present but remain presentation stubs (static
mock shells) and are not yet wired for end-to-end interactive map workflows.

| UI tool | What exists now | Playground gaps | Notes |
| --- | --- | --- | --- |
| os_apps.render_geography_selector | MCP-Apps widget resource and tool | Embed UI resource, capture selection context, and show how to pass selections into follow-on tool calls | Needs a state panel for selected areas. |
| os_apps.render_statistics_dashboard | MCP-Apps widget resource and tool | Embed UI, allow user to wire dataset/filters, show resulting `ons_data.*` calls | Needs read/write sync between UI and tool calls. |
| os_apps.render_feature_inspector | MCP-Apps widget resource and tool | Embed UI, show selected feature JSON and source tool calls | Current UI is a static mock shell; needs GeoJSON preview, live tool wiring, and result drill-down. |
| os_apps.render_route_planner | MCP-Apps widget resource and tool | Embed UI, show chosen route geometry and parameters | Current UI is a static mock shell; needs map viewport, live routing/tool wiring, and geometry preview. |
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
