#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${MCP_GEO_BENCHMARK_CACHE_MODE:-isolated}"
POSTGIS_CONTAINER="${MCP_GEO_BENCHMARK_POSTGIS_CONTAINER:-mcp-geo_devcontainer-postgis-1}"
CLAUDE_WRAPPER="${MCP_GEO_BENCHMARK_CLAUDE_WRAPPER:-$REPO_ROOT/scripts/claude-mcp-local}"
CODEX_WRAPPER="${MCP_GEO_BENCHMARK_CODEX_WRAPPER:-$REPO_ROOT/scripts/codex-mcp-local}"
GEMINI_WRAPPER="${MCP_GEO_BENCHMARK_GEMINI_WRAPPER:-$REPO_ROOT/scripts/gemini-mcp-local}"

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

DOCKER_BIN="${MCP_GEO_DOCKER_BIN:-$(find_docker)}"
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

text_matches() {
  local pattern="$1"
  if command -v rg >/dev/null 2>&1; then
    rg -q "$pattern"
  else
    grep -Eq "$pattern"
  fi
}

plan_value() {
  local plan="$1"
  local key="$2"
  printf "%s\n" "$plan" | awk -F= -v target="$key" '$1 == target {print substr($0, index($0, "=") + 1)}'
}

count_value() {
  local summary="$1"
  local key="$2"
  printf "%s\n" "$summary" | awk -F= -v target="$key" '$1 == target {print $2; exit}'
}

require_running_container() {
  local container="$1"
  if ! "$DOCKER_BIN" container inspect "$container" >/dev/null 2>&1; then
    fail "required PostGIS container not found: $container"
  fi
  if [[ "$("$DOCKER_BIN" container inspect -f '{{.State.Running}}' "$container")" != "true" ]]; then
    fail "required PostGIS container is not running: $container"
  fi
}

extension_summary() {
  local container="$1"
  "$DOCKER_BIN" exec "$container" \
    psql -U mcp_geo -d mcp_geo -Atqc \
    "SELECT extname || '=' || extversion FROM pg_extension WHERE extname IN ('postgis','pgrouting') ORDER BY extname;"
}

count_summary() {
  local container="$1"
  "$DOCKER_BIN" exec "$container" \
    psql -U mcp_geo -d mcp_geo -Atqc \
    "SELECT 'boundary_datasets=' || COUNT(*) FROM public.boundary_datasets;
     SELECT 'admin_boundaries=' || COUNT(*) FROM public.admin_boundaries;
     SELECT 'routing_graph_metadata=' || COUNT(*) FROM routing.graph_metadata;
     SELECT 'landis_products=' || COUNT(*) FROM landis.product_registry;"
}

host_port_binding() {
  local container="$1"
  "$DOCKER_BIN" container inspect -f '{{with index .HostConfig.PortBindings "5432/tcp"}}{{(index . 0).HostPort}}{{end}}' "$container" 2>/dev/null || true
}

assert_same_value() {
  local label="$1"
  local first="$2"
  local second="$3"
  local third="$4"
  if [[ "$first" != "$second" || "$first" != "$third" ]]; then
    fail "$label mismatch across wrappers: claude=$first codex=$second gemini=$third"
  fi
}

collect_plan() {
  local wrapper="$1"
  shift
  if [[ ! -x "$wrapper" ]]; then
    fail "wrapper is not executable: $wrapper"
  fi
  env \
    MCP_GEO_DOCKER_PLAN_ONLY=1 \
    MCP_GEO_DOCKER_BUILD=never \
    MCP_GEO_POSTGIS_BUILD=never \
    "$@" \
    "$wrapper"
}

require_extensions() {
  local container="$1"
  local extensions="$2"
  printf "%s\n" "$extensions" | text_matches '^postgis=' \
    || fail "postgis extension missing in $container"
  printf "%s\n" "$extensions" | text_matches '^pgrouting=' \
    || fail "pgrouting extension missing in $container"
}

if ! "$DOCKER_BIN" info >/dev/null 2>&1; then
  fail "docker is not running"
fi

case "$MODE" in
  isolated|shared)
    ;;
  *)
    fail "unknown benchmark cache mode: $MODE (use isolated|shared)"
    ;;
esac

