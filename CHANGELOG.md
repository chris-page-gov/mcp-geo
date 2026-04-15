# Changelog

All notable changes to this project will be documented in this file.


## [Unreleased]

### Added
- Added the switchable Obsidian agent-control implementation plan at
  `Plans/PLAN-Obsidian-agent-control-plane.md`, plus the tracked rollout
  baseline in `PROGRESS.MD` and `CONTEXT.md`. The new workstream will build a
  dedicated control vault under `Obsidian/MCP Geo Agent Control/`, keep
  `AGENTS.md` as the root entrypoint, and compare `classic` versus `obsidian`
  instruction profiles with a dedicated smoke pack.
- Added the first checked-in Obsidian agent-control vault scaffold under
  `Obsidian/MCP Geo Agent Control/`, including curated control notes,
  generated digests for repo map / plans / verification / releases, the new
  build helper `scripts/agent_control_common.py`, the vault builder
  `scripts/build_agent_control_vault.py`, the manifest
  `data/agent_control/control_vault_manifest.json`, and focused regression
  coverage in `tests/test_agent_control_vault.py`.
- Added the official Obsidian CLI wrapper `scripts/obsidian_cli.py`, the
  control-vault validator `scripts/validate_agent_control.py`, and focused
  preflight coverage in `tests/test_obsidian_cli.py`. The new preflight checks
  the effective installed app version, bundled CLI binary, PATH registration,
  and vault read/search behavior, including the macOS auto-updated runtime
  package under `~/Library/Application Support/obsidian/obsidian-<version>.asar`.
- Added the switcher `scripts/switch_agent_mode.py --mode classic|obsidian`
  plus the active-mode validation checks in `scripts/validate_agent_control.py`
  and focused coverage in `tests/test_switch_agent_mode.py`. The repo now
  keeps the committed baseline in `classic` mode while the switcher can
  locally rewrite the root instruction files into `obsidian` mode and restore
  the tracked baseline from `HEAD` for repeatable evaluation.
- Added the instruction-focused comparison pack
  `docs/benchmarking/obsidian_agent_control_smoke_pack_v1.json` plus the
  structural regression test `tests/test_obsidian_agent_control_smoke_pack.py`
  for six smoke scenarios across Codex, Claude, Gemini, and VS Code in both
  `classic` and `obsidian` modes.
- Added the smoke-pack runbook
  `docs/benchmarking/obsidian_agent_control_smoke_pack.md`, the evidence
  template `docs/benchmarking/obsidian_agent_control_smoke_evidence_template.md`,
  and README guidance that distinguishes the new agent-control vault from the
  existing repo-navigation knowledge base. The Obsidian control-plane
  implementation is now complete in-repo; the remaining local prerequisite for
  full CLI-ready validation is making the desktop CLI binary available to the
  shell and passing the live read/search preflight.
- Added the canonical vault-root control contract
  `Obsidian/MCP Geo Agent Control/AGENTS.md`, rewired `obsidian`-mode
  repo-root adapters to delegate to that file, and checked in human-usable
  `.obsidian/workspace.json` / core-plugin defaults so opening the control
  vault in Obsidian shows the canonical instruction surface and file explorer
  instead of an empty tab.

### Fixed
- Bounded Obsidian CLI preflight commands with an explicit timeout and made
  the missing-CLI regression coverage independent of any host-level `obsidian`
  binary on `PATH`, preventing validation and pytest runs from hanging on an
  unresponsive desktop CLI registration.
- Fixed the Obsidian CLI preflight so it no longer treats the macOS installer
  shell version as the authoritative app version. The validator now prefers
  the effective runtime version from the newest auto-updated
  `obsidian-<version>.asar` package when present, matching the version shown
  in Obsidian's About dialog.
- Added the checked-in unattended multi-client remediation implementation plan
  at `Plans/PLAN-Unattended-multiclient-eval-remediation.md`, plus lockstep
  tracking updates in `CONTEXT.md` and `PROGRESS.MD` so the repo records the
  readiness-first redesign before the harness changes land.
- Added a built-in readiness probe to `scripts/unattended_client_eval.py`
  together with `--readiness-only`, per-track readiness artifact files, and
  structured attempt records labelled as `readiness`, `recovery`, or
  `capability`.
- Added unattended multi-client host evaluation tooling via
  `scripts/unattended_client_eval.py`, focused regression coverage in
  `tests/test_unattended_client_eval.py`, and the first captured aggregate
  report at `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-12.{md,json}`.
- Added the first full remediation-era four-client rerun artifacts at
  `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13.{md,json}` plus the
  per-track readiness JSON outputs. That run confirmed Codex CLI, Gemini CLI,
  and Claude Code CLI now complete the full eight-scenario pack while VS Code
  Agent still needs additional remediation before closure.
- Added the VS Code closure evidence at
  `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_canary_v17_no_primer.{md,json}`
  and
  `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13_vscode_full_v18_no_primer.{md,json}`,
  plus the final rewritten canonical four-client rerun at
  `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-13.{md,json}` showing
  all four clients ready and all four completing the full eight-scenario pack.
- Added the follow-on unattended analysis report
  `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-12_analysis.md`,
  grouping the captured evidence by tool family, working flows, failure
  classes, and a concrete remediation plan for cross-client optimization.
- Added shared benchmark secret-resolution helper
  `scripts/benchmark_env.py` and wired `scripts/unattended_client_eval.py`,
  `scripts/host_benchmark.py`, and `scripts/mcp-docker-local` to use it.
  Unattended benchmark runs can now resolve `OS_API_KEY` / `OS_API_KEY_FILE`
  from process env, `launchctl`, repo `.env`, and the local Claude/Codex
  `mcp-geo` client configs, closing the previous `NO_API_KEY` gap where eval
  runs bypassed the normal per-client secret sources.
- Added explicit unattended scenario metadata in
  `docs/benchmarking/codex_vs_claude_host_scenarios_v1.json` for
  `requiresLiveOsApi`, `requiresUiRuntime`, `toolFamily`, and
  `expectedCapability`, allowing the runner to separate readiness from
  capability and to summarize results by capability/tool family.
- Added `ons_geo.area_summary`, the compact postcode/UPRN/area-code follow-up
  surface for OA/LSOA/MSOA/ward summaries. It resolves the target area from
  the local ONS cache, returns compact area counts, can use the new
  `os_map.inventory` summary/count modes for lightweight built-environment
  context, and exposes curated NOMIS follow-up datasets for small-area
  profiling.
- Added the new guide resource
  `resource://mcp-geo/area-summary-workflows` plus the supporting evaluation
  artifact `examples/ons_from_postcode_03_summary_only_eval.md`, documenting
  the recommended prompt pattern and the guardrail against raw
  `os_map.inventory` calls for summary-only prompts.
- Added `scripts/check_spec_drift.py` plus the related `docs/spec_tracking.md`
  workflow so vendored specification/supporting-reference submodules can be
  audited for origin-head drift and missing local spec paths with one command.
- Added configurable boundary-run archive path resolution via
  `BOUNDARY_RUNS_DIR`, `BOUNDARY_RUNS_SEARCH_DIRS`, and the shared helper
  `server/boundary_run_paths.py`. Boundary-report readers can now search
  optional mounted roots such as `/Volumes/ExtSSD-Data/Data`, and the boundary
  pipeline/autofix scripts now honor the configured primary write location.
- Added DuckDB-backed AddressBase Premium Parquet support for
  `council_tax.query`, alongside the new builder
  `scripts/addressbase_build_xref.py`. The council-tax lookup now accepts
  supplier-style CSV headers, extracted camelCase headers, or Parquet xref
  files, prefers `xref_voa_os.parquet` when scanning configured directories,
  and can query local Parquet extracts directly without creating a separate
  indexed DuckDB database.

### Changed
- Unattended client interop report outputs now live under
  `docs/reports/client_interop_unattended/` instead of cluttering the
  top-level `docs/reports/` directory. `scripts/unattended_client_eval.py`
  now defaults to that subfolder for its report prefix, and new
  `client_interop_unattended_eval_*` artifacts there are ignored by git.
- `scripts/unattended_client_eval.py` now runs each client through a readiness
  phase before the scenario pack, marks unusable tracks as `not_ready` instead
  of emitting misleading per-scenario runner errors, and skips only the
  `live_os` scenarios when readiness shows that no usable OS key is visible.
- The unattended aggregate report schema now separates readiness from
  capability, tracks first-attempt versus recovery-attempt outcomes, emits
  blocker taxonomy classes such as `client_auth_failure`,
  `client_workspace_restriction`, `client_no_mcp_traffic`,
  `server_no_live_key`, and `scenario_tool_failure`, and adds expected-
  capability / tool-family summaries so resource-consumption scenarios are not
  conflated with general tool-selection flows.
- Gemini unattended runs now use stable ignored benchmark workspaces under
  `logs/benchmark-workspaces/gemini/<task>/` and include `~/.gemini` in the
  allowed directory set, eliminating the prior temporary-project pattern that
  blocked headless Gemini before the first MCP request.
- Gemini unattended runs now also write a per-workspace `.gemini/settings.json`
  plus workspace policy that allows only `mcp_*` tools during benchmark runs,
  replacing the earlier transient `gemini mcp add` flow that still let Gemini
  fall back to local built-in tools instead of exercising the MCP surface.
- `scripts/mcp-docker-local --plan` now reports the chosen default/include/
  exclude toolset settings alongside the existing non-sensitive OS-key
  visibility flags, and the wrapper now hydrates those toolset env vars from
  the same local sources as the benchmark env helper.
- The unattended benchmark/report flow now treats blocked runs as blocked:
  runner errors, startup-only sessions, and no-traffic sessions keep only a
  `diagnosticScore` and no longer count toward the scored-track average.
- The VS Code unattended benchmark runner now opens a clean ignored benchmark
  workspace before `code chat` so each attempt attaches to a deterministic
  window instead of whichever shared VS Code window happens to be active.
- The VS Code unattended benchmark runner now writes the traced benchmark-only
  server definition into the benchmark workspace's own `.vscode/mcp.json`
  instead of mutating `~/Library/Application Support/Code` or depending on a
  copied profile. Each attempt opens that workspace on the live authenticated
  VS Code profile, raises the newly created benchmark window before
  `code chat --reuse-window`, materializes only the session-owned MCP/UI log
  deltas into the benchmark session directory, and then closes that same
  benchmark window afterward. This removes the shared-window coupling without
  breaking Copilot auth or accumulating stray benchmark windows.
- Traced temp stdio server definitions now wrap Python-script entrypoints with
  the active interpreter before passing them to
  `scripts/mcp_stdio_trace_proxy.py`. This keeps workspace-scoped VS Code
  benchmark servers aligned with the checked-in `python3
  scripts/vscode_mcp_stdio.py` launch shape and avoids `PermissionError`
  startup failures when the traced launcher targets a non-executable Python
  file directly.
