# MCP Geo Context

Last updated: 2026-03-25
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
  admin lookup/ONS/NOMIS/Council Tax pilot tools; boundary cache pipeline; MCP-Apps UI
  resources via `ui://`.

## Codex Usage (Mac App + Devcontainer)

- `CONTEXT.md` is the durable, cross-surface source of truth; read and update it at session start.
- Devcontainer persistence: `CODEX_HOME` is mounted to the named volume `mcp-geo-codex`
  in `.devcontainer/devcontainer.json`, so Codex local state survives rebuilds.
- Spec package exports are ignored in git: `docs/spec_package/build/`.
- External ref (Codex app overview/install): `https://developers.openai.com/codex/app/`.
- External ref (Codex app features): `https://developers.openai.com/codex/app/features`.
- OpenAI developer docs are now expected to be read via the shared
  `openaiDeveloperDocs` MCP server (`https://developers.openai.com/mcp`) when
  current OpenAI/Codex/API/App SDK guidance is needed; `docs/vendor/openai/`
  is deprecated legacy fallback material only.
- External ref (Codex app announcement): `https://openai.com/index/introducing-the-codex-app/`.
- External ref (VS Code devcontainer mounts): `https://code.visualstudio.com/remote/advancedcontainers/add-local-file-mount`.
- External ref (Docker volumes reference): `https://docs.docker.com/engine/storage/volumes/`.

## Current Focus

- Maintaining the new 2026-03-25 experimental Council Tax pilot under
  `tools/council_tax.py`, `README.md`, `PROGRESS.MD`, and related tests. The
  first implementation is intentionally scoped to England/Wales public band
  lookup only via the GOV.UK/HMRC service, with premise-level band matches and
  billing-authority metadata as the target contract. Live probing on
  2026-03-25 showed that the upstream public form flow can reject scripted
  POSTs with the generic service-error page even when CSRF/cookie handling is
  mirrored, so the pilot keeps the HTML-scrape provider explicit and surfaces
  that instability as an upstream constraint rather than treating it as a
  stable API. The follow-on gold fixture pack in
  `tests/fixtures/council_tax*` now captures curated published examples from
  the GOV.UK service, and the live no-results page title is treated as a
  grounded empty-search outcome rather than a parser failure.
- Maintaining the 2026-03-24 remediation follow-up under
  `docs/reports/mcp_geo_full_code_review_2026-03-24.md` and `PROGRESS.MD`.
  The raw HTTP auth gap is now closed for `/metrics`, `/tools/list`,
  `/tools/describe`, `/tools/search`, and `/playground/*`, leaving only
  `GET /health` public when MCP HTTP auth is enabled. The shared
  secret-redaction path now also masks `MCP_HTTP_AUTH_TOKEN` and
  `MCP_HTTP_JWT_HS256_SECRET` in generic exception responses and structured
  logs. The host-side wrapper zero-argument path is now repaired for
  `scripts/ruff-local` and `scripts/mypy-local`, those wrapper defaults now
  define the active curated static-analysis slice, and CI plus
  `scripts/check_non_runtime_quality.sh` reuse that shared gate directly. The
  first follow-on expansion now includes shared `server/config.py` and
  `server/security.py` infrastructure, plus the directly related Ruff
  regression tests. The OWASP MCP validator also now treats wrapper-based Ruff
  CI gates as equivalent to inline `ruff check`, preserving the compliant
  baseline after the wrapper cleanup. Remaining review-driven work is the next
  incremental expansion beyond that shared config/security slice.
- Maintaining Docker MCP catalog submission readiness in the repo, including
  the new root `LICENSE` / `SECURITY.md`, Docker OCI image labels, the active
  doc cleanup that standardizes on `OS_API_KEY` plus optional
  `NOMIS_UID` / `NOMIS_SIGNATURE`, and the internal submission draft under
  `docs/docker_mcp_catalog_submission.md` for the follow-on
  `docker/mcp-registry` PR.
- Maintaining the 2026-03-17 secret-loading hardening follow-up in
  `server/config.py`, including placeholder-value normalization for
  `${env:OS_API_KEY}`-style injections, `OS_API_KEY_FILE` fallback hydration,
  and the minimal-settings fallback path that now reads environment-backed
  defaults even when `pydantic-settings` is unavailable.
- Published release `v0.7.0`, including the post-`0.6.0` changelog/release
  packaging, the merged docs-only follow-up for
  `docs/reports/Working with Codex redacted.docx`, and the validated
  `./scripts/pytest-local -q` release gate (`1200 passed`, `6 skipped`,
  coverage `90.26%`).
- Maintaining the 2026-03-16 release-CI follow-up in `.github/workflows/ci.yml`
  that skips the OpenSSF Scorecard `supply-chain-posture` job on `v*` tag
  pushes, because the action only supports pull requests and the default-branch
  ref surface; the SARIF upload step now also runs only when the Scorecard file
  exists so unsupported refs do not add a second missing-artifact failure.
- Maintaining the new public-document hygiene workflow for repo-authored DOCX
  assets under `docs/` and `troubleshooting/`, including the metadata-stripping
  sanitizer/checker in `scripts/docx_hygiene.py`, the policy note
  `docs/document_hygiene.md`, the audit outputs
  `docs/reports/docx_hygiene_audit_2026-03-16.{md,json}`, and the first-pass
  sanitation of repo-authored public DOCX files to remove personal core
  metadata and custom MSIP properties before wider release.

- Maintaining the 2026-03-14 NOMIS dataset-geography recovery in
  `tools/nomis_data.py`, including dataset-specific geography-type lookup,
  stale-code recovery by area name, focused regressions in
  `tests/test_nomis_data.py`, and the follow-on live-source refresh in
  `tools/admin_lookup.py` that moves ward/district lookups to the 2024 ArcGIS
  services so Harold Wood now resolves to current ward code `E05013973`
  directly at source.
- Maintaining the Harold Wood trace analysis package under `troubleshooting/`,
  including the new evidence/deep-analysis reports, route-query hardening for
  `resource://` recovery prompts and conversational place extraction, the
  Harold Wood bbox regression coverage, and the same-route Codex validation
  artifact under
  `logs/sessions/20260314T203104Z-harold-wood-wrapper-validation/`.
