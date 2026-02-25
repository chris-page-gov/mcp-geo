---
name: mcp-geo-repo-extent-complexity
description: Analyze mcp-geo repository extent and functional complexity using dual-scope inventory, generated-output exclusion, hotspot scoring (complexity x churn), and optional GitHub stats.
---

# MCP Geo Repo Extent and Complexity

Use this skill when you need a reliable complexity/extent snapshot for this repo,
including mixed content and non-git files, while avoiding inflation from generated
outputs.

## Why this skill

- Produces a dual-scope view:
  - `git_tracked` (what is committed)
  - `workspace` (tracked + untracked non-ignored)
- Focuses on functional complexity, not artifact volume.
- Excludes known generated/output paths by default and honors Linguist attributes
  (`linguist-generated`, `linguist-vendored`) when available.
- Surfaces change-risk hotspots using `complexity x churn`.

## Inputs

- Local repository checkout.
- Optional GitHub access via `gh` CLI for additional stats.

## Outputs

- Markdown report in `docs/reports/`.
- Manager-facing report card in `docs/reports/` with plain-English terminology,
  source/basis notes, and practical implications.
- Optional JSON payload for dashboards/time-series tracking.

## Runbook

1. Generate report (recommended):

```bash
python3 scripts/repo_extent_complexity_report.py \
  --scope both \
  --lookback-days 180 \
  --top-hotspots 20 \
  --output docs/reports/repo_extent_complexity_$(date -u +%F).md \
  --json-output docs/reports/repo_extent_complexity_$(date -u +%F).json \
  --manager-output docs/reports/repo_extent_complexity_report_card_$(date -u +%F).md
```

2. Include GitHub stats when `gh` is authenticated:

```bash
python3 scripts/repo_extent_complexity_report.py \
  --scope both \
  --include-github
```

3. Add custom exclusions when needed (for generated assets):

```bash
python3 scripts/repo_extent_complexity_report.py \
  --exclude-glob "data/exports/**" \
  --exclude-glob "playground/screenshots/**"
```

## Interpretation guide

- Use the manager report card for non-technical stakeholders; it explains each
  metric in plain English with practical operational impact.
- Prioritize hotspots with both high `complexity_points` and high recent churn.
- Use `workspace` scope to catch high-risk uncommitted/untracked code.
- Use `git_tracked` scope for release and governance reporting.
- Treat docs/data growth as context, not implementation complexity.

## References

Read [references/sota_practice.md](references/sota_practice.md) for the metric
model rationale and source links.
