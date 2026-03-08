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
server_cmd="$repo_root/scripts/codex-mcp-local"
openai_docs_server_name="openaiDeveloperDocs"
openai_docs_server_url="https://developers.openai.com/mcp"

remove_server() {
  local name="$1"
  codex mcp remove "$name" >/dev/null 2>&1 || \
    codex mcp rm "$name" >/dev/null 2>&1 || true
}

ensure_stdio_server() {
  local name="$1"
  local command="$2"
  shift 2
  local -a add_args=("$@")

  if current_json="$(codex mcp get --json "$name" 2>/dev/null)"; then
    if printf '%s' "$current_json" | grep -Fq "\"$command\""; then
      return 0
    fi
    remove_server "$name"
  fi

  codex mcp add "${add_args[@]}" "$name" -- "$command"
}

ensure_http_server() {
  local name="$1"
  local url="$2"

  if current_json="$(codex mcp get --json "$name" 2>/dev/null)"; then
    if printf '%s' "$current_json" | grep -Fq "\"$url\""; then
      return 0
    fi
    remove_server "$name"
  fi

  codex mcp add "$name" --url "$url"
}

legacy_server_name="os-ngd-api"
if codex mcp get "$legacy_server_name" >/dev/null 2>&1; then
  remove_server "$legacy_server_name"
fi

env_args=()
for var in OS_API_KEY ONS_API_KEY ONS_LIVE_ENABLED LOG_LEVEL STDIO_KEY BEARER_TOKENS; do
  if [[ -n "${!var:-}" ]]; then
    env_args+=(--env "$var=${!var}")
  fi
done

ensure_stdio_server "$server_name" "$server_cmd" "${env_args[@]}"
ensure_http_server "$openai_docs_server_name" "$openai_docs_server_url"