if [[ "$MODE" == "shared" ]]; then
  require_running_container "$POSTGIS_CONTAINER"

  shared_extensions="$(extension_summary "$POSTGIS_CONTAINER")"
  require_extensions "$POSTGIS_CONTAINER" "$shared_extensions"
  shared_counts="$(count_summary "$POSTGIS_CONTAINER")"

  claude_plan="$(
    collect_plan \
      "$CLAUDE_WRAPPER" \
      MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=1 \
      MCP_GEO_POSTGIS_REUSE_CONTAINER="$POSTGIS_CONTAINER"
  )"
  codex_plan="$(
    collect_plan \
      "$CODEX_WRAPPER" \
      MCP_GEO_CODEX_LAUNCHER=docker \
      MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=1 \
      MCP_GEO_POSTGIS_REUSE_CONTAINER="$POSTGIS_CONTAINER"
  )"
  gemini_plan="$(
    collect_plan \
      "$GEMINI_WRAPPER" \
      MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=1 \
      MCP_GEO_POSTGIS_REUSE_CONTAINER="$POSTGIS_CONTAINER"
  )"

  claude_target="$(plan_value "$claude_plan" postgis_target_container)"
  claude_manage="$(plan_value "$claude_plan" manage_postgis_container)"
  codex_target="$(plan_value "$codex_plan" postgis_target_container)"
  codex_manage="$(plan_value "$codex_plan" manage_postgis_container)"
  gemini_target="$(plan_value "$gemini_plan" postgis_target_container)"
  gemini_manage="$(plan_value "$gemini_plan" manage_postgis_container)"

  [[ "$claude_target" == "$POSTGIS_CONTAINER" ]] || fail "Claude wrapper targets $claude_target, expected $POSTGIS_CONTAINER"
  [[ "$codex_target" == "$POSTGIS_CONTAINER" ]] || fail "Codex wrapper targets $codex_target, expected $POSTGIS_CONTAINER"
  [[ "$gemini_target" == "$POSTGIS_CONTAINER" ]] || fail "Gemini wrapper targets $gemini_target, expected $POSTGIS_CONTAINER"
  [[ "$claude_manage" == "false" ]] || fail "Claude wrapper would start its own PostGIS container in shared mode"
  [[ "$codex_manage" == "false" ]] || fail "Codex wrapper would start its own PostGIS container in shared mode"
  [[ "$gemini_manage" == "false" ]] || fail "Gemini wrapper would start its own PostGIS container in shared mode"

  assert_same_value "landis_host_data_root" \
    "$(plan_value "$claude_plan" landis_host_data_root)" \
    "$(plan_value "$codex_plan" landis_host_data_root)" \
    "$(plan_value "$gemini_plan" landis_host_data_root)"
  assert_same_value "addressbase_xref_host_path" \
    "$(plan_value "$claude_plan" addressbase_xref_host_path)" \
    "$(plan_value "$codex_plan" addressbase_xref_host_path)" \
    "$(plan_value "$gemini_plan" addressbase_xref_host_path)"
  assert_same_value "ons_geo_host_cache_dir" \
    "$(plan_value "$claude_plan" ons_geo_host_cache_dir)" \
    "$(plan_value "$codex_plan" ons_geo_host_cache_dir)" \
    "$(plan_value "$gemini_plan" ons_geo_host_cache_dir)"
  assert_same_value "boundary_runs_search_host_paths" \
    "$(plan_value "$claude_plan" boundary_runs_search_host_paths)" \
    "$(plan_value "$codex_plan" boundary_runs_search_host_paths)" \
    "$(plan_value "$gemini_plan" boundary_runs_search_host_paths)"

  info "PASS: benchmark cache is ready"
  info "benchmark_cache_mode=shared"
  info "shared_postgis_container=$POSTGIS_CONTAINER"
  info "$shared_extensions"
  info "$shared_counts"
  info "claude_target=$claude_target"
  info "codex_target=$codex_target"
  info "gemini_target=$gemini_target"
  exit 0
fi

claude_plan="$(
  collect_plan \
    "$CLAUDE_WRAPPER" \
    MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=0
)"
codex_plan="$(
  collect_plan \
    "$CODEX_WRAPPER" \
    MCP_GEO_CODEX_LAUNCHER=docker \
    MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=0
)"
gemini_plan="$(
  collect_plan \
    "$GEMINI_WRAPPER" \
    MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=0
)"

claude_target="$(plan_value "$claude_plan" postgis_target_container)"
claude_manage="$(plan_value "$claude_plan" manage_postgis_container)"
claude_container="$(plan_value "$claude_plan" postgis_container_name)"
claude_network="$(plan_value "$claude_plan" network)"
codex_target="$(plan_value "$codex_plan" postgis_target_container)"
codex_manage="$(plan_value "$codex_plan" manage_postgis_container)"
codex_container="$(plan_value "$codex_plan" postgis_container_name)"
codex_network="$(plan_value "$codex_plan" network)"
gemini_target="$(plan_value "$gemini_plan" postgis_target_container)"
gemini_manage="$(plan_value "$gemini_plan" manage_postgis_container)"
gemini_container="$(plan_value "$gemini_plan" postgis_container_name)"
gemini_network="$(plan_value "$gemini_plan" network)"