- Maintaining the 2026-03-15 third Harold Wood follow-up analysis under
  `troubleshooting/`, including the new transcript working copy and analysis
  that separate ward-geometry discoverability from client/runtime failures on
  `resource://` export consumption and `os_mcp.select_toolsets`, plus the
  follow-on metadata and startup-profile cleanup that makes
  `admin_lookup.find_by_name` explicitly bbox-oriented,
  `admin_lookup.area_geometry` explicitly polygon-capable,
  `os_mcp.descriptor` tolerant of `category="map"` as an alias for `maps`, and
  the Harold Wood recovery tools (`admin_lookup.area_geometry`,
  `os_linked_ids.get`, `os_resources.get`) always loaded instead of deferred.
- Maintaining the 2026-03-15 fourth Harold Wood follow-up analysis under
  `troubleshooting/`, including the new transcript working copy and exhaustive
  report that narrow the remaining hard server-side defect to the strict OS
  Places `< 1 km²` clamp in `os_places.within`, plus the follow-on helper fix
  that now targets a safety margin below the vendor threshold and the focused
  Harold Wood regressions in `tests/test_os_places_extra_more_success.py` and
  `tests/test_os_map_tools.py`.
- Finalizing public launch packaging for `v0.5.0`, including secret/sensitive
  content review, release notes, tagging, and repository visibility transition
  to Public.
- Prioritizing reliable layered map rendering (polygons, lines, points) across
  all clients, with interaction as progressive enhancement where host runtime
  supports MCP-Apps UI; repo-side `LMR-BASE-0` through `LMR-FBK-3` are complete
  (2026-02-21), `LMR-GATE-5` is complete with documented map-quality
  waiver/threshold policy, and external host/runtime risk remains tracked
  explicitly under `LMR-HOST-4`.
- Keeping the completed phased progress program stable with full regression coverage.
- Driving the OS catalog/tooling gap closure plan via parallel workstreams.
- Maintaining the new GitHub Actions CI + GHCR multi-arch image workflow,
  including the repo-supported Ruff/Mypy gate surface plus full Python pytest
  coverage on PRs and pushes.
- Maintaining post-remediation safe-by-design/governance compliance against UK
  standards (NCSC/ICO/Data Ethics Framework/ATRS/Five Safes), OWASP LLM
  guidance, W3C provenance/catalog standards, and MCP `2025-11-25`.
- Maintaining the new rerunnable OWASP MCP validation pack under `security/owasp_mcp/`, including the strict baseline report `docs/reports/owasp_mcp_server_validation_2026-03-13.md`, signed tool manifest verification, CI artifact publication, and attestation-backed control evaluation. The current strict score is `100.0` with verdict `compliant`; the repo now has committed deployment/auth/governance attestations, hardened `/mcp` auth and session controls, private monitoring assets, and no live token passthrough in `server/maps_proxy.py`.
- Maintaining the new auth-aware cross-transport resource fallback so clients
  that do not auto-resolve `resource://` URIs can still retrieve MCP
  resources safely via `os_resources.get`, while HTTP `/tools/call` and
  `/resources/*` now follow the same auth gate surface as `/mcp` when MCP
  HTTP auth is enabled and direct HTTP resource links remain opt-in only. The
  2026-03-14 PR `#39` follow-up also keeps raw `/tools/call` parse/lookup
  errors on the authenticated session header surface, records authorization
  failures in the shared HTTP auth metrics, streams `/resources/download` only
  from prevalidated offline-pack paths, rejects offline-pack symlink escapes
  outside `data/offline_packs`, and makes `os_resources.get` fail cleanly when
  `maxBytes` cannot fit the next UTF-8 codepoint. The latest follow-up also
  keeps raw `/resources/read` 400/404 responses on the same `mcp-session-id`
  surface and aligns `offline-packs-index` discovery with the same trusted
  catalog whitelist used for offline-pack reads/downloads. Offline-pack
  downloads now retain `Range`/resume semantics via `FileResponse` on the
  prevalidated pack path, and all resource-backed stream hints that point
  callers at `os_resources.get` now use the shared chunk-size limits from
  `server/mcp/resource_handoff.py`. A second 2026-03-14 manual-review pass
  moved raw `/resources/*` query validation behind `authorize_http_route()` so
  unauthenticated bad-query requests no longer bypass the 401/403 surface via
  FastAPI 422s, preserved `mcp-session-id` on `/resources/download` 400/404
  responses, and kept configured `httpAccess.readUrl` handoffs visible even
  when MCP HTTP auth is disabled. A final 2026-03-14 follow-up made
  `os_resources.get` transport-aware for `ui://` resources, so HTTP tool
  callers now receive absolute `/ui/...` asset URLs while stdio callers retain
  relative resource-local asset paths.
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
- Standardizing repo-level Codex execution telemetry using a Long Horizon-style
  session summary workflow for repeatable reporting.
- Standardizing repo extent/complexity telemetry with generated-output
  exclusion and hotspot scoring for risk-focused maintenance planning.
- Exploring a simple-map delivery path that prioritizes browser bearer auth for
  OS vector tiles with deterministic fallback to server `OS_API_KEY`, plus
  PMTiles trial instrumentation.
- Reviewing MCP-Apps small-window host constraints (Claude/VS Code) and
  standardizing compact UI design budgets + redesign artifacts for all MCP-Apps
  views.
- Operating Figma MCP as a secondary collaboration surface (capture + annotate),
  with design decisions anchored in repo review artifacts due capture-fidelity
  caveats on SVG-embedded text.
- Maintaining completed unattended compact-window implementation on
  `codex/compact-windows` with strict six-UI acceptance gating, including
  smoke + matrix Playwright evidence.
- Publishing and maintaining the UK Public Sector AI Community documentation
  set (`docs/public_sector_ai_community/`) with novice/apprentice pathways,
  timeline synthesis, and Prism-ready LaTeX outputs.
- Publishing and maintaining the new MCP-Geo analytical index package under
  `docs/reports/mcp_geo_analytical_index_2026-03-11.md` plus the regenerated
  Prism bundle in `docs/mcp_geo_prism_bundle/`, pinned to commit
  `fe862910da246ca77f374cfbe484985f5df4d316` for stable GitHub citations.