- The VS Code readiness probe now uses a Copilot-compatible alias-based MCP
  prompt that targets `os_resources.get` through the benchmark server's exposed
  tool alias, and VS Code benchmark attempts once again use unique per-session
  benchmark workspace paths instead of one stable `readiness-probe` workspace.
  This restores fresh VS Code MCP alias registration per attempt; live probe
  `client_interop_unattended_eval_2026-04-13_vscode_workspace_probe_v14_unique_alias_fix`
  reached `ready` on the bounded recovery attempt with a traced
  `tools/call:os_resources.get`.
- The VS Code unattended runner now re-raises the benchmark window immediately
  before the real scenario chat, resets trace/UI delta snapshots after the
  primer phase so capability scoring does not confuse primer traffic for
  scenario traffic, waits longer for first chat-specific MCP activity before
  concluding `no_mcp_traffic`, and explicitly confirms the `A session is in
  progress` close dialog when closing benchmark windows. These follow-on fixes
  were prompted by the first full `client_interop_unattended_eval_2026-04-13`
  rerun, which showed VS Code readiness succeeding but capability scenarios
  falling back to primer-only startup traffic while benchmark windows remained
  open long enough to exhaust workstation memory.
- The same VS Code unattended runner now also distinguishes startup catalog
  traffic from useful tool/resource activity during the post-chat wait loop,
  records cleanup metadata in each benchmark session, and escalates cleanup to
  benchmark-workspace-specific VS Code process-tree termination when window
  close automation still leaves a benchmark instance alive. This follow-on fix
  was prompted by the same `2026-04-13` rerun plus the observed 50+ GB RAM
  leak, which showed the runner still stopping after short idle periods that
  contained only `initialize` / `prompts.list` / `tools.list` traffic.
- The same VS Code unattended runner now also treats zero-window-baseline
  launches as benchmark-owned Code app lifecycles and quits the whole Code app
  after workspace cleanup when no other Code windows remain. Session metadata
  now records that app-quit path alongside the existing window/process cleanup
  facts so operator-reported memory leaks can be traced back to a specific
  cleanup branch.
- The VS Code unattended runner no longer issues a separate primer chat before
  each benchmark attempt. A targeted canary run showed the reclaimed benchmark
  Code process tree still left the capability session with zero retained
  post-primer MCP traffic, which isolated the primer itself as the only MCP
  traffic source in that flow. The real scenario chat is now the first
  MCP-driving action in each benchmark window.
- The canonical unattended aggregate report still records all four tracks as
  `ready` and each client completing the full scenario pack, but operational
  closure is reopened after a same-day operator report that Code still reached
  roughly 58 GB and required a manual kill after the unattended rerun. The new
  zero-window-baseline app-quit safeguard is in place; a fresh live rerun is
  still pending before the remediation can be re-closed.
- The unattended aggregate renderer now summarizes only the requested tracks
  instead of assuming all four benchmark clients are always present, so
  single-track readiness probes produce report artifacts instead of crashing.
- The benchmark wrapper plan output now reports whether an OS key and/or key
  file was resolved, without revealing the secret itself. This makes wrapper
  preflight diagnosis possible when local client configs, `.env`, and shell
  env differ.
- Setup docs now explicitly treat absolute paths as local examples only, and
  the README / `.env.example` point path-bearing settings at portable
  placeholders instead of maintainer-specific locations.
- `scripts/mcp-docker-local` now hydrates path-bearing local settings such as
  `LANDIS_LOCAL_DATA_ROOT`, `LANDIS_PORTAL_ARCHIVE_DIR`,
  `LANDIS_FULL_RELEASE_ARCHIVE_DIR`, `ADDRESSBASE_PREMIUM_XREF_PATH`,
  `BOUNDARY_RUNS_DIR`, and `BOUNDARY_RUNS_SEARCH_DIRS` from the repo `.env`
  when host-side GUI clients do not export them directly. The wrapper also now
  normalizes relative host paths against the repo root and mounts those paths
  into the container so Docker-backed Claude/Codex sessions can use repo-local
  data roots and external archives such as `/Volumes/ExtSSD-Data/Data`
  consistently.
- Added `scripts/gemini-mcp-local` and `scripts/check_gemini_startup_scope.sh`
  so Gemini CLI can use the same Docker-backed startup path, scoped discovery,
  cache mounts, and benchmark preflight checks as Claude/Codex. The benchmark
  preflight now supports both isolated per-client sidecars and explicit shared
  devcontainer reuse, validates Gemini alongside Claude/Codex in both modes,
  and the trace session helpers now recognize Gemini wrapper runs.
- Docker-backed local wrappers now default to isolated PostGIS sidecars again
  (`MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=0`) instead of silent devcontainer
  reuse. Shared PostGIS benchmarking remains available, but only as explicit
  opt-in mode.
- Shell benchmark/runtime helpers no longer assume `rg` is installed. The
  benchmark-cache preflight and PostGIS diagnostics now fall back to `grep`
  in minimal CI or host shells, preventing false failures when ripgrep is not
  available on PATH.
- LandIS helper scripts now default to `~/Data/...` rather than maintainer
  machine paths, and LandIS archive relocalization no longer depends on the
  specific `/Volumes/ExtSSD-Data/Data` prefix.
- `scripts/check_spec_drift.py` now invokes Git through PATH resolution rather
  than hardcoding `/usr/bin/git`, so vendored-spec drift audits work on hosts
  where Git is installed via Homebrew, Nix, or other nonstandard locations.
- Hardened the `tools/os_mcp.py` property-tax router so plain `council tax status`
  prompts now follow the postcode/address-to-`council_tax.query` status workflow
  instead of falling back to `council_tax.band_lookup`, with matching toolset
  inference for discovery clients.
- The same router/summary follow-up now keeps explicit higher-level area-profile
  requests on area-code prompts instead of silently collapsing them back to the
  code-implied level, rejects narrower target levels with descriptor guidance,
  routes under-specified Council Tax band prompts to a resolution-first flow,
  and hardens `ons_geo.area_summary` so direct area ids return `NOT_FOUND`
  unless they resolve via hierarchy/geometry or non-zero cached counts.
- `ons_geo.area_summary` now treats helper tools such as
  `admin_lookup.area_geometry`, `admin_lookup.reverse_hierarchy`, and
  `os_map.inventory` as genuinely best-effort: helper exceptions no longer turn
  an otherwise valid summary request into a `500`.
- Tightened ONS release detection in `scripts/ons_geo_cache_refresh.py` so
  explicit release-pattern matches keep month/epoch pairing local to the matched
  candidate instead of borrowing an epoch from an unrelated archived resource in
  the same CKAN payload.
- `os_map.inventory` now supports opt-in `responseMode=summary|counts` for
  compact UPRN/building counts, `nomis.query` now includes human-readable
  `datasetSummary` metadata when available, and `tools/os_mcp.py` now routes
  area-profile prompts such as `What do you know about that OA?` to
  `ons_geo.area_summary` instead of encouraging low-level orchestration.
- Added the grounded troubleshooting analysis
  `troubleshooting/Landis/draw_roads_on_map_analysis_2026-04-07.md`, which
  documents why AI clients struggle when map-building tasks are forced through
  low-level paged feature queries plus byte-chunk resource recovery, and
  recommends a task-shaped road-overlay export contract as the preferred fix.
- Added the new task-shaped road-overlay exporter `os_map.export_roads` in
  `tools/os_map.py`. It now fetches all required `os_features.query` pages
  server-side, assembles complete per-road GeoJSON parts, writes durable
  semantic export bundles under `resource://mcp-geo/os-exports/road-overlays/`,
  and can emit either `geojson_bundle`, `javascript_overlay`, or
  `leaflet_snippet` artifacts from a deterministic request hash rather than
  forcing clients to recover byte-chunked resources by hand.
- Added a repo-wide generated Obsidian knowledge base under
  `Obsidian/MCP Geo Knowledge Base/`, backed by
  `scripts/obsidian_kb_common.py`, `scripts/build_obsidian_kb.py`,
  `scripts/validate_obsidian_kb.py`, the canonical manifest
  `data/knowledge_base/obsidian_kb_manifest.json`, and the maintenance skill
  `skills/mcp-geo-obsidian-kb/SKILL.md`. The canonical build is evidence-first,
  excludes `Obsidian/**` from source scanning to avoid recursion, records
  source hashes and commit-pinned GitHub URLs in note frontmatter, and keeps
  local trace/session notes in an ignored `98 Local Overlay/` subtree.
- Added a root `LICENSE` file, `SECURITY.md`, and the Docker catalog submission
  note `docs/docker_mcp_catalog_submission.md` so the repo now carries explicit
  licensing, security-reporting, and Docker MCP catalog metadata guidance.
- Added the LandIS MVP namespace, including `landis_catalog.list_products`,
  `landis_metadata.get`, `landis_soilscapes.point`,
  `landis_soilscapes.area_summary`, and `landis_derive.pipe_risk`, backed by
  the new LandIS runtime helpers in `server/landis.py`.
- Added LandIS product and guidance resources:
  `resource://mcp-geo/landis-products`,
  `resource://mcp-geo/landis-docs-soil-data-structures`,
  `resource://mcp-geo/landis-docs-soil-classification`, and
  `resource://mcp-geo/landis-licence-current`, plus three LandIS prompt
  templates for planner, water-utility, and catchment soil briefings.
- Added LandIS warehouse scaffolding via `scripts/landis_schema.sql` and
  `scripts/landis_ingest.py`, defining the minimum PostGIS ingestion contract
  for the Soilscapes and pipe-risk MVP datasets with explicit provenance
  tables.
- Added `scripts/landis_portal_inventory.py` plus generated LandIS catalog
  inventories at `research/landis-data-source/landis_portal_inventory_2026-04-04.json`
  and `docs/reports/landis_portal_inventory_2026-04-04.md`, documenting the
  authenticated Atlas-visible portal datasets, documentation pages, maps,
  applications, and supporting assets.
- Added `scripts/landis_portal_download.py` to mirror the authenticated LandIS
  portal to local storage, including raw item payload capture for docs/media
  and chunked layer/table exports for Feature Services.
- Added the follow-on LandIS phase-2 architecture report
  `docs/reports/landis_phase_2_surfacing_plan_2026-04-04.md`, documenting how
  the completed authenticated archive (`106` mirrored items with `0` manifest
  errors) should evolve into the next MCP surface: keep the validated MVP
  stable, normalize NATMAP next, treat NSI as evidence-first, and defer AUGER
  plus catalogue/reference layers from the first analytical expansion.
- Added the follow-on LandIS release reconciliation report
  `docs/reports/landis_release_surface_reconciliation_2026-04-05.md`,
  confirming that the local archive is complete for the current authenticated
  ArcGIS portal route while also recording additional LandIS families/services
  still listed on the public LandIS website and separately licensed metadata

### Fixed
- Fixed sanitized tool-schema rewriting so top-level `oneOf` / `anyOf` /
  `allOf` flattening is now limited to the strict stdio transport. HTTP
  `/tools/describe` again preserves the full schema contract for alternate
  input tools such as area-vs-geometry selectors.
- Fixed `council_tax.band_lookup` so live GOV.UK form-validation responses are
  normalized into actionable `INVALID_INPUT` errors instead of leaking raw HTML
  back to clients, and updated property-tax routing so address-only council-tax
  band prompts resolve candidate postcodes through `os_places.search` before
  calling the live VOA lookup.
