#!/usr/bin/env bash
set -euo pipefail

# Pin key upstream repos as submodules under docs/vendor/.
# This gives you a stable, reviewable offline copy (and easy updating) without scraping websites.
#
# Usage:
#   ./scripts/vendor_submodules.sh
#
# Notes:
# - Run from the repo root.
# - You can later update with:
#     git submodule update --remote --merge

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p docs/vendor/mcp/repos docs/vendor/openai/repos

add_submodule () {
  local url="$1"
  local path="$2"
  if [ -e "$path" ]; then
    echo "Skipping (already exists): $path"
    return 0
  fi
  git submodule add "$url" "$path"
}

# MCP spec + docs source
add_submodule "https://github.com/modelcontextprotocol/modelcontextprotocol.git" "docs/vendor/mcp/repos/modelcontextprotocol"

# MCP Apps extension / SDK proposal (SEP-1865)
add_submodule "https://github.com/modelcontextprotocol/ext-apps.git" "docs/vendor/mcp/repos/ext-apps"

# Inspector
add_submodule "https://github.com/modelcontextprotocol/inspector.git" "docs/vendor/mcp/repos/inspector"

# OpenAI Apps SDK examples (useful for UI rendering patterns)
add_submodule "https://github.com/openai/openai-apps-sdk-examples.git" "docs/vendor/openai/repos/openai-apps-sdk-examples"

echo "==> Submodules added."
echo "Now run:"
echo "  git submodule update --init --recursive"