- Benchmarking Codex GPT-5.4 as a first-class MCP host alongside Claude
  Desktop Opus 4.6, including launcher separation, trace/session scoring, and
  reproducible comparison reports.
- Implementing the new Decision Support Audit Pack (DSAP) program as an
  additive audit layer over the existing trace/session tooling. Milestones 1-6
  are now in place under `server/audit/` with canonical event normalization,
  pack assembly, integrity manifests, episode slicing, decision records,
  source registers, disclosure/redaction derivatives, retention-state support,
  legal-hold handling, dedicated audit HTTP/CLI entrypoints, pack discovery
  under `AUDIT_PACK_ROOT`, and SHA-256 sidecars for original and derivative
  bundle zips.
- Maintaining the new OS MRN route-planning stack under `tools/os_route.py`,
  `server/route_graph.py`, `server/route_planning.py`, and
  `ui/route_planner.html`, with pgRouting/PostGIS graph readiness surfaced via
  `os_route.descriptor` and SG03-style prompts routed through
  `os_route.get`.
- Maintaining the stakeholder-evaluation benchmark pack under
  `scripts/stakeholder_benchmark_pack.py` and
  `data/benchmarking/stakeholder_eval/` so the Phase 3 prompt bank stays tied
  to concrete public examples, scored reference outputs, a repeatable
  workflow note, and the Phase 1 extension scenarios added on 2026-03-10 via
  `scripts/stakeholder_phase1_extension.py`.
- Tracking the follow-up stakeholder capability gap analysis in
  `docs/reports/mcp_geo_stakeholder_gap_analysis_2026-03-09.md`, including the
  separation between benchmark gold-answer scoring and current MCP-Geo feature
  completeness plus the missing work to make the 20 scenarios runnable against
  live tools.
- Maintaining the stakeholder live-rerun harness under
  `scripts/stakeholder_live_run.py` and the resulting evidence artifacts under
  `data/benchmarking/stakeholder_eval/live_run_2026-03-10.json` and
  `docs/reports/mcp_geo_stakeholder_live_run_2026-03-10.md`, so authenticated
  OS-backed reruns can be compared directly with the benchmark pack and still
  report first-class product readiness separately from raw live tool success.
  The current seeded-graph live baseline is `1 full`, `17 partial`, `2 blocked`;
  SG03 now returns a full routed answer, while SG17 and SG20 remain the only
  blocked scenarios.
- Maintaining the new playground hardening branch work under
  `playground/src/`, `playground/tests/`, `server/mcp/resource_catalog.py`,
  and `scripts/stakeholder_benchmark_pack.py`, including the Svelte 5/Vite 7
  dependency baseline, strict iframe-bridge token validation, DSAP audit/FOI
  workbench, routing demos for SG03/SG12, benchmark-pack/live-run resources,
  and the new deterministic fixture-backed frontend Playwright acceptance suite
  plus env-gated live smoke coverage that supersede the earlier
  dependency-only PRs `#24` and `#29`. The 2026-03-14 live-smoke follow-up
  fixed the remaining SG03 bridge failure by treating sanitized and original
  tool aliases as equivalent in the preview-session allowlist, so the route
  planner's `os_route.get` call is no longer rejected as `TOOL_NOT_ALLOWED`
  when the live MCP `tools/list` surface only advertises `os_route_get`.
- Clearing the remaining PR `#36` follow-up blockers by keeping the full
  Playwright config port override honest, restoring the devcontainer's system
  CA/custom-cert policy, and replacing parameterized widget asset routes with
  fixed static endpoints that satisfy CodeQL's path-handling rules.
- Clearing the latest PR `#36` review thread on `playground/src/lib/uiBridge.js`
  by deriving `expectedOrigin` from the effective sandbox permission set, and
  mirroring the fixed-asset pattern in the deterministic fixture server so the
  frontend acceptance harness no longer performs request-driven asset path
  joins.
- Clearing the subsequent PR `#36` CSP follow-up by skipping preview CSP
  injection when a widget publishes no `ui.csp` metadata, preserving route and
  map widget fetch behavior unless the resource explicitly declares a CSP.
- Clearing the latest PR `#36` follow-up by preserving preview session tokens
  across catalog refreshes, hardening benchmark live-alias resource loading
  against malformed JSON, and making the analytical-index validator tolerate
  CI shallow clones when the pinned citation commit is not present locally.
- Clearing the remaining PR `#36` Python follow-up by normalizing published UI
  resource HTML to absolute `/ui/shared/*` and `/ui/vendor/*` asset URLs and
  treating non-object benchmark live-alias JSON as structured
  `INVALID_CONFIGURATION` data instead of a 500.
- Clearing the last transport-specific PR `#36` follow-up by splitting UI
  asset-path publication by transport: HTTP resource reads keep absolute
  `/ui/...` asset URLs for browser hosts, while STDIO and embedded widget
  payloads keep resource-local paths so MCP clients without HTTP side channels
  can still load map widget assets.
- Clearing the remaining GitHub Advanced Security PR `#36` review noise by
  changing `/ui` static asset delivery to an internal allowlist in
  `server/mcp/resources.py` and sanitizing deterministic fixture-server JSON
  responses to drop stack-like fields before serialization.
- Clearing the remaining PR `#36` frontend timeout by stabilizing the routing
  full-suite selectors in `playground/tests/support/full_playground.js` and
  `playground/tests/full/routing_full.spec.js`, so the SG03/SG12 seeded demos
  are selected only after the routing workbench renders its list items.
- Clearing the last actionable PR `#36` review thread by extending the iframe
  bridge preview-session allowlist to accept `resources/read` requests by
  resource name as well as URI, matching the MCP contract returned by
  `resources/list`.
- Capturing the durable PR `#36` lessons in `AGENTS.md`: bridge allowlists
  must treat `resources/read` names and URIs as equivalent valid shapes,
  deterministic frontend Playwright fixes should be rerun through the exact CI
  entrypoint with an override port to catch hard-coded assumptions, routing/UI
  full-suite specs should wait for stable rendered state before selecting
  controls, and GitHub Advanced Security discussion markers cannot be resolved
  through the normal review-thread API.
