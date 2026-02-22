# Testing and Quality

## Test suite

- Pytest with >=90% coverage gate.
- Success, validation, and upstream error paths covered.
- STDIO adapter behaviors tested (notification handling, framing).

## Current execution status (2026-02-21)

- Strict regression (`pytest -q`):
  - `785 passed`, `6 skipped`
  - Coverage gate failed: `86.69%` (required `>= 90%`)
- Live evaluation harness:
  - Report: `data/evaluation_results_live_review_2026-02-21_after_patch2_full.json`
  - Score: `6290/6900` (`91.16%`)
  - Passed questions: `67/69`
- Missing-tool live probe:
  - Report: `data/live_missing_tools_probe_report_2026-02-21.json`
  - Result: `27/28` pass; `1/28` blocked by auth entitlement
    (`os_features.wfs_archive_capabilities`)
- Combined live tool operability:
  - Report: `data/spec_tool_operability_coverage_2026-02-21.json`
  - Functional tools: `75/76` (`98.68%`)
  - Release-gated functional tools (excluding optional entitlement):
    `75/75` (`100.0%`)
  - Blocked by auth: `1/76` (`1.32%`)
  - Unresolved tools: `0`
  - Optional-by-entitlement:
    `os_features.wfs_archive_capabilities` (tracked/evidenced but excluded
    from release-gated functional denominator)

## Quality standards

- Typed schemas for all tools.
- Max line length: 100.
- Ruff + mypy enforced.

## Static analysis status (2026-02-21)

- `ruff check .` currently fails across the repo (`1172` findings, many in
  scripts and line-length/import-order categories).
- `mypy server tools scripts` currently fails (`175` errors).
- These are release risks because there is no CI gate yet to keep static
  quality debt from regressing.

## Executable specification linkage

- Gherkin requirements:
  `docs/spec_package/14_tool_operability.feature`
- Measured requirement outcomes:
  `docs/spec_package/14_tool_operability_coverage.md`
- Coverage generator:
  `scripts/spec_tool_operability_coverage.py`

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
  to downgrade fail->warning when justified.
  - Supported policy fields:
    - `thresholds`: optional threshold overrides (`contrastFailMin`,
      `contrastWarnMin`, `labelDensityWarnMin`, `labelDensityFailMin`).
    - `waivers[]`: `trialId`, optional `browser`, and `reason`.
