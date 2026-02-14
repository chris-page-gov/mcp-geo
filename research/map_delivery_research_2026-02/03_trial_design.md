# Trial Design

## Objectives

- Validate that map outputs are reliably renderable across multiple browser engines.
- Validate that MCP tool contracts for maps are directly consumable by clients.
- Validate that MCP-App interactive widgets still work where host support is available.
- Capture reproducible artifacts (logs, screenshots, machine-readable observations).

## Environment

- Devcontainer runtime for reproducibility.
- MCP server launched in-container via `uvicorn server.main:app`.
- Browser validation via Playwright in-container.

## Trial harness components

- Config: `playground/playwright.trials.config.js`
- Tests: `playground/trials/tests/map_delivery_matrix.spec.js`
- Runner: `scripts/run_map_delivery_trials.sh`
- Result summarizer: `scripts/map_trials/summarize_playwright_trials.py`

## Trial suite

| Trial ID | Purpose | Inputs | Expected outcome |
| --- | --- | --- | --- |
| `trial-1-static-osm` | Browser-level static route render | `/maps/static/osm` URL | image loads with non-zero dimensions |
| `trial-2-os-maps-render` | Tool-contract renderability | MCP `tools/call os_maps.render` | returned `imageUrl` renders successfully |
| `trial-3-geography-selector` | MCP-App widget interaction | `ui/geography_selector.html` + host stubs | map initializes and overlays persist after style switch |
| `trial-4-boundary-explorer` | Local layer interactive workflow | `ui/boundary_explorer.html` + inventory stub | polygon selection highlights matching UPRNs |

## Browser strategy

- Cross-browser mandatory for transport-level map delivery:
  - Chromium
  - Firefox
  - WebKit
- Widget-interaction tests run in Chromium for deterministic host emulation under `file://` loading.

## Pass/fail criteria

- Hard fail:
  - image dimensions zero
  - tool call cannot produce renderable URL
  - widget trial fails on required Chromium path
- Soft signal:
  - host-emulation variance on non-Chromium widget tests (captured as skipped)

## Evidence outputs

- JSON report: `research/map_delivery_research_2026-02/evidence/logs/playwright_trials_results.json`
- Observation JSONL: `research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl`
- Screenshots: `research/map_delivery_research_2026-02/evidence/screenshots/*.png`
- Run log: `research/map_delivery_research_2026-02/evidence/logs/map_delivery_trials_run_20260213T200601Z.log`