- Fixed Docker-backed `claude-mcp-local` / `mcp-docker-local` sessions so they
  mount the host ONS geo cache directory and cache index into the container
  when present. This restores `ons_geo.by_postcode` / `ons_geo.by_uprn` lookups
  in Claude-sidecar sessions that previously saw `CACHE_UNAVAILABLE` despite a
  populated host cache.
- Fixed `os_features.query` so legacy `ngd-base:` collection ids are accepted
  as compatibility aliases. Unversioned legacy ids are now upgraded to the
  latest advertised NGD collection version before the live items request, so
  older client prompts such as `ngd-base:bld-fts-buildingpart` no longer fail
  with avoidable unsupported-collection errors.
- Fixed `ons_select.search` elicitation forms so the optional geography/time
  fields now use plain string `enum` schemas rather than property-level
  `oneOf` literals. This avoids strict-client validation failures seen in
  Claude Code, where accepting the form previously stalled because the client
  treated selected string values as invalid `never` inputs.
  pages that sit outside the mirrored portal slice.
- Added `scripts/landis_release_reconciliation.py` plus generated manifest
  `research/landis-data-source/landis_release_reconciliation_2026-04-05.json`
  to probe the missing public-menu LandIS items, capture `data.gov.uk`
  metadata matches, and attach conservative size guidance for dataset-like
  items that are still outside the mirrored portal slice.
- Added `scripts/landis_full_release_archive.py` plus generated manifest
  `research/landis-data-source/landis_full_release_manifest_2026-04-05.json`
  to build a rerunnable supplementary LandIS release archive on
  `ExtSSD-Data`, covering the missing public-site pages plus matched
  `data.gov.uk` packages/resources beyond the authenticated ArcGIS portal
  mirror and writing a separate `verification_manifest.json` completion test.
- Added the first local-archive-driven LandIS phase-2 tranche:
  `scripts/landis_archive_triage.py`,
  `research/landis-data-source/landis_archive_triage_2026-04-05.json`,
  `scripts/landis_phase2_ingest.py`, and the new MCP tool families
  `landis_archive.*`, `landis_natmap.*`, and `landis_nsi.*`, plus the
  archive-backed resources `resource://mcp-geo/landis-portal-inventory`,
  `resource://mcp-geo/landis-archive-triage`, and
  `resource://mcp-geo/landis-full-release-manifest`.
- Added direct LandIS archive support to `scripts/mcp-docker-local`, which now
  mounts the host `~/Data` tree read-only into the app container at
  `/landis-data`, sets `LANDIS_LOCAL_DATA_ROOT` automatically when that host
  directory exists, and forwards the LandIS warehouse/schema toggles so the
  standard app-container + PostGIS-container workflow can use the local archive
  without baking raw archives into the image.
- Added PostGIS lifecycle hardening across the Docker/devcontainer entrypoints:
  `.devcontainer/docker-compose.yml` now defaults to its own
  `mcp-geo-postgis-devcontainer` volume, `scripts/claude-mcp-local` and
  `scripts/codex-mcp-local` now use dedicated fallback container/network/volume
  names, and `scripts/mcp-docker-local` now inspects recent Postgres logs to
  call out checkpoint-corrupted volumes explicitly when a wrapper-managed
  sidecar does not become ready.
- Added Docker wrapper startup hardening so wrapper-managed PostGIS sidecars no
  longer publish host port `5432` by default, and stale sidecars with the wrong
  port-binding state are now called out for recreation instead of silently
  colliding with another wrapper's PostGIS container.
- Added the checked-in Obsidian vault `Obsidian/LandIS Knowledge Base/`,
  bundling the LandIS strategy, dataset notes, MCP architecture pages,
  reference material, and supporting PDF/image assets as a browsable local
  knowledge base for the LandIS workstream.
- Added the full repository review report
  `docs/reports/mcp_geo_full_code_review_2026-03-24.md`, indexed it in the
  reports catalog, recorded the remediation baseline in `PROGRESS.MD` and
  `CONTEXT.md`, and committed the Gemini review companion documents
  `GEMINI.md` and `Gemini-Code-Review.md` as part of the recorded review trail.
- Added the experimental `council_tax.band_lookup` pilot for England/Wales
  premise-level Council Tax band searches, including the GOV.UK HTML client,
  discovery wiring, focused mocked regressions, and the initial config/docs
  surface for the new Council Tax namespace.
- Added `council_tax.query`, an AddressBase Premium-backed batch UPRN check for
  Council Tax and non-domestic-rates status. The new tool stream-scans the
  configured Type 23 Application Cross Reference CSV, treats `7666VC` as
  Council Tax and `7666VN` as non-domestic rates, defaults to current records
  with blank `END_DATE`, and returns historical inactive source flags
  separately so ended records are visible without being misreported as current.
- Added `ons_geo.release_audit`, which combines the tracked AddressBase epoch
  schedule, ONS Open Geography Portal RSS notices, ONS Open Geography Portal
  dataset discovery, and current package resolution so operators can see both
  the latest resolvable public UPRN dataset and whether it is lagging behind
  the authoritative AddressBase publication schedule.
- Added `docs/ons_geo_source_resolution.md`, documenting the ONS geo source
  model with glossary coverage for abbreviations such as CKAN, DCAT, OGC API
  Records, ONSPD, NSPL, ONSUD, NSUL, CHD, and RGC, plus cited guidance on why
  package availability and freshness must be treated separately.
  separately for traceability. The docs/config surface now points to the
  current OS Docs specification pages instead of the dead legacy PDF URL.

### Changed
- Flattened top-level `oneOf` / `anyOf` / `allOf` combinators in sanitized
  stdio tool input schemas for strict MCP clients such as Claude Code. Nested
  property unions remain intact, but the startup tool catalog no longer emits
  top-level combinators that cause client-side tool-registration failures.
- Hardened `os_mcp.route_query` and `os_mcp.select_toolsets` for the current
  development surfaces. Council-tax/business-rates prompts now route through a
  dedicated property-tax path instead of generic address lookup, including the
  `os_places.by_uprn -> council_tax.band_lookup` workflow for band-from-UPRN
  prompts and direct `council_tax.query` routing for UPRN status checks.
  LandIS soil-screening prompts now classify as environmental survey work with
  explicit `landis_soils` discovery guidance and LandIS-focused survey plans.
- Updated the checked-in constrained-host startup profile (`starter` plus
  `ons_geo_lookup,property_tax,features_layers,landis_soils`) across
  `.vscode/mcp.json`, `.env.example`, `README.md`, and the startup-scope
  validation scripts so active development tools stay discoverable without
  exposing the full catalog at startup.
- Documented the 2026-04-09 DuckDB/PostGIS architecture review: DuckDB is the
  preferred local file-backed query engine for AddressBase-style artifacts,
  but the repo is not replacing the existing PostGIS-backed cache/warehouse
  surfaces at this stage because the route graph still depends on
  pgRouting/PostGIS and the boundary/LandIS stores would require a broader
  backend migration to change cleanly.
- `docs/tutorial.md` now documents automatic `ons_geo` source resolution during
  cache refresh, links to the new ONS source-resolution note, and includes the
  `ons_geo.release_audit` tool in the ONS geography walkthrough.
- Clarified the repo guidance for tool-surface changes so agents now treat
  tool additions and contract edits as OWASP maintenance work as well:
  update `security/owasp_mcp/tool_risk_inventory.json`, regenerate the signed
  manifest artifacts, and rerun the strict validator in the same change.
- Added the first real-delivery Council Tax UPRN example artifact set from the
  2026-04-07 ABP GML delivery: the repo now keeps
  `tests/fixtures/council_tax_uprn_abp_example.json` as a stable example
  output fixture, and the matching analyst-friendly workbook is generated at
  `output/spreadsheet/uprns_council_tax_status.xlsx`.
- Added a deterministic gold evaluation fixture pack for
  `council_tax.band_lookup` under `tests/fixtures/council_tax*` and
  `tests/test_council_tax_gold_eval.py`, using curated public GOV.UK search
  excerpts plus verified property-detail URLs for Westminster, Manchester, and
  York examples.
- Added a resolver-driven ONS geo source manifest in
  `resources/ons_geo_sources.json`, replacing the old `downloadUrl`-only shape
  with explicit resolver metadata for ArcGIS hosted tables (ONSPD/NSPL),
  release-file discovery (ONSUD/NSUL), and mandatory CHD/RGC support
  sidecars.
- Added `scripts/ons_geo_live_validate.py` as an opt-in external validation
  entrypoint that resolves live/public ONS sources and checks only high-signal
  invariants such as source reachability and required semantic field families,
  keeping that validation outside the default deterministic CI gate.
- Added compact schema-drift and code-history fixtures under
  `tests/fixtures/ons_geo/` plus focused offline regression coverage in
  `tests/test_ons_geo_cache_refresh.py`, `tests/test_ons_geo_cache.py`,
  `tests/test_ons_geo.py`, and `tests/test_ons_geo_live_validate.py`.
- Added the tracked AddressBase epoch schedule
  `resources/addressbase_epoch_schedule.json`, which now acts as the
  authoritative freshness reference for `ONSUD` / `NSUL` validation.

### Fixed
- Fixed the checked-in repo Docker image so it installs
  `mcp-geo[addressbase]` instead of only the base package. This restores the
  intended server-side DuckDB runtime for Parquet-backed `council_tax.query`
  calls and avoids false `MISSING_DEPENDENCY` errors when the container is
  rebuilt from the repo `Dockerfile`.
- `playground/package.json` now pins the non-vulnerable patch lines for
  `vite`, `hono`, and `@hono/node-server`, clearing the remaining npm audit
  findings after the earlier `path-to-regexp` / `picomatch` security refresh
  without widening the upgrade scope to Vite 8.
- `os_map.export_roads` now accepts concise selector payloads such as
  `selectionSpec: {"postcode": "CV3 1HB"}` (plus the same shorthand for
  `uprn`, `gssCode`+`level`, and `geometry`/`polygon`) instead of requiring
  callers to always build `selectionSpec.selectors[...]` manually. The same
  parser is shared with selector-driven `os_map.export` jobs so both flows now
  accept the shorthand form.
- `os_features.query` and `os_places.polygon` now accept JSON-encoded polygon
  strings as well as native JSON arrays/objects, so hosts that stringify nested
  polygon payloads no longer fail with `INVALID_INPUT` before the upstream OS
  call is attempted.
- Selector-driven road exports and selector-driven `os_map.export` jobs now
  normalize missing or unreadable ONS geo cache failures into explicit
  `CACHE_UNAVAILABLE` / `CACHE_READ_ERROR` tool errors rather than bubbling
  raw SQLite exceptions as internal errors. `os_map.export_roads` also now
  returns `AOI_NOT_RESOLVED` when a syntactically valid `selectionSpec` does
  not resolve any AOI geometry.
- `scripts/ons_geo_cache_refresh.py` now performs resolver-driven source
  acquisition, writes raw artifacts under `data/cache/ons_geo/raw/...`,
  stores schema fingerprints and validation summaries, and enriches the cache
  with normalized semantic geography payloads plus CHD/RGC-backed code-history
  annotations instead of depending on exact raw column names.
