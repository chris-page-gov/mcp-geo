#!/usr/bin/env bashset -euo pipefail

if ! command -v codex >/dev/null 2>&1; then
  exit 0
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
server_name="mcp-geo"
server_cmd="$repo_root/scripts/os-mcp"

if codex mcp get "$server_name" >/dev/null 2>&1; then
  exit 0
fi

env_args=()
for var in OS_API_KEY ONS_API_KEY ONS_LIVE_ENABLED LOG_LEVEL STDIO_KEY BEARER_TOKENS; do
  if [ -n "${!var:-}" ]; then
    env_args+=(--env "$var=${!var}")
  fidone

codex mcp add "${env_args[@]}" "$server_name" -- "$server_cmd"
