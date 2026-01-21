#!/usr/bin/env bash
set -euo pipefail

# Static snapshotter for specific documentation pages so an offline code assistant can read them.
# Requires: wget
#
# Usage:
#   ./scripts/vendor_fetch.sh
#
# Output:
#   docs/vendor/openai/_snapshot/<host>/<path>/index.html (and assets)
#   docs/vendor/mcp/_snapshot/<host>/<path>/index.html (and assets)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

OPENAI_OUT="$ROOT_DIR/docs/vendor/openai/_snapshot"
MCP_OUT="$ROOT_DIR/docs/vendor/mcp/_snapshot"

mkdir -p "$OPENAI_OUT" "$MCP_OUT"

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

# We avoid crawling entire sites; we fetch only these pages and their requisites.
OPENAI_URLS=(
  "https://platform.openai.com/docs/guides/developer-mode"
  "https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt-beta"
  "https://help.openai.com/en/articles/11487775-connectors-in-chatgpt"
  "https://developers.openai.com/apps-sdk/"
  "https://developers.openai.com/apps-sdk/quickstart/"
  "https://developers.openai.com/apps-sdk/deploy/connect-chatgpt/"
  "https://developers.openai.com/apps-sdk/build/mcp-server/"
  "https://developers.openai.com/apps-sdk/build/chatgpt-ui/"
  "https://developers.openai.com/apps-sdk/reference/"
  "https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk"
)

MCP_URLS=(
  "https://modelcontextprotocol.io/specification/2025-11-25"
  "https://modelcontextprotocol.io/specification/2025-11-25/basic/transports"
  "https://modelcontextprotocol.io/docs/tools/inspector"
  "https://modelcontextprotocol.io/docs/learn/architecture"
  "https://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/"
)

echo "==> Fetching OpenAI docs pages…"
( cd "$OPENAI_OUT" && wget "${WGET_COMMON[@]}" "${OPENAI_URLS[@]}" )

echo "==> Fetching MCP docs pages…"
( cd "$MCP_OUT" && wget "${WGET_COMMON[@]}" "${MCP_URLS[@]}" )

echo "==> Done."
echo "OpenAI snapshots: $OPENAI_OUT"
echo "MCP snapshots:    $MCP_OUT"
