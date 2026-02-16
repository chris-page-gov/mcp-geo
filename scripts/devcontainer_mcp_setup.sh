#!/usr/bin/env bash
set -euo pipefail

if [[ "${MCP_GEO_DEVCONTAINER_REGISTER_STDIO:-1}" =~ ^(0|false|no)$ ]]; then
  exit 0
fi

# Registers the MCP server with the local Codex MCP registry (if available).
# No-op when codex isn't installed.

if ! command -v codex >/dev/null 2>&1; then
  exit 0
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
server_name="mcp-geo"
server_cmd="$repo_root/scripts/os-mcp"

legacy_server_name="os-ngd-api"
if codex mcp get "$legacy_server_name" >/dev/null 2>&1; then
  codex mcp remove "$legacy_server_name" >/dev/null 2>&1 || \
    codex mcp rm "$legacy_server_name" >/dev/null 2>&1 || true
fi

if codex mcp get "$server_name" >/dev/null 2>&1; then
  exit 0
fi

env_args=()
for var in OS_API_KEY ONS_API_KEY ONS_LIVE_ENABLED LOG_LEVEL STDIO_KEY BEARER_TOKENS; do
  if [[ -n "${!var:-}" ]]; then
    env_args+=(--env "$var=${!var}")
  fi
done

codex mcp add "${env_args[@]}" "$server_name" -- python3 "$server_cmd"