- `scripts/ons_geo_live_validate.py` now uses metadata-only source probes
  rather than full dataset refreshes during live validation, downgrades
  archive-style remote releases to explicit warnings instead of hanging on
  large downloads, ignores page-fragment/static-asset false positives when
  selecting `portal_release_file` candidates, and now points the RGC manifest
  at the direct December 2025 data.gov.uk package rather than a generic
  geoportal search page.
- `scripts/ons_geo_live_validate.py`, `scripts/ons_geo_cache_refresh.py`, and
  `tools/ons_geo.py` now treat ONSUD/NSUL freshness as an explicit validation
  concern. The resolver parses dataset epochs, compares them against the
  tracked AddressBase publication schedule, reports `freshness` metadata, and
  flags lagging UPRN datasets rather than assuming the newest-looking ONS title
  is current.
- `server/ons_geo_cache.py` and `tools/ons_geo.py` now prefer stored normalized
  geography payloads on lookup, expose richer provenance such as resolved
  release/source/schema fingerprint, and report exact/best-fit/support-dataset
  readiness in `ons_geo.cache_status` rather than only checking for a cache
  file and shallow product list.
- Selector-driven road exports can now use ward/country/region-backed GSS-code
  membership columns from the expanded ONS UPRN index, so the normalized cache
  remains useful to downstream AOI flows without any year-specific header
  assumptions.
- `os_mcp.route_query` now recognizes road-overlay/map-repair prompts such as
  replacing broken Overpass fetches with OS road geometry and recommends
  `os_map.export_roads` directly, including extracted road numbers plus
  output-format hints for Leaflet/JavaScript-oriented requests.
- `resource://mcp-geo/os-exports/*` reads now return content-type-aware MIME
  metadata for `.geojson`, `.js`, and `.html` artifacts, so semantic road
  export parts are advertised as `application/geo+json` /
  `application/javascript` instead of generic plain text.
- `os_features.query` now normalizes CQL property identifiers against the
  collection queryables schema before sending upstream NGD requests, so agents
  using mixed-case field names like `roadClassificationNumber` on RoadLink no
  longer fail on OS's lowercase-only queryable contract. Added focused
  regressions for the normalization path and preserved the rewritten CQL in the
  tool response for traceability.
- MCP HTTP and STDIO tool responses now omit `structuredContent` for error
  results, preventing clients such as Claude from validating error payloads
  against success-only output schemas. Added focused postcode-tool regressions
  covering the `NO_API_KEY` path across both transports.
- LandIS discovery and archive coverage now better match the resilience-use-case
  data already mirrored locally: the callable registry exposes the exact
  NATMAP thematic `productId` values accepted by
  `landis_natmap.thematic_area_summary`, LandIS live-query errors now return
  structured fallback guidance, and `landis_archive.*` includes the
  supplementary full-release/public-menu plus matched `data.gov.uk` package
  slice so `HOST`, `wetness`, `Series Hydrology`, `Series Leacs`, and similar
  supplementary references are discoverable through MCP.
- Fresh Docker PostGIS sidecars no longer expose empty LandIS live-query
  surfaces by default. `scripts/mcp-docker-local` now detects missing or empty
  LandIS tables and auto-bootstraps the mounted local archive plus validation
  layers before starting the stdio server, `scripts/landis_phase2_ingest.py`
  now remaps mounted `/landis-data/...` archive paths correctly inside the
  container, and `scripts/landis_ingest.py` now executes schema SQL
  statement-by-statement so repeated bootstrap passes remain safe.
- LandIS wrapper bootstrap now rejects incomplete portal archive roots before
  phase-2 ingest. `scripts/mcp-docker-local` now falls back to the newest
  complete `landis_portal_archive_*` directory instead of hard-failing on the
  newest partial mirror, and `scripts/landis_phase2_ingest.py` now exposes the
  same archive-completeness validation for both direct invocation and wrapper
  selection.
- The checked-in Obsidian knowledge base no longer trips the OWASP secret-scan
  gate on frontmatter provenance hashes. `scripts/obsidian_kb_common.py` now
  renders note-level `source_hashes` in a chunked `sha256:` format that
  preserves provenance while avoiding `gitleaks` false positives, and the
  regenerated vault now includes canonical notes for the KB build/validate
  scripts themselves.
- Playground transcript endpoints now normalize non-object JSON payloads back to
  the standard `INVALID_INPUT` response instead of leaking a `TypeError` from
  Pydantic construction, and the config fallback shim now has explicit
  regression coverage for the overrides path the daily bug scan flagged.
- LandIS release-surface HTML stripping now tolerates malformed closing
  `script`/`style` tags across both the reconciliation helper and the
  script-free vendor snapshot helper, and `landis_nsi.nearest_sites` now binds
  filtered-distance SQL parameters in placeholder order when `maxDistanceKm`
  is supplied.

### Changed
- Tool/resource discovery now includes the LandIS namespace and resources, and
  the full evaluation harness treats the initial LandIS tool set as specialist
  surfaces until the canonical question bank expands to cover them directly.
- LandIS phase-2 work is now local-data-first: the repo defaults to the local
  archive roots under `~/Data` when resolving the mirrored LandIS portal and
  supplementary full-release archive, and the new phase-2 ingest path loads
  NATMAP and NSI data from those local archives rather than depending on a
  fresh authenticated portal session.
- The LandIS release-reconciliation/archive tooling now treats query-string
  download URLs as distinct cached resources instead of collapsing them onto a
  single path, and the full-release verifier now accepts base `MapServer`
  locator URLs when the same package already includes an archived companion
  `FeatureServer`/`WMS`/`WFS`/OGC representation. The recorded 2026-04-05
  supplementary archive therefore completes with `0` manifest errors and `0`
  verification failures.
- The normal Docker wrapper path is back in sync with the LandIS phase-2
  runtime: `mcp-geo-server:latest` has been refreshed, `scripts/mcp-docker-local`
  now exposes the local archive under `/landis-data`, and the containerized
  LandIS surface has been revalidated against a fresh PostGIS sidecar using the
  local archive plus validation warehouse layers.
- `scripts/landis_phase2_ingest.py` now writes real portal-derived `updated_at`
  timestamps into the NATMAP/NSI warehouse tables instead of incorrectly
  inserting dataset-version labels into timestamp columns.
- GitHub Actions CI now skips the `supply-chain-posture` OpenSSF Scorecard job
  on release-tag pushes, limiting it to pull requests and the default branch so
  `v*` release tags do not fail on the action's unsupported tag-push path. The
  scorecard artifact upload now also runs only when the SARIF output exists, so
  unsupported or upstream-failed runs do not add a second missing-file error.
- MCP HTTP auth now covers the remaining raw HTTP discovery and operator
  surfaces: `/metrics`, `/tools/list`, `/tools/describe`, `/tools/search`, and
  all `/playground/*` routes now follow the same bearer-auth boundary as
  `/mcp`, leaving only `GET /health` public when auth is enabled. The
  playground input-validation endpoints now return `400` for invalid payloads
  instead of `200`.
- Central secret redaction now also covers `MCP_HTTP_AUTH_TOKEN` and
  `MCP_HTTP_JWT_HS256_SECRET`, so both structured logs and generic exception
  responses mask the active MCP HTTP auth secrets alongside the existing
  OS/NOMIS credentials.
- `scripts/run-local-tool` now handles zero-argument wrapper calls correctly,
  and `./scripts/ruff-local` / `./scripts/mypy-local` now default to the same
  curated phased static-analysis slice that CI enforces. The active docs and CI
  configuration now describe and reuse that shared wrapper-defined gate.
- The curated phased Ruff/mypy slice now also covers shared
  `server/config.py` and `server/security.py` infrastructure, with Ruff
  coverage widened to the directly related security and wrapper regression
  tests.
- The OWASP MCP validator now recognizes wrapper-based Ruff CI gates
  (`./scripts/ruff-local`) as equivalent to inline `ruff check`, so the
  committed compliant baseline remains valid after the wrapper-based CI
  cleanup.
- Hardened secret loading in `server/config.py` so placeholder-style values
  such as `${env:OS_API_KEY}` are treated as unset, `*_FILE` fallbacks can
  still hydrate the real secret, and minimal runtimes without
  `pydantic-settings` still read environment-backed settings.
- Added explicit MIT package metadata to `pyproject.toml`, OCI image labels to
  `Dockerfile`, and aligned active Docker-facing docs and wrappers on
  `OS_API_KEY` as the required live credential. `NOMIS_UID` and
  `NOMIS_SIGNATURE` are now the only optional higher-rate stats credentials,
  and stale `ONS_API_KEY` forwarding has been removed from active runtime,
  tracing, benchmark, live-playwright, and CI surfaces.
- Refactored the benchmark and trace helper scripts so the targeted local
  quality gates now pass: `scripts/host_benchmark.py`,
  `scripts/trace_session.py`, `scripts/trace_report.py`, and
  `scripts/trace_utils.py` no longer drag unrelated server modules into the
  `mypy` graph, and the focused Ruff checks for the benchmark/trace scripts and
  regressions are now clean.
- The Council Tax band pilot now recognizes the GOV.UK service's live
  `No results` page shape, so postcode searches with no published matches
  return an empty result set instead of `UPSTREAM_INVALID_RESPONSE`.

## [0.7.0] - 2026-03-16

### Added
- Added repo-authored DOCX hygiene tooling in `scripts/docx_hygiene.py`,
  focused regression coverage in `tests/test_docx_hygiene.py`, the policy note
  `docs/document_hygiene.md`, and generated audit outputs
  `docs/reports/docx_hygiene_audit_2026-03-16.{md,json}`.
- Added the Harold Wood troubleshooting package:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md`,
  `troubleshooting/harold-wood-essex-trace-evidence-2026-03-14.md`, and
  `troubleshooting/harold-wood-essex-deep-analysis-2026-03-14.md`.
- Added the third Harold Wood follow-up transcript working copy and analysis:
  `troubleshooting/Third Harold Wood, after updates.md` and
  `troubleshooting/third-harold-wood-after-updates-analysis-2026-03-15.md`.
- Added the fourth Harold Wood follow-up transcript working copy and
  exhaustive analysis:
  `troubleshooting/Fourth Harold Wood, after updates.md` and
  `troubleshooting/fourth-harold-wood-after-updates-analysis-2026-03-15.md`.
- Added Harold Wood-focused regressions in
  `tests/test_os_mcp_route_query.py` and `tests/test_os_map_tools.py` covering
  conversational place routing, `resource://` bridge guidance, and OS Places
  bbox axis ordering through `os_map.inventory`.
- Added focused regressions in `tests/test_os_places_extra_more_success.py`
  and `tests/test_os_map_tools.py` proving the Harold Wood OS Places clamp now
  stays strictly below the vendor's `< 1 km²` limit.
- Added cross-transport MCP resource fallback support via the new
  `os_resources.get` tool, shared resource-reading helpers in
  `server/mcp/resource_access.py`, normalized `resourceHandoff` metadata in
  `server/mcp/resource_handoff.py`, and focused regression coverage in
  `tests/test_resource_fallback.py`.
