#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_PATH="${1:-$ROOT_DIR/build/vendor-snapshot-$(date +%Y%m%d).tar.gz}"

mkdir -p "$(dirname "$OUT_PATH")"

declare -a INPUTS=()
OPENAI_SNAPSHOT="docs/vendor/openai/_snapshot"
OPENAI_NOSCRIPT="docs/vendor/openai/_snapshot_noscript"
MCP_SNAPSHOT="docs/vendor/mcp/_snapshot"

if [[ -d "$ROOT_DIR/$OPENAI_SNAPSHOT" ]]; then
  INPUTS+=("$OPENAI_SNAPSHOT")
fi
if [[ -d "$ROOT_DIR/$OPENAI_NOSCRIPT" ]]; then
  INPUTS+=("$OPENAI_NOSCRIPT")
fi
if [[ -d "$ROOT_DIR/$MCP_SNAPSHOT" ]]; then
  INPUTS+=("$MCP_SNAPSHOT")
fi

if [[ ${#INPUTS[@]} -eq 0 ]]; then
  echo "No snapshots found. Run scripts/vendor_fetch.sh first." >&2
  exit 1
fi

tar -czf "$OUT_PATH" -C "$ROOT_DIR" "${INPUTS[@]}"
echo "Wrote $OUT_PATH"