- Clearing the newest PR `#36` `frontend` failure by making `connect()` keep
  the playground in `connecting` state until the descriptor, benchmark, and
  audit bootstrap loads complete, and by removing the end-of-connect tab reset
  that could switch Benchmarks or Routing back to Explorer while the full
  Playwright suite was waiting on seeded demo content.
- Validating preservation of the original Explorer resource flows by adding
  `playground/tests/full/explorer_resources_full.spec.js`, which iterates over
  every baseline fixture resource, confirms each one remains selectable from
  the hardened Explorer list, verifies every MCP-App resource still opens in
  the host preview, and keeps data resources visible through the detail pane.
- Rolling out the Map Lab novice-learning and selector-based collection/export
  workflow on the compatibility-locked boundary explorer entrypoint.
- Hardening storage isolation so mutable database/cache/log state is decoupled
  from git worktrees (named-volume PostGIS + runtime data roots).
- Standardizing local Docker PostGIS on the repo-owned named volume
  `mcp-geo-postgis`; the March 10, 2026 cleanup consolidated the seed boundary
  cache rows from `mcpgeo_cache_local_data` into that canonical volume and left
  the legacy bind-mounted `data/postgres/pgdata` cluster non-canonical because
  it is storage-corrupted (`invalid checkpoint record`).
- Standardizing devcontainer/host PostGIS on a pgRouting-capable image and
  automatic boundary-cache/route-schema bootstrap so local route planning
  defaults no longer depend on a plain PostGIS sidecar missing `pgrouting` or
  an external pgRouting image tag; the repo now builds
  `.devcontainer/postgis.Dockerfile` as the canonical sidecar image, though the
  upstream `postgis/postgis:16-3.4` base is still amd64-only.
- Standardizing Claude Desktop on the same PostGIS instance as the repo
  devcontainer when it is already running, with Docker-sidecar fallback only
  when the devcontainer database is absent.
- Standardizing benchmark startup on a single shared PostGIS cache across
  clients, with `scripts/check_shared_benchmark_cache.sh` as the required
  preflight before Codex-vs-Claude or stakeholder live comparison runs.
- Keeping route-graph bootstrap/provenance tooling free of raw credential
  storage/logging by sanitizing MRN download metadata and redacting DSN-derived
  secrets in `scripts/route_graph_pipeline.py`.
- Standardizing host-side verification commands on repo-local wrappers
  (`scripts/pytest-local`, `scripts/ruff-local`, `scripts/mypy-local`) so
  Codex/CLI sessions reuse the running devcontainer toolchain before falling
  back to `.venv` or `uv run`.
- Converting Codex execution evidence into stakeholder-facing usage examples
  from session telemetry and git/PR history.

## Active Work

- Maintain and iterate the OWASP MCP strict validation pack (`server/owasp_mcp_validation.py`, `security/owasp_mcp/`, `.github/workflows/ci.yml`) from the current `compliant` strict baseline, keeping the attestation set fresh and preserving the hardened `/mcp` auth, session, deployment, and governance controls.
- Prepare the minor-release integration branch `codex/release-0.6.0-integration`
  by landing `codex/validate-maps` plus the boundary harness follow-up while
  explicitly deferring PRs `#24`, `#29`, and `codex/reporting-2026-03-01`.
- Maintain the additive DSAP implementation under `server/audit/`, including
  pack assembly, integrity verification, disclosure derivatives, retention
  state, pack discovery, bundle sidecar hashing, and the audit API surface,
  while preserving the current trace/session capture stack.
- Maintain published `v0.5.0` launch state (release notes/caveat visibility,
  security-review traceability, and public-repo hygiene checks).
- Maintain the Codex-vs-Claude host benchmark harness: `scripts/codex-mcp-local`,
  `scripts/mcp-docker-local`, `scripts/host_benchmark.py`,
  `docs/benchmarking/codex_vs_claude_host_benchmark.md`, and the
  host-simulation profiles (`codex_cli_stdio`, `codex_ide_ui`,
  `claude_desktop_ui_partial`).
- Capture benchmark evidence runs for Codex CLI, Codex IDE, and Claude
  Desktop using the new scenario pack
  `docs/benchmarking/codex_vs_claude_host_scenarios_v1.json` and generate
  side-by-side reports under `docs/reports/`.
- Maintain the stakeholder benchmark generator, fixture pack, scored reference
  outputs, and workflow-validation report under
  `scripts/stakeholder_benchmark_pack.py`,
  `data/benchmarking/stakeholder_eval/`,
  `docs/reports/MCP-Geo_evaluation_questions.md`, and
  `docs/reports/mcp_geo_stakeholder_benchmark_workflow_2026-03-10.md`,
  including the 10 additional Phase 1-derived scenarios shipped via
  `scripts/stakeholder_phase1_extension.py`.
- Maintain the stakeholder benchmark gap-analysis note under
  `docs/reports/mcp_geo_stakeholder_gap_analysis_2026-03-09.md`, including the
  runtime finding that `OS_API_KEY` was not visible to the benchmark-generation
  process in the Codex workspace and the scenario-by-scenario capability gaps
  that still explain why only 1 of the 20 live rerun scenarios is first-class
  ready.
- Maintain the stakeholder live-rerun harness and report under
  `scripts/stakeholder_live_run.py`,
  `data/benchmarking/stakeholder_eval/live_run_2026-03-10.json`, and
  `docs/reports/mcp_geo_stakeholder_live_run_2026-03-10.md`, including the
  stricter `firstClassProductReady` interpretation for live OS-backed runs, the
  seeded route-graph preflight from `scripts/seed_benchmark_route_graph.py`,
  and the updated SG03 full-pass evidence.
- Maintain the playground hardening and demo workbench implementation on
  `codex/playground-hardening-demo-workbench`, including the consolidated
  Dependabot remediation in `playground/package.json` / `package-lock.json`,
  the new benchmark resource aliases in `server/mcp/resource_catalog.py`,
  regenerated benchmark pack demo metadata under
  `data/benchmarking/stakeholder_eval/`, the refactored Svelte workbench shell,
  the fixture-backed full UI acceptance suite under `playground/tests/full/`,
  the live smoke suite under `playground/tests/live/`, and the updated
  frontend CI + manual live-smoke workflow support in `.github/workflows/ci.yml`.