- Added hardened production deployment assets under `ops/deployment/`, including a private-network Docker Compose profile, TLS edge proxy example, Docker secret-file delivery contract, and operator runbook for JWT-protected `/mcp` deployments.
- Added monitoring assets under `ops/monitoring/`, including Prometheus scrape configuration, OWASP-oriented alert rules, and Vector SIEM routing for structured container and audit/runtime logs.
- Added OWASP MCP evidence and attestation records under `security/owasp_mcp/evidence/` and `security/owasp_mcp/attestations/`, plus captured live GitHub branch-protection state for `main`.
- Added `.github/CODEOWNERS` to require explicit code-owner review on security-sensitive runtime, tool, workflow, and OWASP validation surfaces.
- Added a repo-pinned OWASP MCP validation namespace under `security/owasp_mcp/`, including the locked control catalog, explicit tool-risk inventory, attestation schema, signed tool manifest lockfile, and committed baseline JSON outputs for the strict `prod-strict` profile.
- Added the OWASP MCP validator implementation in `server/owasp_mcp_validation.py` plus CLI and helper entrypoints `scripts/validate_owasp_mcp_server.py`, `scripts/validate-owasp-mcp-local`, and `scripts/generate_owasp_mcp_tool_manifest.py`.
- Added focused regression coverage in `tests/test_owasp_mcp_validation.py` for strict attestation behavior, high-risk tool applicability, signed-manifest verification, backlog stability, and the current-repo baseline failure path.
- Added the OWASP MCP validation report `docs/reports/owasp_mcp_server_validation_2026-03-13.md` and updated the reports index.
- Added a standalone MCP-Geo analytical index publication set pinned to commit
  `fe862910da246ca77f374cfbe484985f5df4d316`, including the canonical report
  `docs/reports/mcp_geo_analytical_index_2026-03-11.md`, appendix-ready slice
  `docs/reports/mcp_geo_ai_community_appendix_a_replacement_2026-03-11.md`,
  and gap-audit note
  `docs/reports/mcp_geo_analytical_index_gap_audit_2026-03-11.md`.
- Added analytical-index generation assets:
  `data/report_inputs/mcp_geo_analytical_index_manifest.json`,
  `scripts/generate_mcp_geo_analytical_index.py`, eight generated infographic
  figures under `docs/reports/assets/analytical_index/`, and focused coverage
  in `tests/test_generate_mcp_geo_analytical_index.py`.
- Added a regenerated Prism-ready analytical-index bundle under
  `docs/mcp_geo_prism_bundle/`, including `README.md`, `main.md`, `main.tex`,
  `references.bib`, and section fragments under `sections/`.
- Added GitHub Actions CI workflow `.github/workflows/ci.yml` with
  repo-supported Ruff/Mypy gates, full Python regression coverage, multi-arch
  Docker build validation, and GHCR image publication on `main` and `v*` tags.
- Added governed DSAP design and implementation docs:
  `docs/decision_support_audit_pack.md`, `implement.md`, and
  `documentation.md`.
- Added additive DSAP scaffolding under `server/audit/`, including the
  canonical event normalization pipeline in `server/audit/normalise.py`, the
  canonical event schema `server/audit/schemas/event.schema.json`, and
  milestone-placeholder modules and schemas for later DSAP work.
- Added full DSAP Milestones 2-6 under `server/audit/`: pack assembly,
  retained-evidence materialization, completeness grading, decision episodes,
  decision records, source-register held-status handling, disclosure/redaction
  derivatives, SHA-256 integrity manifests with verification, retention-state
  and legal-hold handling, and additive audit HTTP/CLI entrypoints.
- Added DSAP follow-on discovery/hash support: `GET /audit/packs`, bundle
  SHA-256 sidecars for original and derivative zip bundles, and bundle-hash
  metadata surfaced through the audit API.
- Added focused DSAP Milestone 1 regression coverage in
  `tests/test_audit_normalise.py` and `tests/test_trace_report_audit.py`.
- Added DSAP acceptance-focused regression coverage in
  `tests/test_audit_pack_builder.py` and `tests/test_audit_api.py`.
- Added first-class route-planning tools `os_route.descriptor` and
  `os_route.get`, backed by the new pgRouting/PostGIS graph service in
  `server/route_graph.py` and route parsing helpers in
  `server/route_planning.py`.
- Added OS MRN graph bootstrap assets
  `scripts/route_graph_schema.sql` and `scripts/route_graph_pipeline.py` for
  versioned routing-schema setup and download/provenance handling.
- Added stakeholder benchmark pack generator
  `scripts/stakeholder_benchmark_pack.py` to turn the Phase 3 evaluation
  prompts into concrete benchmark scenarios with reusable-header prompts,
  scored reference outputs, and workflow validation.

### Changed
- Sanitized repo-authored public DOCX files under `docs/` and
  `troubleshooting/` to strip personal core metadata and custom Microsoft
  Information Protection properties, and removed a stray Office lockfile from
  `docs/reports/`.
- `os_mcp.descriptor` and tool-search category normalization now accept
  `category="map"` as an alias for `maps`, matching the existing
  `stats -> statistics` tolerance.
- Promoted `admin_lookup.area_geometry`, `os_linked_ids.get`, and
  `os_resources.get` into the starter/always-loaded tool set so Harold Wood
  recovery no longer depends on deferred-tool activation in Claude-like hosts.
- `tools/os_places_extra.py` now targets a safety margin below the published
  1 km² OS Places bbox limit so clamped or tiled helper-generated bboxes do not
  reproduce the fourth Harold Wood `uprns` failure at the strict vendor
  threshold.
- Clarified admin-boundary tool descriptions so `admin_lookup.find_by_name`
  reads as discovery plus bbox summary, while `admin_lookup.area_geometry`
  reads as the route to optional full boundary geometry.
- Added Phase 1 stakeholder benchmark extension module
  `scripts/stakeholder_phase1_extension.py` plus seeded routing helper
  `scripts/seed_benchmark_route_graph.py` so the benchmark harness can expand
  beyond the original 10 scenarios and exercise routed live examples against a
  deterministic graph.
- Added stakeholder benchmark machine-readable assets under
  `data/benchmarking/stakeholder_eval/`, including fixture files, 20 JSON
  reference outputs, and `benchmark_pack_v1.json`.
- Added generated stakeholder benchmark reports
  `docs/reports/MCP-Geo_evaluation_questions.md` and
  `docs/reports/mcp_geo_stakeholder_benchmark_workflow_2026-03-10.md`.
- Added stakeholder gap-analysis report
  `docs/reports/mcp_geo_stakeholder_gap_analysis_2026-03-09.md` explaining why
  the benchmark can score gold answers at `100/100` while current MCP-Geo
  support remains `partial`/`blocked`, and recording the missing capability
  work needed to answer the 10 stakeholder scenarios directly.
- Added stakeholder live-rerun harness `scripts/stakeholder_live_run.py`,
  machine-readable live evidence
  `data/benchmarking/stakeholder_eval/live_run_2026-03-10.json`, second report
  `docs/reports/mcp_geo_stakeholder_live_run_2026-03-10.md`, and focused
  regression coverage in `tests/test_stakeholder_live_run.py`.
- Added focused regression coverage in
  `tests/test_stakeholder_benchmark_pack.py`.
- Added a hardened multi-workbench playground shell under `playground/src/`
  with extracted Explorer, Routing, Audit / FOI, Benchmarks, Debug, and shared
  UI preview components, plus browser-side MCP transport and bridge-policy
  helpers.
- Added stakeholder benchmark demo metadata for all 20 scenarios plus stable
  benchmark resources
  `resource://mcp-geo/stakeholder-benchmark-pack` and
  `resource://mcp-geo/stakeholder-benchmark-live-run-latest`, backed by the
  checked-in alias file `data/benchmarking/stakeholder_eval/live_run_latest.json`.
- Added bounded frontend regression coverage for the new playground shell in
  `playground/tests/playground.spec.js`,
  `playground/tests/bridge_security.spec.js`,
  `playground/tests/routing_workbench.spec.js`,
  `playground/tests/audit_workbench.spec.js`, and
  `playground/tests/benchmark_workbench.spec.js`.
- Added a deterministic fixture-backed full Playwright acceptance suite for
  the playground under `playground/tests/full/`, backed by
  `playground/playwright.full.config.js`, shared helpers in
  `playground/tests/support/full_playground.js`, and a real MCP/DSAP/widget
  fixture server in `playground/tests/support/fixture_server.mjs`.
- Added an env-gated live playground smoke suite under
  `playground/tests/live/live_smoke.spec.js` with
  `playground/playwright.live.config.js` so the real backend can be exercised
  separately from the deterministic fixture suite.
- Added `playground/package.json` scripts `test:full` and `test:live`, plus
  frontend CI failure-artifact upload for the new full and live-smoke suites.
- Added `/ui/vendor/*` resource serving in `server/mcp/resources.py` and
  focused HTTP/resource regressions in `tests/test_resources_data_catalog.py`
  for locally hosted widget vendor assets.
- Added focused regression coverage so published UI resources now normalize
  widget asset URLs to absolute `/ui/shared/*` and `/ui/vendor/*` paths and
  benchmark live-alias resources return structured `INVALID_CONFIGURATION`
  payloads when the alias JSON is valid but not an object.
- Split UI-resource asset publication by transport so HTTP-served widget HTML
  keeps absolute `/ui/...` asset URLs while STDIO and embedded MCP-App payloads
  retain resource-local asset paths that remain fetchable without an HTTP side
  channel.
- Tightened the remaining PR review cleanup by switching `/ui` static asset
  serving to an internal allowlist in `server/mcp/resources.py` and stripping
  stack-like keys from deterministic fixture-server JSON responses in
  `playground/tests/support/fixture_server.mjs`.

### Fixed
- `nomis.query` now reads dataset-specific geography types from NOMIS dataset
  overviews before resolving plain GSS geography codes, so Census 2021 ward
  queries can use the dataset's current geography type (for example `TYPE153`
  / `2022 wards`) instead of relying on the older generic `TYPE297` lookup.
- `nomis.query` now falls back from stale admin-lookup geography codes to the
  current NOMIS geography by area name when the dataset-specific code search
  misses, which restores live Census 2021 responses for cases such as Harold
  Wood (`E05000312` -> `E05013973` -> `641734965`).
- `nomis.query` success payloads now expose richer
  `queryAdjusted.geographyResolution` and `mapping[].currentGss` metadata so
  stale-code recoveries are visible instead of looking like intermittent NOMIS
  failures.
- `admin_lookup` now uses the current ArcGIS ward and district services
  `Wards_December_2024_Boundaries_UK_BGC` and
  `Local_Authority_Districts_December_2024_Boundaries_UK_BGC`, with the
  matching `WD24*` and `LAD24*` fields, so live admin lookups return current
  codes such as Harold Wood ward `E05013973` at the source.

### Tests
- Added focused NOMIS regressions covering dataset-specific geography-type
  resolution and stale ward-code recovery by area-name fallback in
  `tests/test_nomis_data.py`.
