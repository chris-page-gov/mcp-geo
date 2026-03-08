#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_PATH="${1:-$ROOT_DIR/build/vendor-snapshot-$(date +%Y%m%d).tar.gz}"

mkdir -p "$(dirname "$OUT_PATH")"

declare -a INPUTS=()
MCP_SNAPSHOT="docs/vendor/mcp/_snapshot"
OS_SNAPSHOT="docs/vendor/os/_snapshot"
if [[ -d "$ROOT_DIR/$MCP_SNAPSHOT" ]]; then
  INPUTS+=("$MCP_SNAPSHOT")
fi
if [[ -d "$ROOT_DIR/$OS_SNAPSHOT" ]]; then
  INPUTS+=("$OS_SNAPSHOT")
fi

if [[ ${#INPUTS[@]} -eq 0 ]]; then
  echo "No supported snapshots found. Run scripts/vendor_fetch.sh for MCP/OS docs first." >&2
  exit 1
fi

tar -czf "$OUT_PATH" -C "$ROOT_DIR" "${INPUTS[@]}"
echo "Wrote $OUT_PATH"