- Maintain and monitor the completed layered-map reliability workstreams
  (`LMR-BASE-0`, `LMR-ALL-1`, `LMR-INT-2`, `LMR-FBK-3`, `LMR-GATE-5`) and keep
  the remaining external host-runtime blocker
  (`LMR-HOST-4`) visible.
- Maintain Claude tool-discovery interoperability hardening where some clients
  send search-style params via `tools/list`; keep filtered `tools/list` behavior
  and troubleshooting evidence synchronized with MCP standard references.
- Keep Docker-backed Claude runs aligned with host/devcontainer defaults by
  forwarding toolset/content env controls in `scripts/claude-mcp-local` so
  startup `tools/list` remains scoped (`starter` + include toolsets) when
  configured.
- Maintain compact startup-catalog behavior for Claude in
  `server/stdio_adapter.py` (`MCP_STDIO_LIST_COMPACT`) to reduce startup
  context pressure while retaining callable tool metadata.
- Maintain `nomis.query` compatibility normalization and actionable query-error
  guidance in `tools/nomis_data.py` so model-generated payload drift (`date`,
  `cell`, missing dimensions, unknown dimension keys) yields deterministic
  correction hints and auto-retry adjustments instead of opaque upstream
  failures.
- Maintain tool-search category alias resilience (`stats` -> `statistics`) in
  `server/mcp/tool_search.py` / `os_mcp.descriptor` for constrained client
  discovery flows.
- Maintain Docker wrapper secret-hydration order in
  `scripts/claude-mcp-local` (env -> `*_FILE` -> macOS `launchctl` -> `.env`)
  and direct server fallback in `server/config.py` (`OS_API_KEY_FILE`) so
  rotated OS credentials are picked up without embedding secrets in MCP client
  config.
- Track post-program stabilization and backlog sequencing in `PROGRESS.MD`.
- Coordinate parallel OS gap workstreams and integration gates from
  `docs/reports/os_catalog_gap_implementation_plan_2026-02-13.md`.
- Documentation pack and preparation for workshop/demo, now delivered as
  `docs/public_sector_ai_community/` with linked markdown and Prism outputs.
- Maintain the analytical-index publication workflow under
  `scripts/generate_mcp_geo_analytical_index.py`,
  `data/report_inputs/mcp_geo_analytical_index_manifest.json`, and
  `docs/mcp_geo_prism_bundle/`, including the appendix replacement slice and
  pinned-commit citation policy for the AI Community materials.
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
- Maintain peat-survey failure-chain hardening in `tools/os_features.py`
  (`resultType=hits` count correctness, legacy transport collection aliasing,
  and unsupported-collection suggestion payloads) with synchronized evidence in
  `troubleshooting/peat-survey-failure-deep-analysis-2026-03-03.md`.
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
- Maintain the Codex long-horizon reporting skill/tooling and refresh summary
  artifacts under `scripts/codex_long_horizon_summary.py`,
  `skills/mcp-geo-long-horizon-summary/`, and `docs/reports/`.
- Maintain the repo extent/complexity analysis skill and report pipeline under
  `scripts/repo_extent_complexity_report.py`,
  `skills/mcp-geo-repo-extent-complexity/`, and `docs/reports/`.
- Maintain the detailed OS map runbook skill under
  `skills/mcp-geo-detailed-os-maps/` so report-style map work defaults to
  MapLibre + OS vector basemaps with label-safe overlays and browser validation.
- Drive the `codex/simple-map` exploration stream (`SMAP-*`) for minimal auth
  handling and PMTiles performance-trial setup artifacts (`ui/simple_map.html`,
  `docs/simple_map_lab.md`, `tests/test_maps_proxy.py`).
- Keep MCP specification coverage complete in local vendor submodules,
  including the draft auth extension repository
  (`docs/vendor/mcp/repos/ext-auth`).
- Maintain the MCP-Apps compact-window review and redesign handoff artifacts in
  `docs/reports/mcp_apps_window_constraints_review_2026-03-01.md` and
  `docs/design/figma/`.
- Maintain the Figma MCP setup/capture runbook for repeatable onboarding and
  troubleshooting at
  `docs/design/figma/mcp_figma_setup_and_capture_runbook.md`.
- Maintain compact-window implementation and test hardening artifacts from
  `docs/reports/compact_windows_unattended_implementation_and_test_plan_2026-03-01.md`
  with strict acceptance evidence from the unattended Playwright suites.
- Maintain the Teignmouth peninsula south-of-railway building-profile briefing
  and operational AOI polygon in
  `docs/reports/teignmouth_peninsula_building_profile_brief_2026-03-06.md`.
- Maintain the repeatable MCP-Geo functionality showcase report workflow under
  `scripts/generate_mcp_geo_functionality_showcase.py`,
  `data/report_inputs/mcp_geo_functionality_showcase_examples.json`,
  `docs/reports/mcp_geo_functionality_showcase_2026-03-07.{md,docx,pdf}`,
  and the supporting Stanley House case note
  `docs/reports/stanley_house_clampet_lane_context_case_2026-03-07.md`.
- Maintain the Teignmouth wheelchair access map generator, live JSON export,
  and slide-format report artifacts in
  `scripts/generate_teignmouth_wheelchair_access_map.py`,
  `data/exports/teignmouth_wheelchair_access_map_2026-03-07.json`, and
  `docs/reports/teignmouth_wheelchair_access_map_2026-03-07.{html,md}` with
  responsive slide-fit layout, Web Mercator overlay alignment, perimeter
  corridor callouts, hover evidence titles, sidebar-only access-point markers
  for Teignmouth station and Shopmobility, and an optional browser-side
  `OS Detailed` vector basemap toggle with slimmer route overlays for label-safe
  context plus wheel zoom, drag pan, reset controls, zoom-aware scale-bar
  updates, browser-side MapLibre sync for sharper street and building context
  at higher zoom levels, and a `--reuse-export` regeneration path for
  presentation-only refreshes when no live OS key is available.
- Maintain the Exmouth comparator outputs and side-by-side accessibility note in
  `data/exports/exmouth_wheelchair_access_map_2026-03-07.json`,
  `docs/reports/exmouth_wheelchair_access_map_2026-03-07.{html,md}`,
  `output/playwright/exmouth-wheelchair-access-map-2026-03-07.png`, and
  `docs/reports/teignmouth_exmouth_sidmouth_access_comparison_2026-03-07.md`,
  keeping the same optional `OS Detailed` browser vector basemap control
  available across all comparator maps.
