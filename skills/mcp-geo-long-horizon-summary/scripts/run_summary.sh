#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DATE_UTC="$(date -u +%F)"
OUT_MD="$ROOT_DIR/docs/reports/mcp_geo_codex_long_horizon_summary_${DATE_UTC}.md"
OUT_JSON="$ROOT_DIR/docs/reports/mcp_geo_codex_long_horizon_summary_${DATE_UTC}.json"
OUT_SVG="$ROOT_DIR/docs/reports/mcp_geo_codex_long_horizon_summary_${DATE_UTC}.svg"

python3 "$ROOT_DIR/scripts/codex_long_horizon_summary.py" \
  --repo-filter mcp-geo \
  --output "$OUT_MD" \
  --summary-svg-output "$OUT_SVG" \
  --summary-title "Codex MCP-Geo Summary" \
  --json-output "$OUT_JSON"

printf 'Markdown: %s\n' "$OUT_MD"
printf 'Summary card SVG: %s\n' "$OUT_SVG"
printf 'JSON: %s\n' "$OUT_JSON"
