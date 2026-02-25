# MCP Geo Repository Report Card (Manager View)

Generated: `2026-02-25T06:34:25.969900Z`
Reporting scope used for the card: `workspace`
Lookback window: `180` days

## Executive Snapshot

This report card is designed for non-technical management. It summarizes maintenance risk, delivery pressure, and concentration risk using repository evidence and standard software-health metrics.

- Overall risk signal: `Very High`
- Priority risks to watch: `Change load`, `Footprint scale`

## Report Card

| Indicator | Current value | Assessment | Terminology (plain English) | Practical meaning | Basis / source |
| --- | --- | --- | --- | --- | --- |
| Functional implementation footprint | 62.2k LOC across 271 files | High | Functional LOC counts non-blank lines in code files, excluding generated/output files. | Higher size increases onboarding, review, and regression-testing effort. | Local file inventory (`git ls-files` / workspace walk) + policy/Linguist exclusions. |
| Recent change load | 229,543 lines changed in 263 commits (4 active authors, intensity 3.69x) | Very High | Change intensity is recent changed lines divided by current functional LOC. | Higher change load means more coordination pressure and release-risk exposure. | `git log --numstat --since=180d`. |
| Structural complexity (Python) | P90 CC 9.0, mean 4.1, max 138 across 2,294 functions | Moderate | Cyclomatic complexity approximates the number of decision paths in a function. | Higher complexity raises defect probability and test-case volume. | AST parsing of Python functions, aligned to Radon-style CC interpretation bands. |
| High-complexity function share | 126 of 2,294 functions (CC >= 15, 5.5%) | Moderate | CC >= 15 is treated as elevated complexity requiring tighter tests/review. | A higher share indicates concentrated maintainability and reliability risk. | Count of Python functions where cyclomatic complexity threshold is exceeded. |
| Hotspot concentration | Top-5 hotspots hold 23.4% of hotspot score (total score 84142.6) | Moderate | Hotspot score = complexity points x log2(1 + churn lines). | Higher concentration means a few files dominate change failure risk. | Complexity model + churn from local git history over the lookback window. |
| In-flight scope delta | 2,053 LOC difference (workspace 62.2k vs tracked 60.2k) | Moderate | Compares current workspace complexity with committed complexity. | Larger deltas indicate release plans may differ from current working state. | Dual-scope measurement (`workspace` minus `git_tracked`). |
| Generated/output exclusion control | 39 files excluded in primary scope `workspace` | Control | Generated outputs are files produced by scripts/builds, not hand-maintained logic. | Prevents report inflation so management decisions reflect real implementation load. | GitHub Linguist attrs + deterministic exclusion policy globs. |

## Practical Interpretation

- Hotspot concentration is manageable; continue routine hotspot monitoring.
- Structural complexity is within routine operating range for current scope.
- Plan for tighter release coordination because recent change volume is high relative to system size.
- Workspace-to-branch delta is limited; release-state reporting is representative.

## Top Hotspots (Management Attention)

- `scripts/boundary_pipeline.py`: score `5127.13` (complexity `460.00`, churn `2,265`).
- `tools/ons_data.py`: score `4674.18` (complexity `416.00`, churn `2,411`).
- `server/stdio_adapter.py`: score `3500.19` (complexity `312.00`, churn `2,382`).
- `tools/os_features.py`: score `3199.71` (complexity `301.00`, churn `1,584`).
- `tools/nomis_data.py`: score `3196.98` (complexity `312.00`, churn `1,214`).

## Terminology Glossary

- `Functional LOC`: Non-blank lines in implementation code, after excluding generated/output files.
- `Cyclomatic Complexity (CC)`: A proxy for how many decision paths code contains.
- `P90 complexity`: The value that 90% of functions are at or below; highlights the heavier tail.
- `Churn`: How many lines changed recently (adds + deletes) in git history.
- `Hotspot`: Code that is both complex and changed frequently, so it carries higher risk.
- `Dual scope`: Comparing committed files (`git_tracked`) versus current local files (`workspace`).

## Metric Basis and Sources

- Local git inventory and churn: Uses `git ls-files` and `git log --numstat` in the configured lookback window.
- Generated-output filtering: Uses GitHub Linguist attrs (`linguist-generated`, `linguist-vendored`) plus policy globs. (https://github.com/github-linguist/linguist)
- Cyclomatic complexity interpretation: Python AST-derived CC values interpreted using common Radon guidance bands. (https://radon.readthedocs.io/en/master/intro.html#cyclomatic-complexity)
- Hotspot practice: Hotspot framing follows complexity x churn approaches used in code-health tooling. (https://docs.enterprise.codescene.io/versions/6.7.8/guides/technical/hotspots.html)
- Optional GitHub repository statistics: When enabled, aggregates GitHub Stats API via `gh` CLI. (https://docs.github.com/rest/metrics/statistics)

## Notes and Limits

- This is a risk-oriented management snapshot, not a release gate by itself.
- Non-Python complexity uses branch-keyword proxies; Python uses AST-level CC.
- Generated/output files are intentionally excluded to avoid inflating implementation scope.