- Maintain the Sidmouth comparator outputs in
  `data/exports/sidmouth_wheelchair_access_map_2026-03-07.json`,
  `docs/reports/sidmouth_wheelchair_access_map_2026-03-07.{html,md}`, and
  `output/playwright/sidmouth-wheelchair-access-map-2026-03-07.png`.
- Refine playground + geography-selector compact UX for map-first workflows:
  compact-preserving maximize behavior, adjustable split-pane sizing, a
  compact tab workflow (`Map/Search/Results/Info/Debug/Help`), and
  non-obstructive zoom-ladder controls.
- Maintain the Codex usage-example portfolio and refresh evidence artifacts in
  `docs/codex_usage_examples.md` plus
  `docs/reports/mcp_geo_codex_long_horizon_summary_*.{md,json,svg}`.

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
- Done: peat-survey failure-chain remediation (`PSF-*`) for `os_features.query`
  count semantics in `hits` mode, legacy `trn-fts-roadlink-*` compatibility
  aliasing to `trn-ntwk-roadlink-*`, and actionable unsupported-collection
  suggestions; coverage and evidence tracked in
  `tests/test_os_features_collections.py` and
  `troubleshooting/peat-survey-trace-evidence-2026-03-03.md`.
- Done: strict non-runtime static quality gate restoration for reliability
  surfaces via `scripts/check_non_runtime_quality.sh`
  (`ruff` + `mypy --follow-imports=skip`).
- Done: dual-derivation ONS geography cache baseline (`ONSPD` + `ONSUD` exact,
  `NSPL` + `NSUL` best_fit) with tooling (`ons_geo.*`), refresh automation,
  route-query integration, and focused regression coverage.
- Done: devcontainer cold-start bootstrap now auto-creates boundary-cache
  PostGIS tables and auto-seeds `ons_geo` cache from bundled bootstrap CSVs in
  `scripts/devcontainer_post_start.sh`, reducing first-run Map Lab degraded
  status on fresh named volumes.
- Done: added Long Horizon-style Codex session reporting for `mcp-geo` via
  `scripts/codex_long_horizon_summary.py`, a dedicated skill runbook
  (`skills/mcp-geo-long-horizon-summary/SKILL.md`), and baseline report
  artifacts for 2026-02-25 (`docs/reports/mcp_geo_codex_long_horizon_summary_2026-02-25.{md,json}`),
  now extended with deterministic summary-card SVG generation
  (`skills/mcp-geo-long-horizon-summary/templates/summary_card.svg.tmpl`)
  and image-first markdown output.
- Done: refreshed Codex long-horizon metrics on 2026-03-04
  (`docs/reports/mcp_geo_codex_long_horizon_summary_2026-03-04.{md,json,svg}`)
  and integrated updated usage evidence into the new UK Public Sector AI
  Community documentation set.
- Done: public-release security review for `v0.5.0` recorded in
  `docs/reports/public_release_security_review_2026-03-04.md`; no live
  credential material identified (history detections were redacted placeholders).
- Done: added repo extent/complexity analysis skill for `mcp-geo` via
  `scripts/repo_extent_complexity_report.py` and
  `skills/mcp-geo-repo-extent-complexity/`, with dual-scope reporting
  (`git_tracked`, `workspace`), generated-output exclusion policy, Python
  cyclomatic complexity, churn-weighted hotspots, baseline artifacts in
  `docs/reports/repo_extent_complexity_2026-02-25.{md,json}`, and a
  manager-facing report card snapshot in
  `docs/reports/repo_extent_complexity_report_card_2026-02-25.md`.
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

- Latest OWASP MCP strict validator run: `./scripts/validate-owasp-mcp-local` on 2026-03-13 (`compliant`, score `100.0`, `0` required/minimum-bar failures, empty remediation backlog, baseline outputs committed under `security/owasp_mcp/baseline/`).
- Latest strict test run: `./scripts/pytest-local -q -m "not integration"` on 2026-03-13
  (`1126 passed`, `6 skipped`, `1 deselected`, coverage `90.00%`, gate passed).
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

- 2026-03-13: Added and remediated the repo-pinned OWASP MCP validation pack (`security/owasp_mcp/`, `server/owasp_mcp_validation.py`, `scripts/validate_owasp_mcp_server.py`) locked to OWASP GenAI Security Project _A Practical Guide for Secure MCP Server Development_ Version 1.0 (February 2026). The strict baseline now scores `100.0` and is `compliant`, backed by committed attestations, hardened `/mcp` auth/session controls, deployment assets, monitoring assets, and protected-branch review evidence.
- 2026-03-10: Standardized cross-platform repo/devcontainer behavior by
  enforcing LF line endings via `.gitattributes`/`.editorconfig`, making
  devcontainer `ngrok` installation opt-in, and routing devcontainer/Docker
  TLS trust through the system CA bundle plus local `.devcontainer/certs/`
  injection so Windows checkouts and corporate proxy environments no longer
  require application-code changes.
- 2026-03-14: Re-aligned the devcontainer implementation with that cross-platform
  contract after a local simplification drifted away from it. The supported
  setup again keeps proxy values build-scoped in `.devcontainer/Dockerfile`,
  trusts corporate/local roots via `.devcontainer/certs/*.crt` plus the system
  CA bundle, and sources container-wide runtime env from
  `.devcontainer/docker-compose.yml` rather than `devcontainer.json` for the
  Docker Compose-based workspace. A same-day PR follow-up also restores the
  pre-APT `update-ca-certificates` step in `.devcontainer/Dockerfile`, so
  custom corporate roots are live before the first package index fetch.
- 2026-03-04: Completed public-release `v0.5.0` publication: formal repository
  security review (`docs/reports/public_release_security_review_2026-03-04.md`),
  release notes (`RELEASE_NOTES/0.5.0.md`), version bump
  (`pyproject.toml`, `server/__init__.py`), public-launch caveat statement in
  `README.md`, pushed tag/release (`https://github.com/chris-page-gov/mcp-geo/releases/tag/v0.5.0`),
  and repository visibility transition to `PUBLIC`.
