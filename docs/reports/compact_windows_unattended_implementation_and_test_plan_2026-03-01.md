# Compact-Windows Unattended Implementation and Test Plan (2026-03-01)

## Goal

Deliver all six MCP-Apps UIs with deterministic behavior in compact host windows, and gate changes with a strict unattended Playwright harness that exercises all supported options and interactions.

Target branch: `codex/compact-windows`

## Scope

In scope:

- `ui/boundary_explorer.html`
- `ui/geography_selector.html`
- `ui/statistics_dashboard.html`
- `ui/simple_map.html`
- `ui/feature_inspector.html`
- `ui/route_planner.html`
- Playwright rewrite/expansion in `playground/tests` and `playground/trials/tests`
- Deterministic host simulation and fixture data for full option coverage

Out of scope:

- New backend tool families not already represented by current contracts
- Production visual polish beyond compact-window functional requirements

## Non-negotiable design contract

- Primary design budget: `320 x 500`
- Comfort budget: `360 x 500`
- Fullscreen is optional enhancement only
- Core flow must work with host inline mode only (VS Code-compatible)

## Current baseline (strict checklist run)

### Evidence commands executed

```bash
npm --prefix playground run test -- --reporter=line \
  playground/tests/geography_selector.spec.js \
  playground/tests/boundary_explorer_local_layers.spec.js \
  playground/tests/boundary_explorer_host_harness.spec.js

npm --prefix playground run test -- --list
```

Results:

- Focused run: `3 passed`
- Current default Playwright suite inventory: `7 tests`
- No dedicated automated tests currently exist for compact behavior across all six UIs.

### Strict checklist status by UI (pre-implementation)

Legend:

- `PASS`: implemented and verified by automated evidence
- `PARTIAL`: implemented but not fully automated/strictly verified
- `FAIL`: missing or not meeting compact-window contract

| UI | Compact 320x500 | Host handshake | Fullscreen fallback | Option coverage automation | Key feature coverage automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Boundary Explorer | FAIL | PASS | PASS | PARTIAL | PARTIAL | FAIL |
| Geography Selector | FAIL | PASS | PARTIAL | PARTIAL | PARTIAL | FAIL |
| Statistics Dashboard | FAIL | PASS | PARTIAL | FAIL | FAIL | FAIL |
| Simple Map Lab | FAIL | FAIL | FAIL | PARTIAL | PARTIAL | FAIL |
| Feature Inspector | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| Route Planner | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |

## Detailed interaction specification (must be automated)

### A. Shared host/runtime interactions (all six UIs)

1. `ui/initialize` handshake success path.
2. `ui/notifications/host-context-changed` merge behavior.
3. Inline-only host profile behavior (`availableDisplayModes=["inline"]`).
4. Fullscreen-capable profile behavior (`["inline","fullscreen"]`).
5. `containerDimensions` handling for `height`, `maxHeight`, `width`, `maxWidth`.
6. Layout invariants at `320x500` and `360x500`.
7. No horizontal overflow in compact mode.
8. Primary CTA visible without scrolling at initial render.

### B. Map/style controls

1. Basemap style dropdown: exercise every option.
2. Basemap opacity slider/control: test min/mid/max values.
3. Style switch rehydration: overlays remain visible and stateful.
4. Worker/script fetch path remains valid after style changes.

### C. Layer controls and domain overlays

1. Toggle layers on/off and verify map layer visibility + source data:
   - Boundaries
   - UPRN density
   - UPRN dots/highlights
   - Building polygons
   - RoadLinks
   - PathLinks
   - Postcode overlays (where applicable)
   - USRN-linked layers/attributes (where surfaced)
2. Verify selected boundary highlighting and hierarchy context rendering.
3. Verify linked UPRN propagation from selected boundaries.
4. Verify debug/diagnostic counters update deterministically.

### D. Selection and filtering interactions

1. Boundary select/deselect workflows.
2. Click and box-drag multi-select workflows.
3. Postcode-level and UPRN-level detail mode transitions.
4. UPRN attribute filtering workflows:
   - postal address text
   - classification code/description
   - boolean/enum flags
5. Include/exclude behavior for highlighted UPRNs.

### E. Local data import and file interactions

1. Drag/drop and file input flows (where supported):
   - `.geojson`
   - `.csv`
   - `.zip` (Shapefile)
2. Imported layer list rendering.
3. Imported polygon selection impact on highlighted records.
4. Invalid file handling and user-facing errors.

### F. Diagnostics and reliability

1. Missing tool fallback paths.
2. Auth failures (`401/403`) with plain-language status.
3. Empty-result states.
4. Export action behavior and payload integrity.

## Unattended implementation workstreams

## CW-1 Shared compact-window framework

Deliverables:

- shared compact layout utility and CSS tokens for all UIs
- shared host-context utility (`displayMode`, `availableDisplayModes`, `containerDimensions`)
- standard status/CTA slot contract across UIs

Definition of done:

- all six UIs render in compact mode without horizontal overflow
- all six satisfy first-screen CTA/status visibility rule

## CW-2 Boundary Explorer hardening

Deliverables:

- compact-first layout path
- explicit layer/state model for boundary + linked UPRN hierarchy
- UPRN attribute filter panel (address/classification/flags)
- complete local layer import flow validation

Definition of done:

- strict checklist sections B/C/D/E/F pass for Boundary Explorer

## CW-3 Geography Selector hardening

Deliverables:

- compact-first layout path
- complete style/opacity/layer test hooks
- deterministic area/postcode/UPRN selection workflows

Definition of done:

- strict checklist sections A/B/C/D/F pass for Geography Selector

## CW-4 Statistics Dashboard compact migration

Deliverables:

