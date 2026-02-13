# MCP Geo Map Delivery Research Pack (2026-02)

## Scope

This research pack investigates how `mcp-geo` can deliver map outputs reliably across:

- AI MCP clients
- web browsers
- GIS desktop tools
- map server and hosted deployment patterns

It combines user research, standards/library landscape analysis, and containerized trial execution.

## Contents

- `00_journal.md`: chronological progress log with embedded screenshots.
- `01_personas_and_user_journeys.md`: persona definitions and journey requirements.
- `02_map_delivery_options_longlist.md`: broad option scan and tradeoffs.
- `03_trial_design.md`: autonomous trial methodology and acceptance criteria.
- `04_trial_results.md`: measured outcomes from Playwright + MCP runtime checks.
- `05_external_scan_os_and_community.md`: OS docs/repos plus open-source mapping MCP server review.
- `06_recommendations_and_report.md`: final evaluation, selected options, and roadmap.
- `reports/trial_summary.md`: generated matrix summary from JSON logs.
- `notebooks/map_delivery_option_tracker.ipynb`: optional notebook tracker.
- `evidence/logs/*`: raw execution logs.
- `evidence/screenshots/*`: trial screenshots.

## Re-run Trial Suite

From repo root:

```bash
./scripts/run_map_delivery_trials.sh
python3 scripts/map_trials/summarize_playwright_trials.py
```

## Key Evidence Artifacts

- Devcontainer MCP baseline: `research/map_delivery_research_2026-02/evidence/logs/devcontainer_mcp_baseline_2026-02-13_v2.log`
- Trial run log: `research/map_delivery_research_2026-02/evidence/logs/map_delivery_trials_run_20260213T200601Z.log`
- Trial observations JSONL: `research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl`
- Trial report JSON: `research/map_delivery_research_2026-02/evidence/logs/playwright_trials_results.json`