- Added admin-lookup regressions locking the default ward/district source
  vintages and proving `admin_lookup._live_find_by_name()` returns the current
  Harold Wood ward code through the 2024 ward service in
  `tests/test_admin_lookup_live_internals.py`.
- Added focused Harold Wood tool-discovery regressions covering exact-name
  `/tools/search` queries for `os_linked_ids.get` and `os_resources.get`,
  transcript-phrase search hits, and descriptor assertions that the Harold
  Wood recovery tools are no longer deferred.

### Changed
- Updated `tools/os_mcp.py` so `os_mcp.route_query` now routes
  `resource://` / large-output recovery prompts to `os_resources.get` and
  `resources/read`, explicitly warns against filesystem searches, and ignores
  conversational prompt openers when extracting place names such as
  `Harold Wood`.
- Updated raw `/tools/call`, `/resources/list`, `/resources/describe`,
  `/resources/read`, and `/resources/download` to enforce the same MCP HTTP
  auth gate surface as `/mcp` when auth is enabled, kept direct HTTP resource
  links opt-in via `MCP_RESOURCE_HTTP_LINKS_ENABLED` and
  `MCP_PUBLIC_BASE_URL`, stripped outward filesystem `path` leakage from
  public resource/tool payloads, and normalized `os_map.export` to return
  `resourceUri` alongside the legacy `uri`.
- Updated MCP HTTP and STDIO tool responses so resource-backed results now add
  spec-native `resource_link` content plus normalized `resourceHandoff`
  metadata, and refreshed README/skill/router guidance to recommend
  `os_resources.get` as the portable fallback when clients cannot invoke
  protocol `resources/read`.
- Updated STDIO resource-handoff decoration to gate `resource_link` blocks on
  advertised MCP-Apps UI support (leaving text handoff metadata intact for
  non-UI hosts), and aligned offline-pack `resources/read` payload resolution
  with `/resources/download` by requiring trusted offline catalog URI matches
  for both paths.
- Hardened the auth-aware raw HTTP/resource fallback follow-up by keeping
  authenticated `/tools/call` parse/lookup errors on the same `mcp-session-id`
  surface, recording authorization failures from `authorize_http_route()` in
  the shared MCP HTTP Prometheus counters, streaming `/resources/download`
  from prevalidated offline-pack paths instead of feeding `FileResponse` a
  user-derived path, rejecting offline-pack symlink escapes outside
  `data/offline_packs`, and returning `INVALID_INPUT` when `os_resources.get`
  receives a `maxBytes` value too small to fit the next UTF-8 codepoint.
- Preserved `mcp-session-id` on raw `/resources/read` 400/404 responses and
  aligned offline-pack discovery with the same catalog-backed whitelist used
  by `/resources/download` and offline-pack `resources/read` payloads.
- Restored range-aware offline-pack downloads by switching `/resources/download`
  back to `FileResponse` on prevalidated pack paths, and normalized all
  `os_resources.get` stream hints (`os_downloads`, `ons_data`) to the shared
  chunk-size contract exposed by `server/mcp/resource_handoff.py`.
- Closed the remaining raw-resource auth parity gaps by moving
  `/resources/list`, `/resources/describe`, `/resources/read`, and
  `/resources/download` query validation behind the shared auth helper,
  preserving `mcp-session-id` on `/resources/download` 400/404 responses, and
  continuing to advertise configured `httpAccess.readUrl` handoffs when MCP
  HTTP auth is disabled.
- Normalized `os_resources.get` UI asset paths by transport so HTTP tool
  callers receive absolute `/ui/...` asset URLs while stdio callers keep
  resource-local relative paths that remain fetchable without an HTTP side
  channel.
- Honored the effective `MCP_APPS_CONTENT_MODE=text` setting for MCP-Apps
  widget tools by setting `uiTextOnlyOverride` from the resolved content mode,
  which prevents raw HTTP and stdio handoff decoration from re-appending
  `resource_link` blocks to text-only UI responses; tightened stdio coverage
  accordingly to validate the loaded settings path rather than incidental
  environment defaults.
- Restored the cross-platform devcontainer trust contract so corporate proxy
  and custom-CA environments use the system certificate bundle, keep proxy
  values build-scoped in the image, source container-wide runtime env from the
  Docker Compose service instead of `devcontainer.json`, and retain both Ruff
  and Svelte editor support in the VS Code extension list. A 2026-03-14
  follow-up refreshes the injected CA trust store before the first devcontainer
  APT fetch so corporate MITM roots under `.devcontainer/certs/*.crt` are
  active for `apt-get update`.
- Rejected JSON boolean values for integer request parameters across the
  resource fallback and discovery surfaces, including `os_resources.get`
  chunking inputs, paginated OS/ONS/admin download/search handlers,
  `os_mcp.select_toolsets.maxTools`, HTTP/stdio tool-search limits, and MCP-Apps
  widget numeric inputs.
- Extended `.github/workflows/ci.yml` with a dedicated `owasp-mcp-validate` job that runs `gitleaks`, `pip-audit`, and the strict OWASP validator with artifact upload, plus a separate OpenSSF Scorecard job for supply-chain posture evidence; paired it with protected-branch enforcement and code-owner review evidence on `main`.
- Updated `README.md`, `docs/Build.md`, `security/owasp_mcp/README.md`, `CONTEXT.md`, and `PROGRESS.MD` to document the hardened `/mcp` auth contract, secret-file delivery, monitoring profile, and the current strict baseline verdict (`compliant`, score `100.0`).
- Updated `docs/reports/README.md`,
  `docs/public_sector_ai_community/14_evidence_and_report_index.md`,
  `CONTEXT.md`, and `PROGRESS.MD` so the analytical-index workflow, appendix
  replacement, and pinned-commit source policy are discoverable in the repo's
  existing documentation and tracker surfaces.
- Stabilized the deterministic playground routing acceptance test by waiting
  for the seeded-demo list to render before selection and by targeting the
  SG03/SG12 scenario buttons through the routing workbench's list-item UI
  instead of a page-wide accessible-name match, eliminating the flaky
  `frontend` CI timeout on PR `#36`.
- Updated the playground bridge resource allowlist so iframe widgets may call
  `resources/read` by either resource URI or resource name, matching the
  accepted MCP request shape and clearing the remaining actionable PR `#36`
  review comment on `playground/src/lib/uiBridge.js`.
- Updated `playground/src/lib/uiBridge.js` so preview-session tool validation
  treats sanitized and original tool aliases as equivalent, allowing live
  widgets that call dotted names such as `os_route.get` to pass the host
  allowlist even when MCP `tools/list` only exposes sanitized aliases such as
  `os_route_get`; added regression coverage in
  `playground/tests/ui_bridge.spec.js` and confirmed the live smoke suite now
  passes `4/4` on fresh ports.
- Fixed the remaining deterministic playground CI race by keeping the host in
  `connecting` state until `refreshLists()`, descriptor load, benchmark load,
  and audit-pack refresh complete, and by no longer forcing the active tab
  back to Explorer at the end of `connect()`. This stops the full-suite
  Benchmarks and Routing specs from being switched away mid-wait on slower
  GitHub runners.
- Added full-UI Explorer resource validation in
  `playground/tests/full/explorer_resources_full.spec.js`, proving that the
  hardened playground still lets users select every baseline fixture resource
  from the Explorer resource list and open each MCP-App resource through the
  host preview flow while keeping data resources viewable in the detail pane.
- Updated `README.md` and `docs/Build.md` to document the published GHCR image
  path and to require absolute `--env-file` paths for GUI desktop clients such
  as Claude Desktop, avoiding broken `.env` resolution outside the repo
  directory.
- Added repo-level LF line-ending policy via `.gitattributes` and
  `.editorconfig`, made devcontainer `ngrok` installation opt-in, and wired
  devcontainer/Docker proxy plus local CA handling through `.devcontainer/.env`
  and `.devcontainer/certs/` so Windows/macOS checkouts and TLS-inspected
  networks behave consistently without touching application code.
- Preserved hard-avoid routing intent in `server/route_planning.py` so route
  queries that omit softening language such as `if possible` now produce hard
  exclusions instead of silent soft penalties.
- Hardened `server/route_graph.py` to reject unparseable `avoidAreas`
  constraints with `INVALID_INPUT` rather than silently dropping them and
  returning an unconstrained route.
- Kept `os_mcp.route_query` route suggestions executable by surfacing
  unresolved free-text avoidance phrases under
  `routeHints.unresolvedAvoidTexts` instead of forwarding invalid
  `avoidAreas` into `os_route.get`.
- Widened `ui/route_planner.html` avoid-id classification so compact tokens
  such as `1001` and `edge-1001` are sent through `avoidIds` rather than the
  geometry-only `avoidAreas` path.
- Hardened `server/mcp/http_transport.py`, `server/maps_proxy.py`, `server/config.py`, and `server/main.py` so remote `/mcp` now supports bounded session state, JWT/static bearer auth hooks, private auth/quota metrics, no upstream bearer passthrough, and file-backed secret hydration.
- Fixed `scripts/generate_mcp_geo_functionality_showcase.py` so the report
  generator no longer uses invalid f-string `"\n".join(...)` expressions that
  break test collection.
- Extended `scripts/trace_report.py` additively so existing traced sessions now
  emit `event-ledger.jsonl` alongside the existing summary and report outputs.
- Extended `scripts/trace_session.py` additively so `session.json` now records
  `endedAt` and `exitCode`, allowing DSAP normalization to emit
  `conversation.closed` without reconstructing missing evidence.
- Extended `server/main.py` and `server/config.py` additively so DSAP packs can
  be assembled, verified, redacted, and placed under the configured
  `AUDIT_PACK_ROOT` without replacing the current tracing stack.
- Extended DSAP pack metadata to report discoverable redacted derivatives and
  bundle-hash sidecars without changing the sealed original pack structure.
- Replaced the route planner's demo-shell behavior with a live MCP-Apps widget
  contract wired to `os_route.get`, including route geometry rendering,
  payload normalization, and explicit graph/ambiguity error states.
- Hardened `os_mcp.route_query` so SG03-style prompts classify as
  `route_planning`, recommend `os_route.get`, and surface route hints before
  postcode/UPRN fast paths fire.
- Fixed `server/route_graph.py` SQL rendering so route execution no longer
  crashes when `_run_leg()` formats a query containing a default JSONB value;
  this removed the live `ROUTE_GRAPH_ERROR` seen in seeded stakeholder runs.
- Switched the devcontainer and local Docker launchers to a pgRouting-capable
  repo-built PostGIS image, aligned them on the
  `PGDATA=/var/lib/postgresql/data/pgdata` layout plus named-volume storage,
  and added idempotent boundary-cache and route-graph schema bootstrap so
  local route readiness no longer depends on a plain PostGIS sidecar or an
  external `pgrouting/pgrouting` image tag.
- Updated the Claude Desktop launcher to reuse the running repo devcontainer
  PostGIS container/network when available, falling back to its own sidecar
  only when the devcontainer database is absent.
