#!/usr/bin/env bash
set -euo pipefail

# Static snapshotter for supported documentation pages that still need local HTML snapshots.
# Requires: wget
#
# Usage:
#   ./scripts/vendor_fetch.sh
#
# Output:
#   docs/vendor/mcp/_snapshot/<host>/<path>/index.html (and assets)
#   docs/vendor/os/_snapshot/<host>/<path>/index.html (and assets)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MCP_OUT="$ROOT_DIR/docs/vendor/mcp/_snapshot"
OS_OUT="$ROOT_DIR/docs/vendor/os/_snapshot"

mkdir -p "$MCP_OUT" "$OS_OUT"

VENDOR_TARGETS="${VENDOR_TARGETS:-mcp,os}"

has_target() {
  local target="$1"
  [[ ",${VENDOR_TARGETS}," == *",${target},"* ]]
}

# Be polite
WGET_COMMON=(
  --mirror
  --page-requisites
  --convert-links
  --adjust-extension
  --no-host-directories
  --restrict-file-names=windows
  --wait=1
  --random-wait
  --tries=3
  --timeout=20
  --user-agent="mcp-geo-doc-vendor/1.0"
)

MCP_URLS=(
  "https://modelcontextprotocol.io/specification/2025-11-25"
  "https://modelcontextprotocol.io/specification/2025-11-25/basic/transports"
  "https://modelcontextprotocol.io/docs/tools/inspector"
  "https://modelcontextprotocol.io/docs/learn/architecture"
  "https://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/"
)

OS_URLS=(
  "https://labs.os.uk/public/os-data-hub-examples/resources.json"
  "https://labs.os.uk/public/os-data-hub-examples/os-vector-tile-api/vts-3857-basic-map#maplibre-gl-js"
  "https://labs.os.uk/public/os-data-hub-examples/os-vector-tile-api/vts-example-custom-style#maplibre-gl-js"
  "https://labs.os.uk/public/os-data-hub-examples/os-vector-tile-api/vts-example-3d-buildings#maplibre-gl-js"
  "https://labs.os.uk/public/os-data-hub-examples/os-vector-tile-api/vts-example-add-overlay#maplibre-gl-js"
  "https://labs.os.uk/public/os-data-hub-examples/dist/os-vector-tile-api/maplibre-gl-js-vts-3857-basic-map.php?auth="
  "https://labs.os.uk/public/os-data-hub-examples/dist/os-vector-tile-api/maplibre-gl-js-vts-example-custom-style.php?auth="
  "https://labs.os.uk/public/os-data-hub-examples/dist/os-vector-tile-api/maplibre-gl-js-vts-example-3d-buildings.php?auth="
  "https://labs.os.uk/public/os-data-hub-examples/dist/os-vector-tile-api/maplibre-gl-js-vts-example-add-overlay.php?auth="
)

if has_target "openai"; then
  echo "==> Skipping deprecated OpenAI docs snapshot refresh."
  echo "    Use the shared openaiDeveloperDocs MCP server at https://developers.openai.com/mcp instead."
fi

if has_target "mcp"; then
  echo "==> Fetching MCP docs pages…"
  ( cd "$MCP_OUT" && wget "${WGET_COMMON[@]}" "${MCP_URLS[@]}" )
fi

if has_target "os"; then
  echo "==> Fetching OS docs pages…"
  ( cd "$OS_OUT" && wget "${WGET_COMMON[@]}" "${OS_URLS[@]}" )
fi

echo "==> Done."
if has_target "mcp"; then
  echo "MCP snapshots:    $MCP_OUT"
fi
if has_target "os"; then
  echo "OS snapshots:     $OS_OUT"
fi