- compact information architecture for datasets/dimensions/options/query
- deterministic fullscreen fallback behavior
- robust no-data/error states in compact mode

Definition of done:

- strict checklist sections A/F plus dashboard-specific query flows pass

## CW-5 Simple Map Lab compact migration

Deliverables:

- compact host-aware variant
- complete auth mode tests (bearer/api/env fallback)
- full style option and diagnostics automation

Definition of done:

- strict checklist sections A/B/F pass for Simple Map Lab

## CW-6 Feature Inspector + Route Planner promotion

Deliverables:

- convert both from static mock pages to MCP-Apps-capable views
- add handshake, host context merge, compact layout
- add deterministic interaction contracts per page

Definition of done:

- strict checklist sections A/F pass for both UIs

## CW-7 Playwright rewrite for exhaustive unattended coverage

## Test architecture changes

Create a dedicated compact suite:

- `playground/tests/compact_windows/`
- `playground/tests/compact_windows/support/`
- `playground/tests/compact_windows/fixtures/`

Core harness components:

1. deterministic host bridge fixture with selectable host profiles:
   - `claude_inline_500`
   - `vscode_inline_only_500`
   - `fullscreen_capable_desktop`
2. deterministic tool response fixtures for each UI scenario
3. stable selector contract using `data-testid` attributes
4. generic control exerciser that iterates dropdown/range/checkbox combinations
5. contract assertions for map source/layer presence and selected-state propagation

## Coverage strategy

- Exhaustive for finite option sets (all style options, all layer toggles).
- Pairwise for combinatorial settings where exhaustive cost is too high, with explicit required combos for critical safety paths.
- Every control must have at least one positive and one negative-path assertion.

## CI gate

Proposed commands:

```bash
npm --prefix playground run test:compact
npm --prefix playground run test:compact-matrix
```

Release gate policy:

- any compact-window test failure blocks merge
- missing checklist item implementation blocks merge
- evidence artifacts (JSON + screenshots) emitted automatically per run

## Strict acceptance checklist (merge gate)

Each item is `required`. All must be green.

### Global (applies to every UI)

- `AC-G-01` compact viewport `320x500` no horizontal overflow
- `AC-G-02` compact viewport `360x500` no horizontal overflow
- `AC-G-03` primary CTA visible on first screen
- `AC-G-04` status/error strip visible on first screen
- `AC-G-05` keyboard-only navigation across primary controls
- `AC-G-06` deterministic loading/empty/error states
- `AC-G-07` no uncaught runtime exceptions in browser console

### MCP-Apps contract (where applicable)

- `AC-M-01` `ui/initialize` response handled
- `AC-M-02` `host-context-changed` merge handled
- `AC-M-03` inline-only host behavior correct
- `AC-M-04` fullscreen request fallback message correct
- `AC-M-05` `containerDimensions` variants handled

### Map/style/layer contract (map-capable UIs)

- `AC-L-01` style dropdown exhaustively exercised
- `AC-L-02` opacity control min/mid/max exercised
- `AC-L-03` layer toggles exhaustively exercised
- `AC-L-04` style swap preserves overlay state
- `AC-L-05` map diagnostics/reporting updated per change

### Domain selection/filter contract (boundary/geography-focused)

- `AC-D-01` boundary selection and deselection
- `AC-D-02` hierarchy highlight integrity
- `AC-D-03` linked UPRN propagation integrity
- `AC-D-04` UPRN attribute filters (address/classification/flags)
- `AC-D-05` postcode and UPRN detail-mode behavior

### Local import contract (where supported)

- `AC-I-01` geojson import flow
- `AC-I-02` csv import flow
- `AC-I-03` shapefile zip import flow
- `AC-I-04` import error handling
- `AC-I-05` import-driven selection correctness

## Per-UI acceptance map

| UI | Required groups |
| --- | --- |
| Boundary Explorer | AC-G, AC-M, AC-L, AC-D, AC-I |
| Geography Selector | AC-G, AC-M, AC-L, AC-D |
| Statistics Dashboard | AC-G, AC-M (+ dashboard query contract checks) |
| Simple Map Lab | AC-G, AC-L (+ auth/diagnostics contract checks) |
| Feature Inspector | AC-G, AC-M (+ inspector interaction contract checks) |
| Route Planner | AC-G, AC-M (+ route interaction contract checks) |

## Implementation sequence (unattended)

1. Add shared compact layout + host-context utilities.
2. Add `data-testid` instrumentation to all six UIs.
3. Implement Boundary Explorer + Geography Selector compact compliance and missing domain filters.
4. Build compact suite harness + fixtures.
5. Rewrite and expand Playwright tests to the new compact suite.
6. Migrate Statistics Dashboard + Simple Map Lab.
7. Promote Feature Inspector + Route Planner to MCP-Apps-capable pages.
8. Run full compact suite and trial suite; publish evidence artifacts.
9. Enforce merge gate on compact suite.

## Risks and mitigations

1. Risk: map rendering nondeterminism in CI.

- Mitigation: synthetic tile/worker fixtures and deterministic style mocks.

2. Risk: combinatorial explosion from option matrices.

- Mitigation: exhaustive only for finite controls; pairwise + mandatory critical combos otherwise.

3. Risk: host differences (Claude vs VS Code) cause false failures.

- Mitigation: separate host profile fixtures and assertions tied to each profile’s declared capabilities.

4. Risk: manual revalidation drift.

- Mitigation: all acceptance checks encoded as automated assertions and machine-readable run output.

## Exit criteria

The compact-windows branch is complete when:

- all six UIs pass strict acceptance checklist automation
- compact suite is unattended and green in CI
- no manual exploratory steps are required to validate functional behavior
- regression evidence is generated and archived per run