- Defaulted the shared Docker launcher to devcontainer-PostGIS reuse for all
  host clients, added `scripts/check_shared_benchmark_cache.sh`, and documented
  the exact benchmark startup order required to guarantee cross-client cache
  parity before scoring Codex vs Claude or stakeholder live runs.
- Sanitized `scripts/route_graph_pipeline.py` provenance capture/output so it
  no longer stores or prints raw DSNs, signed download URLs, or other
  credential-like fields from MRN download metadata.
- Added host/devcontainer-aware tool wrappers `scripts/pytest-local`,
  `scripts/ruff-local`, `scripts/mypy-local`, and `scripts/run-local-tool` so
  host-side verification commands automatically reuse the repo devcontainer,
  then the repo `.venv`, then `uv run`.
- Replaced the Phase 3 evaluation-question note with a comprehensive benchmark
  pack that embeds populated prompts, comparator notes, capability gaps, and
  full expected-output JSON for 20 scenarios, including a new 10-scenario
  Phase 1 extension.
- Clarified the stakeholder benchmark report so `Reference score` is explicitly
  described as gold-answer completeness, not current MCP-Geo capability
  completeness.
- Added an authenticated live rerun of the stakeholder scenarios and reported
  the result separately from the benchmark pack. The latest seeded-graph live
  rerun reports `1` first-class-ready scenario, `17 partial`, and `2 blocked`,
  with live OS-backed evidence proven in-session via `OS_API_KEY_FILE`. SG03
  now returns a full routed answer on the seeded graph and SG12 moves from
  blocked to partial; SG17 and SG20 remain blocked for capability reasons.
- Upgraded the playground dependency/runtime baseline to
  `@modelcontextprotocol/sdk 1.27.1`, `svelte 5.53.10`,
  `@sveltejs/vite-plugin-svelte 6.2.4`, and `vite 7.3.1`, added npm overrides
  to clear the Hono / Svelte / Rollup / esbuild / AJV / express-rate-limit
  Dependabot chain, and pinned the Node baseline to `20.19.0` in the
  devcontainer and frontend CI.
- Hardened the MCP-Apps iframe bridge so same-origin is no longer auto-enabled
  in dev, each preview issues a session token, host-side message handling now
  validates origin/method/tool/resource allowlists, and rejected widget
  requests are surfaced in the Debug workbench.
- Replaced the playground's bounded mock-first CI browser run with a
  deterministic full UI Playwright suite and added a separate manual live-smoke
  job in `.github/workflows/ci.yml`.
- Fixed hosted widget route-demo regressions by accepting dotted and sanitized
  tool aliases through `playground/src/lib/uiBridge.js`, normalizing SG03/SG12
  route config before `ui/notifications/tool-input`, proxying `/ui` through
  Vite, and switching hosted widgets to local `/ui/vendor/` MapLibre assets
  instead of CDN-loaded scripts/styles.
- Tightened the follow-up playground review fixes by honoring
  `PLAYGROUND_FULL_FRONTEND_PORT` throughout
  `playground/playwright.full.config.js`, restoring the devcontainer's system
  CA / custom-cert contract in `.devcontainer/Dockerfile`, replacing
  parameterized `/ui/shared/*` and `/ui/vendor/*` asset handling with fixed
  static endpoints in `server/mcp/resources.py`, and simplifying CSP-domain
  regression assertions so CodeQL sees exact allowlists instead of parsed URL
  host filtering.
- Aligned `playground/src/lib/uiBridge.js` with the effective iframe sandbox by
  deriving preview-session origin expectations from the actual widget
  `sameOrigin` permission rather than the raw unsafe-toggle state, and mirrored
  the fixed-asset serving pattern in
  `playground/tests/support/fixture_server.mjs` so the deterministic fixture
  harness no longer performs request-driven UI asset path joins.
- Stopped injecting a synthetic deny-all CSP into widget previews when a UI
  resource publishes no `ui.csp` metadata, preserving existing map-widget
  network behavior while keeping explicit CSP injection for widgets that do
  declare allowed domains.
- Preserved active widget preview tokens across catalog refreshes, hardened the
  stakeholder benchmark live-alias loader to return structured
  `INVALID_CONFIGURATION` payloads for malformed JSON, and made the
  analytical-index top-level validator fall back to `HEAD` when CI's shallow
  checkout does not contain the pinned citation commit object locally.
- Tightened `os_route.get` schema publication for strict MCP clients by adding
  explicit `items` definitions to array-typed route constraints and outputs, so
  VS Code no longer rejects the tool during post-initialize validation.

## [0.6.0] - 2026-03-08

### Added
- Added shared Docker-backed stdio launcher `scripts/mcp-docker-local` plus
  Codex-specific launcher `scripts/codex-mcp-local`, keeping
  `scripts/claude-mcp-local` Claude-only.
- Added Codex startup-scope probe `scripts/check_codex_startup_scope.sh`.
- Added shared `openaiDeveloperDocs` MCP configuration pointing at
  `https://developers.openai.com/mcp` in `mcp.json`, `.vscode/mcp.json`, and
  `scripts/devcontainer_mcp_setup.sh`.
- Added Codex-vs-Claude host benchmark scenario pack
  `docs/benchmarking/codex_vs_claude_host_scenarios_v1.json`.
- Added host benchmark runner `scripts/host_benchmark.py` for scenario export,
  Codex CLI runs, per-session scoring, and aggregate comparison reports.
- Added benchmark runbook
  `docs/benchmarking/codex_vs_claude_host_benchmark.md`.
- Added `scripts/generate_teignmouth_wheelchair_access_map.py` plus live Teignmouth
  wheelchair-access artifacts:
  `docs/reports/teignmouth_wheelchair_access_map_2026-03-07.{html,md}`,
  `data/exports/teignmouth_wheelchair_access_map_2026-03-07.json`, and
  `output/playwright/teignmouth-wheelchair-access-map-2026-03-07.png`.
- Added Exmouth comparator artifacts:
  `docs/reports/exmouth_wheelchair_access_map_2026-03-07.{html,md}`,
  `data/exports/exmouth_wheelchair_access_map_2026-03-07.json`,
  `output/playwright/exmouth-wheelchair-access-map-2026-03-07.png`, and
  `docs/reports/teignmouth_exmouth_sidmouth_access_comparison_2026-03-07.md`.
- Added Sidmouth comparator artifacts:
  `docs/reports/sidmouth_wheelchair_access_map_2026-03-07.{html,md}`,
  `data/exports/sidmouth_wheelchair_access_map_2026-03-07.json`, and
  `output/playwright/sidmouth-wheelchair-access-map-2026-03-07.png`.
- Added repeatable showcase-report inputs and generation pipeline:
  `data/report_inputs/mcp_geo_functionality_showcase_examples.json`,
  `scripts/generate_mcp_geo_functionality_showcase.py`, and focused parser
  coverage in `tests/test_generate_mcp_geo_functionality_showcase.py`.
- Added public showcase artifacts:
  `docs/reports/mcp_geo_functionality_showcase_2026-03-07.{md,docx,pdf}`,
  supporting figure assets under `docs/reports/assets/`, public companion note
  `docs/reports/stanley_house_clampet_lane_context_case_2026-03-07.md`, and
  tracked Stanley House illustration PNGs under `output/playwright/`.

### Changed
- Updated `scripts/devcontainer_mcp_setup.sh` so Codex registers `mcp-geo`
  against `scripts/codex-mcp-local` instead of the Claude wrapper.
- Deprecated the local OpenAI-docs vendor workflow in `docs/vendor/openai/` and
  switched repo guidance to the official OpenAI Documentation MCP for current
  developer docs.
- Extended `scripts/trace_session.py` and `scripts/trace_report.py` with
  host-aware metadata/reporting (`source`, `surface`, `hostProfile`,
  `clientVersion`, `model`, `scenarioPack`, `scenarioId`, `summary.json`).
- Extended host-simulation fixtures and compact host profiles with benchmark
  profiles for `codex_cli_stdio`, `codex_ide_ui`, and
  `claude_desktop_ui_partial`.
- Updated `docs/reports/README.md`, `CONTEXT.md`, and `PROGRESS.MD` to index the
  new Teignmouth wheelchair-access map work.
- Refined the Teignmouth wheelchair-access HTML map to fit wide browser windows
  cleanly, reduce named corridor callouts to a single representative segment per
  street, and move access-point labels into the sidebar with numbered map
  markers plus hover evidence text.
- Refined the wheelchair-access report generator and regenerated the Teignmouth,
  Exmouth, and Sidmouth map artefacts with Web Mercator overlay alignment,
  slimmer route casing, and an optional browser-side `OS Detailed` vector
  basemap toggle for richer street-name and building context without obscuring
  labels.
- Extended the wheelchair-access HTML maps with wheel zoom, drag pan, reset
  controls, zoom-aware scale bars, and browser-side OS vector basemap syncing
  so the optional `OS Detailed` context sharpens as the user zooms in.
- Extended `scripts/generate_teignmouth_wheelchair_access_map.py` with reusable
  place presets and OS export-resource handling so wider footprints like Exmouth
  can be generated with the same scoring logic.
- Added Sidmouth as a compact-core preset and updated the comparison note to
  distinguish Exmouth as the strongest positive comparator from Sidmouth's
  smaller but tighter seafront-market core.
- Added repo guidance in `AGENTS.md` plus the new skill
  `skills/mcp-geo-detailed-os-maps/SKILL.md` so future agents default to
  MapLibre + OS vector detail for user-facing report maps.
- Added `--reuse-export` to `scripts/generate_teignmouth_wheelchair_access_map.py`
  so HTML and note artefacts can be regenerated reliably from saved JSON exports
  when presentation changes do not require a fresh live data pull.
- Fixed `os_poi.search` bbox handling to filter text-search results locally
  instead of sending unsupported bbox coordinates to the OS Places `/find`
  endpoint; updated focused regression coverage in `tests/test_os_poi.py`.
- Updated `docs/reports/README.md`, `CONTEXT.md`, and `PROGRESS.MD` to index the
  new functionality-showcase report workflow and generated outputs.

## [0.5.0] - 2026-03-04

### Added
- Added a UK Public Sector AI Community documentation collection under
  `docs/public_sector_ai_community/`, including:
  - novice/apprentice-oriented chapter set with section-level diagrams
  - full project journey coverage (origin, timeline, standards/client evolution,
    harness permissions and troubleshooting loops, evaluation, BDUK extension
    requirements, RBAC/ABAC considerations, and future direction)
  - evidence index linking repository research and troubleshooting artifacts.
- Added Prism-ready LaTeX publication output for the documentation set under
  `docs/public_sector_ai_community/prism/` (`main.tex`, sectionized chapters,
  bibliography, and compile/runbook README).
- Added refreshed Codex long-horizon summary artifacts for 2026-03-04:
  `docs/reports/mcp_geo_codex_long_horizon_summary_2026-03-04.{md,json,svg}`.
- Added public-release security review artifact:
  `docs/reports/public_release_security_review_2026-03-04.md`.
- Added release notes for public launch candidate:
  `RELEASE_NOTES/0.5.0.md`.
