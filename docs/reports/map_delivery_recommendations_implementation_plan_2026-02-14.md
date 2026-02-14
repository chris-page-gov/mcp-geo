# Map Delivery Recommendations Implementation Plan (2026-02-14)

## Objective

Translate the recommendations in
`/Users/crpage/repos/mcp-geo/research/map_delivery_research_2026-02/06_recommendations_and_report.md`
into a tracked, dependency-aware implementation program for MCP Geo.

## Scope and constraints

- Scope: planning and tracking only in this branch.
- Constraint: no feature implementation as part of this plan branch.
- Tracking sources of truth: `CONTEXT.md`, `PROGRESS.MD`, `CHANGELOG.md`.

## Completion criteria

1. Recommendation items are mapped to explicit workstreams with dependencies.
2. Every workstream has clear acceptance and verification criteria.
3. Progress tracking is present in repo-standard docs.
4. Ecosystem requests to OS/community are captured as external-facing deliverables.

## Program board

Legend: pending, in_progress, done

| ID | Phase | Status | Dependencies | Primary outcome |
| --- | --- | --- | --- | --- |
| MDR-I1 | Immediate | pending | none | `os_maps.render` is documented as the canonical compatibility baseline. |
| MDR-I2 | Immediate | pending | MDR-I1 | Fallback skeleton payloads are standardized (`map_card`, `overlay_bundle`, `export_handoff`). |
| MDR-I3 | Immediate | pending | MDR-I1 | Lean startup discovery (`starter`) is default in docs and client setup examples. |
| MDR-I4 | Immediate | pending | MDR-I1 | Browser/widget support matrix is published and linked from setup docs. |
| MDR-N1 | Near-term | pending | MDR-I2, MDR-I4 | Deterministic host-simulation utilities exist for UI resource tests across engines. |
| MDR-N2 | Near-term | pending | MDR-I2 | Tool payloads expose explicit widget-unsupported guidance fields. |
| MDR-N3 | Near-term | pending | MDR-N1 | Trial suite includes mobile viewport projects and latency-budget assertions. |
| MDR-N4 | Near-term | pending | MDR-I2 | Optional PostGIS/vector-tile sidecar deployment profile is documented and tested. |
| MDR-M1 | Medium-term | pending | MDR-N4 | PMTiles/MBTiles delivery option is available for offline-friendly deployments. |
| MDR-M2 | Medium-term | pending | MDR-N3 | Map output quality checks cover label density, contrast, and accessibility metadata. |
| MDR-M3 | Medium-term | pending | MDR-N3 | Notebook-generated scenario packs are integrated into resource outputs. |
| MDR-E1 | Ecosystem | pending | MDR-I4 | Client-side best-practice bundle for MCP/AI-hosted map embedding is published. |
| MDR-E2 | Ecosystem | pending | MDR-E1 | Lightweight style profiles for constrained AI embedding contexts are published. |
| MDR-E3 | Ecosystem | pending | MDR-E1, MDR-E2 | Official examples show progressive fallback from full vector map to static card. |
| MDR-E4 | Ecosystem | pending | MDR-E1 | Mixed UI/no-UI host guidance is documented with deterministic degradation paths. |

## Detailed workstreams

### MDR-I1: Canonical `os_maps.render` baseline

Dependencies: none

Scope:
- Normalize docs/tutorials to lead with `os_maps.render` compatibility-first flow.
- Ensure the first map example in setup docs succeeds without UI widgets.
- Align wording across README, getting-started, and examples.

Deliverables:
- `/Users/crpage/repos/mcp-geo/README.md`
- `/Users/crpage/repos/mcp-geo/docs/getting_started.md`
- `/Users/crpage/repos/mcp-geo/docs/examples.md`
- `/Users/crpage/repos/mcp-geo/docs/tutorial.md`

Acceptance:
- `os_maps.render` appears as the first recommended map path in core docs.
- Documentation language is consistent on layered fallback ordering.

Verification:
- Doc-link sanity pass.
- Manual walkthrough from docs reaches a valid static map contract output.

### MDR-I2: Standardized fallback skeleton payloads

Dependencies: MDR-I1

Scope:
- Define contract schemas for `map_card`, `overlay_bundle`, and `export_handoff`.
- Document required and optional keys, error semantics, and compatibility notes.
- Add conformance checklist for tool authors.

Deliverables:
- `/Users/crpage/repos/mcp-geo/docs/spec_package/06_api_contracts.md`
- `/Users/crpage/repos/mcp-geo/docs/mcp_apps_alignment.md`
- `/Users/crpage/repos/mcp-geo/docs/tool_catalog.md`
- New contract reference appendix under `docs/spec_package/`.

Acceptance:
- All three skeleton payloads have stable documented schemas.
- Compatibility guidance includes no-UI, partial-UI, and full-UI hosts.

Verification:
- Contract examples validate against schema snippets.
- Review pass confirms no conflicting payload definitions in docs.

### MDR-I3: Lean default discovery for initialization

