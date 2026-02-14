# Testing and Quality

## Test suite

- Pytest with >=90% coverage gate.
- Success, validation, and upstream error paths covered.
- STDIO adapter behaviors tested (notification handling, framing).

## Quality standards

- Typed schemas for all tools.
- Max line length: 100.
- Ruff + mypy enforced.

## Recommended additional tests (backlog)

- MCP-Apps UI rendering in a real client (Inspector + Claude).
- Boundary cache regression tests for freshness metadata.
- ONS dataset cache snapshot tests.

## Map output quality checks

- Trial screenshot checks run via `scripts/map_trials/map_quality_checks.py`.
- Metrics:
  - contrast ratio proxy (`p95 - p05` luminance spread),
  - label-density proxy (edge-density estimate),
  - accessibility metadata presence (`details.accessibility.altText`).
- Thresholds and status levels are emitted in
  `research/map_delivery_research_2026-02/reports/map_quality_report.json`.
- Waiver process:
  add approved exceptions to
  `research/map_delivery_research_2026-02/reports/map_quality_waivers.json`
  (`trialId` + `reason`) to downgrade fail->warning when justified.
