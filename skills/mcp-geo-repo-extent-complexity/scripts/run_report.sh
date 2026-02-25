#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DATE_UTC="$(date -u +%F)"
OUT_MD="$ROOT_DIR/docs/reports/repo_extent_complexity_${DATE_UTC}.md"
OUT_JSON="$ROOT_DIR/docs/reports/repo_extent_complexity_${DATE_UTC}.json"
OUT_MANAGER="$ROOT_DIR/docs/reports/repo_extent_complexity_report_card_${DATE_UTC}.md"

python3 "$ROOT_DIR/scripts/repo_extent_complexity_report.py" \
  --scope both \
  --lookback-days 180 \
  --top-hotspots 20 \
  --output "$OUT_MD" \
  --json-output "$OUT_JSON" \
  --manager-output "$OUT_MANAGER"

printf 'Markdown: %s\n' "$OUT_MD"
printf 'JSON: %s\n' "$OUT_JSON"
printf 'Manager report card: %s\n' "$OUT_MANAGER"
