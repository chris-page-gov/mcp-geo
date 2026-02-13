#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT/docs/spec_package/build"
mkdir -p "$OUT_DIR"

ORDER=(
  "docs/spec_package/01_aims_objectives.md"
  "docs/spec_package/02_personas_user_stories.md"
  "docs/spec_package/03_architecture.md"
  "docs/spec_package/04_system_design.md"
  "docs/spec_package/05_data_flow_and_cache.md"
  "docs/spec_package/06_api_contracts.md"
  "docs/spec_package/07_security_privacy.md"
  "docs/spec_package/08_observability_ops.md"
  "docs/spec_package/09_testing_quality.md"
  "docs/spec_package/10_mcp_apps_ui.md"
  "docs/spec_package/11_walkthroughs.md"
  "docs/spec_package/12_backlog_and_plan.md"
  "docs/spec_package/13_sequence_diagrams.md"
  "docs/spec_package/screenshots.md"
)

if ! command -v pandoc >/dev/null 2>&1; then
  echo "pandoc is required for export. Install pandoc and re-run." >&2
  exit 1
fi

pandoc "${ORDER[@]}" \
  -o "$OUT_DIR/mcp-geo-spec.docx" \
  --toc \
  --metadata title="MCP Geo Specification" \
  --resource-path="$ROOT/docs/spec_package:$ROOT/docs"

if command -v tectonic >/dev/null 2>&1; then
  pandoc "${ORDER[@]}" \
    -o "$OUT_DIR/mcp-geo-spec.pdf" \
    --toc \
    --metadata title="MCP Geo Specification" \
    --resource-path="$ROOT/docs/spec_package:$ROOT/docs"
fi

echo "Exported to $OUT_DIR"
