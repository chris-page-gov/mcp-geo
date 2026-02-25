---
name: mcp-geo-long-horizon-summary
description: Generate a Long Horizon-style Codex metrics summary for mcp-geo from local Codex session logs.
---

# MCP Geo Long Horizon Summary

Use this skill when a user asks for an OpenAI "Long horizon tasks" style summary
for MCP Geo work (runtime, tokens, tool calls, patch volume, compactions, etc.).

## Inputs

- Codex session logs under `$CODEX_HOME` (defaults to `~/.codex`).
- Repo filter (default: `mcp-geo`).

## Output

- Summary-card SVG image in `docs/reports/`.
- Markdown report in `docs/reports/` that opens with the summary image.
- Optional JSON metrics payload for downstream dashboards.

## Runbook

1. Generate report:

```bash
python3 scripts/codex_long_horizon_summary.py \
  --repo-filter mcp-geo \
  --summary-svg-output docs/reports/mcp_geo_codex_long_horizon_summary_$(date -u +%F).svg \
  --summary-title "Codex MCP-Geo Summary" \
  --output docs/reports/mcp_geo_codex_long_horizon_summary_$(date -u +%F).md \
  --json-output docs/reports/mcp_geo_codex_long_horizon_summary_$(date -u +%F).json
```

2. If needed, point to a non-default Codex home:

```bash
python3 scripts/codex_long_horizon_summary.py \
  --codex-home /path/to/.codex \
  --repo-filter mcp-geo
```

3. Validate that the report includes these headline metrics:
- Active runtime
- Wall-clock span
- Token usage (input/output)
- Cached input reused
- Tool calls (shell + patch calls)
- Patch volume (added lines from `apply_patch`)
- Peak single-step tokens
- Auto context compactions

## Notes

- Sessions are included when `session_meta.payload.cwd` contains the repo filter.
- Patch volume is estimated from `apply_patch` payloads and will not include
  edits made through other methods.
- Token totals use the latest `token_count.total_token_usage` snapshot per session.
- Graphic output uses deterministic template file
  `skills/mcp-geo-long-horizon-summary/templates/summary_card.svg.tmpl` with
  slot-based number substitution.
- Template is tuned for slide import (`1920x1080`, 16:9) and uses
  PowerPoint-friendly inline text styling (no CSS `font` shorthand) to keep
  text sizing consistent.
