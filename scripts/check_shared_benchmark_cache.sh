#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POSTGIS_CONTAINER="${MCP_GEO_BENCHMARK_POSTGIS_CONTAINER:-mcp-geo_devcontainer-postgis-1}"

find_docker() {
  local candidate
  for candidate in /usr/local/bin/docker /opt/homebrew/bin/docker /usr/bin/docker; do
    if [[ -x "$candidate" ]]; then
      printf "%s" "$candidate"
      return 0
    fi
  done
  command -v docker 2>/dev/null || true
}

DOCKER_BIN="$(find_docker)"
if [[ -z "$DOCKER_BIN" || ! -x "$DOCKER_BIN" ]]; then
  echo "FAIL: docker not found" >&2
  exit 1
fi

fail() {
  printf "FAIL: %s\n" "$*" >&2
  exit 1
}

info() {
  printf "%s\n" "$*"
}

plan_value() {
  local key="$1"
  awk -F= -v target="$key" '$1 == target {print substr($0, index($0, "=") + 1)}'
}

if ! "$DOCKER_BIN" info >/dev/null 2>&1; then
  fail "docker is not running"
fi

if ! "$DOCKER_BIN" container inspect "$POSTGIS_CONTAINER" >/dev/null 2>&1; then
  fail "shared PostGIS container not found: $POSTGIS_CONTAINER"
fi

if [[ "$("$DOCKER_BIN" container inspect -f '{{.State.Running}}' "$POSTGIS_CONTAINER")" != "true" ]]; then
  fail "shared PostGIS container is not running: $POSTGIS_CONTAINER"
fi

extensions="$("$DOCKER_BIN" exec "$POSTGIS_CONTAINER" \
  psql -U mcp_geo -d mcp_geo -Atqc \
  "SELECT extname || '=' || extversion FROM pg_extension WHERE extname IN ('postgis','pgrouting') ORDER BY extname;")"

printf "%s\n" "$extensions" | rg -q '^postgis=' || fail "postgis extension missing in $POSTGIS_CONTAINER"
printf "%s\n" "$extensions" | rg -q '^pgrouting=' || fail "pgrouting extension missing in $POSTGIS_CONTAINER"

cache_counts="$("$DOCKER_BIN" exec "$POSTGIS_CONTAINER" \
  psql -U mcp_geo -d mcp_geo -Atqc \
  "SELECT 'boundary_datasets=' || COUNT(*) FROM public.boundary_datasets;
   SELECT 'admin_boundaries=' || COUNT(*) FROM public.admin_boundaries;
   SELECT 'routing_graph_metadata=' || COUNT(*) FROM routing.graph_metadata;")"

claude_plan="$(
  MCP_GEO_DOCKER_PLAN_ONLY=1 \
  MCP_GEO_DOCKER_BUILD=never \
  MCP_GEO_POSTGIS_BUILD=never \
  "$REPO_ROOT/scripts/claude-mcp-local"
)"

codex_plan="$(
  MCP_GEO_DOCKER_PLAN_ONLY=1 \
  MCP_GEO_DOCKER_BUILD=never \
  MCP_GEO_POSTGIS_BUILD=never \
  MCP_GEO_CODEX_LAUNCHER=docker \
  "$REPO_ROOT/scripts/codex-mcp-local"
)"

claude_target="$(printf "%s\n" "$claude_plan" | plan_value postgis_target_container)"
claude_manage="$(printf "%s\n" "$claude_plan" | plan_value manage_postgis_container)"
codex_target="$(printf "%s\n" "$codex_plan" | plan_value postgis_target_container)"
codex_manage="$(printf "%s\n" "$codex_plan" | plan_value manage_postgis_container)"
shared_network="$(printf "%s\n" "$claude_plan" | plan_value network)"

[[ "$claude_target" == "$POSTGIS_CONTAINER" ]] || fail "Claude wrapper targets $claude_target, expected $POSTGIS_CONTAINER"
[[ "$codex_target" == "$POSTGIS_CONTAINER" ]] || fail "Codex wrapper targets $codex_target, expected $POSTGIS_CONTAINER"
[[ "$claude_manage" == "false" ]] || fail "Claude wrapper would start its own PostGIS container"
[[ "$codex_manage" == "false" ]] || fail "Codex wrapper would start its own PostGIS container"

for fallback in mcp-geo-postgis-sidecar mcp-geo-postgis-claude mcp-geo-postgis-codex; do
  if "$DOCKER_BIN" container inspect "$fallback" >/dev/null 2>&1; then
    fail "fallback PostGIS container $fallback still exists; remove it before benchmarking"
  fi
done

info "PASS: shared benchmark cache is ready"
info "shared_postgis_container=$POSTGIS_CONTAINER"
info "shared_network=$shared_network"
info "$extensions"
info "$cache_counts"
info "claude_target=$claude_target"
info "codex_target=$codex_target"