Dependencies: MDR-I1

Scope:
- Keep startup discovery guidance anchored on `starter` toolset.
- Defer heavy discovery to explicit post-init selection flows.
- Add host-specific onboarding snippets for lean startup behavior.

Deliverables:
- `/Users/crpage/repos/mcp-geo/docs/ChatGPT_setup_chat.md`
- `/Users/crpage/repos/mcp-geo/docs/troubleshooting.md`
- `/Users/crpage/repos/mcp-geo/docs/examples.md`

Acceptance:
- Startup examples use `starter` or explicit narrow filters.
- Heavy discovery is documented as an opt-in step.

Verification:
- Example configs produce reduced tool lists during initialize/discovery.

### MDR-I4: Browser/widget support matrix

Dependencies: MDR-I1

Scope:
- Publish supported/validated behavior matrix by host and browser engine.
- Include rendering mode availability: static contract, overlays, widgets, fallback.
- Add known limitations and required toggles/env flags.

Deliverables:
- New matrix doc in `/Users/crpage/repos/mcp-geo/docs/`.
- Links from README, getting-started, troubleshooting, and research report index.

Acceptance:
- Matrix includes tested engines and explicit unsupported/unknown states.
- Every matrix row includes verification date and evidence pointer.

Verification:
- Matrix entries map to reproducible trial artifacts under
  `research/map_delivery_research_2026-02/evidence/`.

### MDR-N1: Deterministic host simulation utilities

Dependencies: MDR-I2, MDR-I4

Scope:
- Add deterministic host simulation wrappers for UI resource tests.
- Ensure stable simulation for Chromium, Firefox, and WebKit paths.
- Add fixtures for capability permutations (UI supported vs unsupported).

Deliverables:
- `/Users/crpage/repos/mcp-geo/playground/trials/`
- `/Users/crpage/repos/mcp-geo/scripts/map_trials/`
- `/Users/crpage/repos/mcp-geo/tests/` host-simulation tests

Acceptance:
- Simulation suite reproduces deterministic outcomes across engines.
- Capability matrix fixtures are reusable by widget and fallback tests.

Verification:
- CI-suitable deterministic replay run with fixed seeds and stable snapshots.

### MDR-N2: Explicit widget-unsupported guidance fields

Dependencies: MDR-I2

Scope:
- Extend response payload guidance with explicit unsupported fields
  for widget-ineligible hosts.
- Document field semantics and client handling order.
- Add regression tests for deterministic guidance output.

Deliverables:
- `/Users/crpage/repos/mcp-geo/tools/os_apps.py`
- `/Users/crpage/repos/mcp-geo/server/mcp/client_capabilities.py`
- `/Users/crpage/repos/mcp-geo/tests/` widget-fallback tests
- Updated contract docs from MDR-I2

Acceptance:
- Non-UI hosts receive explicit guidance fields, not implicit assumptions.
- Guidance fields remain stable across STDIO and HTTP transports.

Verification:
- Branch tests assert exact guidance keys and fallback behavior.

### MDR-N3: Mobile viewport and latency budgets

Dependencies: MDR-N1

Scope:
- Add mobile viewport projects to Playwright trials.
- Define latency budgets by scenario type (static render, widget init, overlays).
- Record and trend latency budget compliance in trial outputs.

Deliverables:
- `/Users/crpage/repos/mcp-geo/playground/playwright.trials.config.js`
- `/Users/crpage/repos/mcp-geo/playground/trials/tests/map_delivery_matrix.spec.js`
- `/Users/crpage/repos/mcp-geo/research/map_delivery_research_2026-02/reports/`

Acceptance:
- Mobile projects run in trial harness with explicit pass/fail budgets.
- Reports include latency percentiles and budget compliance summary.

Verification:
- Repeat run (at least two consecutive runs) yields stable budget outcomes.

### MDR-N4: Optional PostGIS/vector-tile sidecar profile

Dependencies: MDR-I2

Scope:
- Define optional sidecar profile (Martin/pg_tileserv) for scaled deployments.
- Document topology, config keys, and security boundaries.
- Provide deployment/runbook guidance and integration tests.

Deliverables:
- `/Users/crpage/repos/mcp-geo/docs/spec_package/03_architecture.md`
- `/Users/crpage/repos/mcp-geo/docs/spec_package/04_system_design.md`
- `/Users/crpage/repos/mcp-geo/docs/spec_package/11_walkthroughs.md`
- Optional deployment assets under `scripts/` or `docs/`.

Acceptance:
- Sidecar profile can be enabled without changing baseline compatibility path.
- Operational guidance includes fallback behavior when sidecar is unavailable.

Verification:
- Smoke-tested sidecar profile runbook with documented evidence.

### MDR-M1: PMTiles/MBTiles offline delivery option

Dependencies: MDR-N4

Scope:
- Add PMTiles/MBTiles option for offline-friendly map delivery.
- Define packaging, versioning, and retrieval contracts.
- Document host constraints and fallback order.

