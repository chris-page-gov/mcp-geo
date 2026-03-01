# Compact-Windows Strict Acceptance Baseline Run (2026-03-01)

## Run intent

Apply the strict acceptance gate defined in:

- `docs/reports/compact_windows_unattended_implementation_and_test_plan_2026-03-01.md`
- `docs/reports/compact_windows_acceptance_checklist_2026-03-01.json`

Policy:

- every required check must be automated and passing
- no manual waivers

## Evidence executed

```bash
npm --prefix playground run test -- --reporter=line \
  playground/tests/geography_selector.spec.js \
  playground/tests/boundary_explorer_local_layers.spec.js \
  playground/tests/boundary_explorer_host_harness.spec.js

npm --prefix playground run test -- --list
```

Observed:

- focused UI run: `3 passed`
- default suite inventory: `7 tests in 5 files`
- compact-window strict suite does not yet exist as dedicated unattended gate

## Strict gate outcome (pre-implementation baseline)

| UI | Strict gate result | Why it fails strict gate now |
| --- | --- | --- |
| Boundary Explorer | FAIL | Partial automation only; compact layout checks and full option matrix are not fully automated. |
| Geography Selector | FAIL | Partial automation only; compact layout + full style/opacity/layer matrix not exhaustively automated. |
| Statistics Dashboard | FAIL | No dedicated strict automation for compact behavior or full interaction matrix. |
| Simple Map Lab | FAIL | No dedicated strict compact-window automation; MCP-host compact contract not implemented. |
| Feature Inspector | FAIL | Static mock; missing MCP-Apps handshake and strict automation. |
| Route Planner | FAIL | Static mock; missing MCP-Apps handshake and strict automation. |

Overall strict status: **0 / 6 UIs pass**.

## Existing automation coverage map

Current automated coverage includes:

- Boundary Explorer:
  - fullscreen fallback handshake behavior
  - local layer import path (`.geojson`, `.zip`) and selection impact
- Geography Selector:
  - style switch and retained point overlays

Coverage gaps that force strict failure:

1. No exhaustive compact-window viewport assertions (`320x500`, `360x500`) across all six UIs.
2. No exhaustive option exerciser for all style/layer/opacity combinations.
3. No automated contract for UPRN attribute filtering (address/classification/flags).
4. No strict CI gate command for compact suite yet.
5. No MCP-Apps contract coverage for Feature Inspector and Route Planner.

## Required next run to pass strict gate

The following unattended commands must exist and pass:

```bash
npm --prefix playground run test:compact
npm --prefix playground run test:compact-matrix
```

Acceptance condition:

- all required checks in `compact_windows_acceptance_checklist_2026-03-01.json` pass for each UI
- run emits machine-readable result artifacts and screenshots per UI profile