- Added a simple map exploration UI resource (`ui://mcp-geo/simple-map-lab`)
  and implementation (`ui/simple_map.html`) for minimal OS Vector vs PMTiles
  trials with basic timing telemetry and deterministic pan-benchmark controls.
- Added `docs/simple_map_lab.md` with a focused runbook for browser bearer auth
  vs API-key fallback tests and PMTiles trial execution.
- Added `scripts/check_claude_startup_scope.sh` to validate Docker-backed
  Claude startup discovery scope (baseline vs scoped `tools/list` counts) so
  toolset config regressions can be detected quickly.
- Added complete Map Lab novice-learning and selector workflow on the
  compatibility-locked boundary explorer integration surface:
  - Help/Map/Collections tab shell in `ui/boundary_explorer.html`
  - detailed "Welcome to Map Lab" tutorial sections with curated external
    references and persisted help state (`maplab.help.*` keys for tab, scroll,
    section fold state, TOC collapse, and last step)
  - local selector-based collection CRUD/import/export with GSS level picker
    and explicit UPRN include/exclude overrides
  - async collection export flow from UI using
    `os_map.export` (`exportType=selection_uprn`) and `os_map.get_export`.
- Added selector-driven async export backend for Map Lab in `tools/os_map.py`:
  - extended `os_map.export` with backward-compatible `selection_uprn` mode
  - new `os_map.get_export` polling/status tool
  - async export job status/result artifacts under
    `resource://mcp-geo/os-exports/jobs/*.json` and
    `resource://mcp-geo/os-exports/*.csv|json`
  - selector resolver pipeline covering `gss_code`, `postcode`, `uprn`, and
    `polygon` selectors, include/exclude overrides, and delivery-filter
    warnings for missing delivery flags.
- Added ONS UPRN reverse-lookup index support for scalable selector resolution:
  - new `ons_geo_uprn_index` schema/indexes in `server/ons_geo_cache.py`
  - refresh ingest population in `scripts/ons_geo_cache_refresh.py` for
    postcode, OA/LSOA/MSOA/LAD codes, local-authority name, delivery flag,
    and serialized geography fields.
- Added a novice-first Map Lab help research blueprint at
  `docs/reports/map_lab_help_resources_2026-02-28.md`, including curated
  references for web mapping fundamentals, UK OS/ONS geographies, and
  stateful Help-tab UX patterns for tutorial-style learning flows.
- Added `docs/codex_usage_examples.md` as a reusable portfolio of Codex
  delivery examples for `mcp-geo`, grounded in git commits/PRs and session
  telemetry artifacts.
- Added refreshed Codex long-horizon session telemetry artifacts for
  `2026-03-01` in
  `docs/reports/mcp_geo_codex_long_horizon_summary_2026-03-01.{md,json,svg}`.

### Changed
- Updated top-level documentation navigation in `README.md` to include the new
  UK Public Sector AI Community documentation set and Prism publication entry.
- Added a public-launch caveat statement in `README.md` clarifying personal
  development status and non-endorsement.
- Updated reports index `docs/reports/README.md` with current Codex summary
  report links (2026-03-04 and baseline 2026-02-25).
- Updated reports index `docs/reports/README.md` to include the public-release
  security review entry.
- Bumped package version to `0.5.0` in `pyproject.toml` and `server/__init__.py`.
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
- Added compact startup catalog behavior in `server/stdio_adapter.py` for
  Claude sessions (`MCP_STDIO_LIST_COMPACT`, auto-enabled for Claude) so
  `tools/list` and `resources/list` omit heavy optional metadata
  (`outputSchema`, `toolsets`, resource `_meta` CSP blocks) and reduce startup
  payload pressure.
- Updated `scripts/claude-mcp-local` to hydrate `OS_API_KEY`/`ONS_API_KEY`
  without hardcoding secrets in MCP config, using fallback resolution from
  process env, `*_FILE` env, macOS `launchctl getenv`, and repo `.env`
  (`MCP_GEO_ENV_FILE` override supported).
- Added direct server support for `OS_API_KEY_FILE` in `server/config.py` and
  updated MCP templates/docs (`mcp.json`, `.vscode/mcp.json`, `.env.example`,
  `README.md`, `docs/getting_started.md`, `docs/vscode.md`) so file-based key
  injection can be used consistently across wrapper and non-wrapper launches.
- Hardened `nomis.query` compatibility/error handling by normalizing common
  model-generated params (`date` -> `time`, dropping `cell` for JSON-stat),
  and returning actionable `NOMIS_QUERY_ERROR` guidance with
  `missingDimensions`, `suggestedParams`, and dataset-specific measure hints.
- Extended `nomis.query` recovery for incomplete/invalid queries by adding an
  overview-driven auto-retry path that fills missing required dimensions,
  removes unknown dimension keys, and reports adjustments in
  `queryAdjusted.dimensionAutoAdjust`.
- Added tool-search category alias normalization (`stats` -> `statistics`) so
  `os_mcp.descriptor`/tool search filters remain stable for constrained client
  payloads that use shorthand category names.
- Hardened `os_features.query` `resultType=hits` semantics so `count` now
  reflects matched-signal estimates (`numberMatched` when available, otherwise
  bounded fallback counts) instead of `numberReturned` alone, and now emits
  explicit warning metadata (`HITS_NUMBER_MATCHED_UNAVAILABLE`,
  `HITS_COUNT_LOWER_BOUND`, optional `matchedCountLowerBound`) when totals are
  uncertain.
- Added legacy transport collection compatibility mapping in
  `tools/os_features.py` so `trn-fts-roadlink-*` requests normalize to
  `trn-ntwk-roadlink-*` while preserving `requestedCollection` and exposing
  `COLLECTION_ALIAS_APPLIED` warning metadata.
- Enriched unsupported-collection `OS_API_ERROR` payloads in
  `os_features.query` with actionable repair guidance (`requestedCollection`,
  `resolvedCollection`, `suggestedCollections`, `hint`) and added focused
  regression coverage in `tests/test_os_features_collections.py`.
- Updated troubleshooting docs with the new wrapper key-resolution order and
  restart guidance for Claude Desktop after key rotation.
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
- Updated visible UI/resource text from Boundary Explorer/simple phrasing to
  "Map Lab" while preserving compatibility entrypoints
  (`ui://mcp-geo/boundary-explorer`, `os_apps.render_boundary_explorer`).
- Updated resource delivery for OS export artifacts to support nested job and
  result files plus MIME-aware reads across HTTP and STDIO (`text/csv` for CSV
  artifacts, `application/json` for JSON artifacts) in
  `server/mcp/resource_catalog.py`, `server/mcp/resources.py`, and
  `server/stdio_adapter.py`.
- Updated map rendering UX with hierarchy preset control (`auto`, `detail`,
  `balanced`, `links`) and automatic tab switch to Map for map-render actions
  while preserving Help tutorial state.
- Updated Map Lab boundary rendering/readability controls in
  `ui/boundary_explorer.html`:
  - boundary areas now default to outline-only (`Area fill` off) while keeping
    interaction via a dedicated invisible hit layer
  - added live opacity controls for basemap dimming, boundary fill, UPRN
    density, buildings, and road/path links
  - added dynamic Guidance & Status panel plus cache-status visibility backed
    by `admin_lookup.get_cache_status` and `ons_geo.cache_status`
  - hardened sandboxed-host storage fallback to avoid `localStorage`
    `SecurityError` breaks.
- Added boundary explorer UI regression coverage for option effects and runtime
  diagnostics in `playground/tests/boundary_explorer_controls.spec.js`, plus a
  bundled runner command `npm --prefix playground run test:boundary-ui`.
- Added exhaustive boundary option matrix Playwright coverage in
  `playground/tests/boundary_explorer_option_matrix.spec.js`, exercising
  hierarchy presets, detail levels, layer toggles, border mode, and opacity
  controls with per-scenario screenshot captures and a JSON matrix summary
  artifact attached to test output.
- Updated rate-limit middleware to support configurable exempt path prefixes
  via `RATE_LIMIT_EXEMPT_PATH_PREFIXES` and set default exemptions for
  high-volume map tile paths (`/maps/vector/vts/tile`,
  `/maps/raster/osm`, `/maps/static/osm`) so local map rendering avoids
  false-positive `429 RATE_LIMITED` responses.
- Updated devcontainer storage defaults to keep mutable runtime data outside
  the git worktree:
  - `.devcontainer/docker-compose.yml` now uses Docker named volumes for
    PostGIS (`MCP_GEO_POSTGIS_VOLUME`) and runtime cache/log data
    (`MCP_GEO_RUNTIME_DATA_VOLUME`) instead of `../data/postgres` bind mounts.
  - Devcontainer app env now points cache/log paths at `/var/lib/mcp-geo/...`
    (`ONS_DATASET_CACHE_DIR`, `ONS_GEO_CACHE_DIR`, `OS_DATA_CACHE_DIR`,
    `UI_EVENT_LOG_PATH`, `PLAYGROUND_EVENT_LOG_PATH`).
  - `scripts/devcontainer_post_start.sh` now ensures the runtime data root is
    writable by `vscode`.
- Updated `scripts/claude-mcp-local` PostGIS storage defaults to named-volume
  mode (`MCP_GEO_POSTGIS_STORAGE_MODE=volume`) with explicit legacy bind-mount
  opt-in (`MCP_GEO_POSTGIS_STORAGE_MODE=bind` + `MCP_GEO_POSTGIS_DATA_DIR`).
- Updated resource cache-path resolution so `resource://mcp-geo/ons-cache/*`
  follows `ONS_DATASET_CACHE_DIR` rather than always reading
  `data/cache/ons`.
- Hardened devcontainer/VS Code STDIO dependency bootstrap to avoid
  `ModuleNotFoundError: loguru` on rebuild/startup:
  - `.devcontainer/devcontainer.json` now installs core runtime (`-e .`) first
    before optional extras.
  - `scripts/devcontainer_post_start.sh` now auto-installs core runtime first,
    then optional dev/test extras.
  - `scripts/vscode_mcp_stdio.py` and `scripts/os_mcp.py` now attempt
    best-effort runtime bootstrap install when `loguru` is missing and emit
    actionable error guidance when bootstrapping fails.
- Hardened VS Code devcontainer interpreter selection and launcher resilience
  for mixed host/container workflows:
  - `.devcontainer/devcontainer.json` now defaults VS Code Python interpreter
    to `/usr/bin/python3` in container.
  - `scripts/vscode_mcp_stdio.py` now treats broken/unspawnable interpreter
    paths (for example host-created `.venv` inside Linux container) as
    unavailable and falls back cleanly instead of crashing.
- Hardened devcontainer cold-start cache behavior so new named volumes no
  longer surface immediate `BOUNDARY_CACHE_ERROR` / `cache_unavailable`
  confusion in Map Lab:
  - `scripts/devcontainer_post_start.sh` now auto-creates PostGIS boundary
    cache tables from `scripts/boundary_cache_schema.sql` when
    `BOUNDARY_CACHE_ENABLED=true` and required tables are missing.
  - `scripts/devcontainer_post_start.sh` now auto-seeds `ons_geo` SQLite cache
    from bundled bootstrap CSVs when the cache DB is absent/empty.

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