- 2026-03-04: Published an end-to-end UK Public Sector AI Community
  documentation package under `docs/public_sector_ai_community/`, including
  novice/apprentice markdown chapters, detailed internal/external timeline,
  evaluation chapter, evidence index, and Prism-ready LaTeX publication set
  (`prism/main.tex` + bibliography + section files). Linked the package from
  `README.md` and synchronized trackers (`PROGRESS.MD`, `CHANGELOG.md`).
- 2026-02-28: Hardened devcontainer/VS Code stdio dependency bootstrap after
  repeated `ModuleNotFoundError: loguru` startup failures by installing core
  runtime before optional extras and adding launcher-level best-effort
  `pip install -e .` fallback in `scripts/vscode_mcp_stdio.py` and
  `scripts/os_mcp.py`.
- 2026-02-28: Mitigated devcontainer interpreter `ENOENT` failures caused by
  host-created workspace `.venv` paths by defaulting container VS Code Python
  to `/usr/bin/python3` and making `scripts/vscode_mcp_stdio.py` treat
  unspawnable interpreter paths as unavailable.
- 2026-02-28: Switched devcontainer and local Claude wrapper defaults away from
  repo bind-mounted PostGIS data toward Docker named volumes, added runtime-data
  volume-backed cache/log paths, and documented host env strategy (separate
  secrets file sourced from shell startup remains recommended practice).
- 2026-02-28: Hardened Map Lab readability/runtime diagnostics in
  `ui/boundary_explorer.html` by defaulting boundary fills off, adding explicit
  opacity controls, introducing a dynamic Guidance & Status panel, surfacing
  cache readiness via `admin_lookup.get_cache_status` +
  `ons_geo.cache_status`, and adding boundary-interaction hit layers so
  selection works even when fills are hidden. Added focused Playwright coverage
  in `playground/tests/boundary_explorer_controls.spec.js` plus exhaustive
  option-matrix screenshot/summary coverage in
  `playground/tests/boundary_explorer_option_matrix.spec.js`.
- 2026-02-28: Completed Map Lab implementation on the existing
  `ui://mcp-geo/boundary-explorer` entrypoint: added Help/Map/Collections tabs,
  detailed tutorial content with persisted help state, selector-based local
  collections, async selector-driven `os_map.export` + `os_map.get_export`,
  and ONS UPRN reverse-lookup cache indexing for OA/LSOA/MSOA/LAD/postcode
  export resolution.
- 2026-02-27: Started `codex/simple-map` exploration to validate a minimal map
  delivery path with browser bearer auth preferred for OS vector proxy calls
  and deterministic fallback to key header/query or server `OS_API_KEY`; added
  `ui://mcp-geo/simple-map-lab` + `docs/simple_map_lab.md` to support OS
  vector vs PMTiles comparative trials.
- 2026-02-27: Resolved a simple-map "tile checks pass but map never idles"
  failure mode by aligning MapLibre runtime/worker versions and disabling cache
  for `/ui/simple-map-lab` (`Cache-Control: no-store, max-age=0`) so browser
  sessions do not retain stale lab HTML during auth/debug iterations.
- 2026-02-27: Updated simple-map style selection UX from free-text to curated
  OS style dropdown (OS + OS Open presets) and added novice-focused style
  guidance in UI/docs to reduce setup ambiguity for first-time users.
- 2026-02-27: Fixed simple-map style switching behavior by handling
  `/maps/vector/vts/resources/styles` as a style endpoint (honoring the
  `style=` query selection) and correcting rewritten vector tile templates to
  `{z}/{y}/{x}` ordering.
- 2026-02-25: Extended the repo extent/complexity workflow with a
  non-technical manager report card output. The analyzer now emits a
  plain-English `manager_report_card` model (terminology explanations, metric
  basis/source notes, practical implications, and hotspot attention list), and
  `--manager-output` writes a dedicated markdown snapshot consumed by the skill
  runner.
- 2026-02-25: Added a source-backed repo extent/complexity analysis workflow
  (`skills/mcp-geo-repo-extent-complexity`) with deterministic analyzer script
  `scripts/repo_extent_complexity_report.py`. The model reports dual scopes
  (`git_tracked`, `workspace`), excludes known generated/output surfaces by
  default (including vendor/report/cache paths), computes Python cyclomatic
  complexity, and ranks hotspots using `complexity x churn`.
- 2026-02-25: Extended the Codex long-horizon reporting workflow with a
  deterministic text-template visual card generator. The new template
  (`skills/mcp-geo-long-horizon-summary/templates/summary_card.svg.tmpl`)
  produces a report header image titled `Codex MCP-Geo Summary`, and
  generated markdown now opens with that summary image when
  `--summary-svg-output` is provided.
- 2026-02-25: Added a standardized Long Horizon-style Codex session summary
  workflow for `mcp-geo`, implemented as `scripts/codex_long_horizon_summary.py`
  plus the reusable skill `skills/mcp-geo-long-horizon-summary/`. The report
  contract now tracks active runtime, wall-clock span, token usage, cached
  input reuse, tool calls, patch volume, peak step tokens, and context
  compactions, with baseline outputs captured under `docs/reports/`.
- 2026-02-23: Completed boundary variant full-coverage hardening for strict
  resolve gates. `scripts/boundary_pipeline.py` now applies manifest default
  variant policy (equivalence + derivation + overrides) across families,
  records explicit accuracy classes for equivalent/derived variants (including
  coarser-source warnings), and enforces full-availability policy in evaluator
  checks. Hardened run `data/boundary_runs/20260223T120022Z/run_report.json`
  reports `COMPLETE_BOUNDARIES_RESOLVED_AND_VERIFIED` with `resolved=112`,
  `derived=44`, `not_published=0`, `errors=0`.
- 2026-02-23: Hardened boundary-source verification to remove ambiguity
  between resolve and ingest stages. `scripts/boundary_pipeline.py` now
  supports `--verify-resolved` with live URL probing, mode-aware pass/fail
  statuses, and stronger CKAN package ranking by query-title token match. The
  latest full resolve+verify run
  (`data/boundary_runs/20260223T082527Z/run_report.json`) now reports
  `COMPLETE_BOUNDARIES_RESOLVED_AND_VERIFIED` with `107` resolved source URLs
  verified reachable and `49` variants explicitly `not_published` with
  evidence.