Deliverables:
- Tool/resource additions in `tools/` and `server/mcp/resource_catalog.py`.
- Delivery docs and example workflows.

Acceptance:
- Offline bundle path works without external tile service availability.
- Metadata includes provenance/version and compatibility notes.

Verification:
- Offline integration test path validates map-card + overlay handoff.

### MDR-M2: Map output quality checks

Dependencies: MDR-N3

Scope:
- Define automated checks for label density, contrast, and accessibility metadata.
- Add quality rubric outputs to map trial reporting.
- Set pass/fail thresholds and waiver process.

Deliverables:
- Trial checker scripts under `scripts/map_trials/`.
- Extended report fields under `research/map_delivery_research_2026-02/reports/`.

Acceptance:
- Quality checks run in automated trial pipeline.
- Report clearly flags threshold failures with actionable context.

Verification:
- Test fixtures cover passing, warning, and failing quality cases.

### MDR-M3: Notebook-generated scenario pack outputs

Dependencies: MDR-N3

Scope:
- Convert notebook scenario outputs into resource-backed artifacts.
- Define resource URI naming and metadata schema.
- Publish consumption examples for clients and analysts.

Deliverables:
- Notebook export scripts and `resource://mcp-geo/*` catalog entries.
- Docs for scenario-pack lifecycle and refresh.

Acceptance:
- Scenario packs are reproducible and retrievable via MCP resources.
- Resource metadata includes source notebook, run timestamp, and hash.

Verification:
- End-to-end generation and retrieval test with deterministic fixture data.

### MDR-E1: MCP/AI-hosted client best-practice bundle

Dependencies: MDR-I4

Scope:
- Publish host-safe map embedding patterns (worker/CSP-safe)
  for MCP/AI runtime contexts.
- Provide implementation checklist and minimal templates.

Deliverables:
- New ecosystem guidance doc in `/Users/crpage/repos/mcp-geo/docs/`.

Acceptance:
- Bundle provides concrete patterns for constrained host runtimes.

Verification:
- Guidance validated against at least two host profiles from support matrix.

### MDR-E2: Lightweight style profiles for AI embedding

Dependencies: MDR-E1

Scope:
- Define normalized lightweight style profiles tuned for embedding limits.
- Document profile constraints, intended use, and fallback behavior.

Deliverables:
- Style profile definitions and examples in docs/resources.

Acceptance:
- Profiles are small enough for constrained clients and remain legible.

Verification:
- Snapshot comparison across baseline and lightweight profiles.

### MDR-E3: Progressive fallback official examples

Dependencies: MDR-E1, MDR-E2

Scope:
- Publish examples showing full vector map to static-card degradation path.
- Include deterministic trigger conditions for each fallback step.

Deliverables:
- `/Users/crpage/repos/mcp-geo/docs/examples.md`
- `/Users/crpage/repos/mcp-geo/docs/tutorial.md`

Acceptance:
- Examples cover full UI, partial UI, and no UI hosts end-to-end.

Verification:
- Example output snippets match documented fallback skeleton payloads.

### MDR-E4: Mixed UI/no-UI host guidance

Dependencies: MDR-E1

Scope:
- Publish explicit guidance for mixed fleet deployments where some hosts
  support widgets and others do not.
- Define deterministic degradation contract expectations.

Deliverables:
- Troubleshooting and architecture guidance updates.

Acceptance:
- Operators can predict map behavior for any host capability profile.

Verification:
- Guidance cross-checked with support matrix and fallback contracts.

## Sequence and release gating

Phase order:
1. Immediate: MDR-I1, MDR-I2, MDR-I3, MDR-I4.
2. Near-term: MDR-N1, MDR-N2, MDR-N3, MDR-N4.
3. Medium-term: MDR-M1, MDR-M2, MDR-M3.
4. Ecosystem: MDR-E1, MDR-E2, MDR-E3, MDR-E4.

Release gates:
1. Immediate gate: docs and compatibility contracts aligned, no conflicting guidance.
2. Near-term gate: deterministic test/simulation coverage in place.
3. Medium-term gate: offline/quality/scenario outputs verified through integration tests.
4. Ecosystem gate: public guidance/examples reviewed against real host constraints.

## Risks and mitigations

- Risk: Host capability drift invalidates matrix and fallback assumptions.
  Mitigation: require matrix timestamp + evidence link updates each release cycle.
- Risk: Contract drift between docs and runtime payloads.
  Mitigation: add schema validation checks into tests and release checklist.
- Risk: Trial instability across browsers increases false failures.
  Mitigation: deterministic host simulation and fixed-fixture replay.
- Risk: Sidecar/offline options fragment baseline guidance.
  Mitigation: preserve `os_maps.render` as required baseline for all profiles.

## Tracking update policy

When any workstream status changes, update in the same change set:

1. `PROGRESS.MD` status table for the workstream ID.
2. `CONTEXT.md` current focus/active work and decisions (if changed).
3. `CHANGELOG.md` unreleased notes for completed milestones.