[[ "$claude_target" == "$claude_container" ]] || fail "Claude wrapper is not targeting its dedicated PostGIS sidecar"
[[ "$codex_target" == "$codex_container" ]] || fail "Codex wrapper is not targeting its dedicated PostGIS sidecar"
[[ "$gemini_target" == "$gemini_container" ]] || fail "Gemini wrapper is not targeting its dedicated PostGIS sidecar"
[[ "$claude_manage" == "true" ]] || fail "Claude wrapper unexpectedly reuses an external PostGIS container"
[[ "$codex_manage" == "true" ]] || fail "Codex wrapper unexpectedly reuses an external PostGIS container"
[[ "$gemini_manage" == "true" ]] || fail "Gemini wrapper unexpectedly reuses an external PostGIS container"

assert_same_value "landis_host_data_root" \
  "$(plan_value "$claude_plan" landis_host_data_root)" \
  "$(plan_value "$codex_plan" landis_host_data_root)" \
  "$(plan_value "$gemini_plan" landis_host_data_root)"
assert_same_value "addressbase_xref_host_path" \
  "$(plan_value "$claude_plan" addressbase_xref_host_path)" \
  "$(plan_value "$codex_plan" addressbase_xref_host_path)" \
  "$(plan_value "$gemini_plan" addressbase_xref_host_path)"
assert_same_value "ons_geo_host_cache_dir" \
  "$(plan_value "$claude_plan" ons_geo_host_cache_dir)" \
  "$(plan_value "$codex_plan" ons_geo_host_cache_dir)" \
  "$(plan_value "$gemini_plan" ons_geo_host_cache_dir)"
assert_same_value "ons_geo_host_cache_index_path" \
  "$(plan_value "$claude_plan" ons_geo_host_cache_index_path)" \
  "$(plan_value "$codex_plan" ons_geo_host_cache_index_path)" \
  "$(plan_value "$gemini_plan" ons_geo_host_cache_index_path)"
assert_same_value "boundary_runs_search_host_paths" \
  "$(plan_value "$claude_plan" boundary_runs_search_host_paths)" \
  "$(plan_value "$codex_plan" boundary_runs_search_host_paths)" \
  "$(plan_value "$gemini_plan" boundary_runs_search_host_paths)"

for container in "$claude_target" "$codex_target" "$gemini_target"; do
  require_running_container "$container"
done

for container in "$claude_target" "$codex_target" "$gemini_target"; do
  publish_port="$(host_port_binding "$container")"
  [[ -z "$publish_port" ]] || fail "PostGIS sidecar publishes host port $publish_port but benchmark parity expects Docker-network-only access: $container"
done

claude_extensions="$(extension_summary "$claude_target")"
codex_extensions="$(extension_summary "$codex_target")"
gemini_extensions="$(extension_summary "$gemini_target")"
require_extensions "$claude_target" "$claude_extensions"
require_extensions "$codex_target" "$codex_extensions"
require_extensions "$gemini_target" "$gemini_extensions"

claude_counts="$(count_summary "$claude_target")"
codex_counts="$(count_summary "$codex_target")"
gemini_counts="$(count_summary "$gemini_target")"

for key in boundary_datasets admin_boundaries routing_graph_metadata landis_products; do
  assert_same_value "$key" \
    "$(count_value "$claude_counts" "$key")" \
    "$(count_value "$codex_counts" "$key")" \
    "$(count_value "$gemini_counts" "$key")"
done

info "PASS: benchmark cache is ready"
info "benchmark_cache_mode=isolated"
info "claude_target=$claude_target"
info "codex_target=$codex_target"
info "gemini_target=$gemini_target"
info "claude_network=$claude_network"
info "codex_network=$codex_network"
info "gemini_network=$gemini_network"
info "boundary_datasets=$(count_value "$claude_counts" boundary_datasets)"
info "admin_boundaries=$(count_value "$claude_counts" admin_boundaries)"
info "routing_graph_metadata=$(count_value "$claude_counts" routing_graph_metadata)"
info "landis_products=$(count_value "$claude_counts" landis_products)"

if [[ "$(count_value "$claude_counts" routing_graph_metadata)" == "0" ]]; then
  info "note=route graph is empty across all dedicated sidecars; route-computation scenarios will measure the same readiness gap unless you seed a graph explicitly"
fi
if [[ "$(count_value "$claude_counts" admin_boundaries)" == "0" ]]; then
  info "note=boundary cache is empty across all dedicated sidecars; admin-boundary scenarios will rely on live fallbacks rather than cached geometry"
fi