- 2026-02-22: Added explicit degraded-performance status signaling for cache
  availability surfaces so clients can detect reduced reliability without
  inferring from missing data: `ons_geo.cache_status`,
  `admin_lookup.get_cache_status`, and
  `resource://mcp-geo/boundary-cache-status` now expose
  `performance.degraded` with reason/impact fields.
- 2026-02-22: Populated all caches feasible in the current local environment:
  refreshed code-list pack cache artifacts, ingested bootstrap ONS geo products
  (ONSPD/NSPL/ONSUD/NSUL) into `data/cache/ons_geo`, and seeded PostGIS
  boundary cache with live ArcGIS geometry for Coventry and Westminster.
  Remaining full-population steps require production source downloads/tooling.
- 2026-02-22: Re-validated startup context pressure for non-deferred clients
  (Claude-style) and hardened mitigation path by adding
  `os_mcp.select_toolsets` to the `starter` toolset; updated tutorial and
  troubleshooting guidance with measured `tools/list` footprint and scoped
  expansion workflow.
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
- 2026-02-23: Updated MCP-Apps fullscreen controls to keep a usable `Try maximise`
  path when hosts do not advertise `availableDisplayModes`, instead of
  disabling the control outright.
- 2026-02-23: Updated boundary explorer OS/inventory diagnostics to distinguish
  `NO_API_KEY`, auth failures, missing proxy, and toolset exposure issues
  (`MISSING_TOOL`) so host/toolset failures are not mislabeled as key issues.
- 2026-02-23: Updated workspace VSCode MCP defaults to include
  `features_layers` alongside `starter`, restoring `os_map.inventory` and
  `os_map.export` availability for boundary explorer workflows.
- 2026-02-23: Added a deterministic Playwright host harness for boundary
  explorer (`playground/tests/boundary_explorer_host_harness.spec.js`) and a
  read-only runtime snapshot probe
  (`window.__MCP_GEO_BOUNDARY_EXPLORER__.getSnapshot()`) to validate boundary
  overlay rendering independently of VSCode host-runtime quirks.
- 2026-02-23: Added host-aware fullscreen controls to the interactive MCP-Apps
  widgets (`boundary_explorer`, `geography_selector`, `statistics_dashboard`)
  using `ui/request-display-mode` with graceful fallback behavior when hosts do
  not expose fullscreen in `availableDisplayModes`.
- 2026-02-23: Updated workspace VSCode MCP config (`.vscode/mcp.json`) to read
  `OS_API_KEY` from `${env:OS_API_KEY}` (allowing deterministic startup via
  environment or `.env`) after observing duplicate prompt/timing failures with
  prompt-driven key injection.
- 2026-02-23: Updated `os_map.inventory` and `os_map.export` `layers` input
  schema definitions from `anyOf` to explicit union `type` + `items` after a
  VSCode/Copilot MCP tool-registration failure (`array schema missing items`)
  against `mcp_mcp-geo-http_os_map_inventory`.
- 2026-02-23: Addressed PR #15 review findings by tightening `os_map` `layers`
  schemas to explicit `oneOf` branches (array/string/null), replacing
  `innerHTML` in boundary explorer OS warnings with DOM-node composition,
  adding guaranteed response close in
  `scripts/boundary_pipeline.py::_probe_source_url`, and surfacing unreadable
  ONS geo cache lookup failures as `503 CACHE_READ_ERROR` instead of false
  `404 NOT_FOUND`.
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
- 2026-03-13: Follow-up PR hardening now gates stdio `resource_link` handoff blocks on negotiated UI capability support and requires offline-pack catalog URI matches consistently for both `resources/read` payloads and `/resources/download` resolution.
- 2026-03-14: Fixed the remaining MCP-Apps text-mode follow-up by making `tools/os_apps.py` set `uiTextOnlyOverride` from the resolved content mode rather than only explicit payload overrides, so env-driven `MCP_APPS_CONTENT_MODE=text` no longer lets raw HTTP or stdio handoff decoration re-append `resource_link` blocks. Audited the current UI tool surface and confirmed all `os_apps.render_*` responses share `_build_widget_response()`, so this fix covers the present MCP-Apps widget implementations in one place.
- 2026-03-14: Standardized the repo fix workflow in `AGENTS.md`: bug fixes and
  PR-comment fixes now require a same-pattern codebase scan, patching all
  confirmed sibling cases in the same change and adding regressions for both
  the reported path and an equivalent sibling when one exists.
- 2026-03-14: Addressed the latest PR #39 `os_resources.get` validation review
  finding by adding strict integer guards that reject JSON booleans for integer
  request fields. Applied the same-pattern sweep across sibling public parsers:
  resource chunking, paginated OS/ONS/admin search/download handlers,
  `os_mcp.select_toolsets.maxTools`, HTTP/stdio tool-search limits, and
  MCP-Apps widget numeric inputs. The remaining raw review threads for HTTP
  auth metrics and offline-pack discovery were rechecked and are already
  satisfied by the current branch code plus regression coverage.
- 2026-02-10: Added `scripts/vscode_mcp_stdio.py` and updated `.vscode/mcp.json` to use it so VS Code can start stdio servers on macOS without requiring global Python deps (it prefers the repo venv at `.venv/`).
- 2026-02-10: Added `scripts/vscode_trace_snapshot.py` to convert VS Code trace artifacts into a `logs/sessions/` directory that can be summarized by `scripts/trace_report.py`.
- 2026-03-13: Tightened `resolve_offline_pack_download` to require exact catalog URI matches only (removed basename fallback) so `/resources/download` no longer accepts alternate user-supplied URI path variants for trusted files.

## Open Questions

- Should we formally deprecate dotted tool names and standardize on sanitized names across HTTP + STDIO (and how do we surface `originalName` mappings consistently)?
- Does Claude Desktop actually render MCP-Apps UI from `_meta.ui.resourceUri` or `uiResourceUris` without `resource_link`, or is it currently ignoring MCP-Apps UI entirely?

## Run and Test Notes

- `uvicorn server.main:app --reload`
- `pytest -q`
