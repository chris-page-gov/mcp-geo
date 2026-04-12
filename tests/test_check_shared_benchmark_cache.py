from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _write_fake_wrapper(path: Path, container: str, network: str) -> None:
    _write_executable(
        path,
        f"""#!/usr/bin/env bash
set -euo pipefail
target="{container}"
manage="true"
if [[ "${{MCP_GEO_POSTGIS_REUSE_DEVCONTAINER:-0}}" == "1" ]]; then
  target="${{MCP_GEO_POSTGIS_REUSE_CONTAINER:-shared-postgis}}"
  manage="false"
fi
cat <<EOF
postgis_target_container=$target
manage_postgis_container=$manage
network={network}
postgis_container_name={container}
landis_host_data_root=/Volumes/ExtSSD-Data/Data
addressbase_xref_host_path=/repo/data/addressbase/xref_voa_os.parquet
ons_geo_host_cache_dir=/repo/data/cache/ons_geo
ons_geo_host_cache_index_path=/repo/resources/ons_geo_cache_index.json
boundary_runs_search_host_paths=/Volumes/ExtSSD-Data/Data
EOF
""",
    )


def _write_fake_docker(path: Path) -> None:
    port_binding_format = (
        '{{with index .HostConfig.PortBindings "5432/tcp"}}'
        "{{(index . 0).HostPort}}{{end}}"
    )
    script = """#!/usr/bin/env bash
set -euo pipefail
cmd="${1:-}"
shift || true
case "$cmd" in
  info)
    exit 0
    ;;
  container)
    sub="${1:-}"
    shift || true
    if [[ "$sub" != "inspect" ]]; then
      exit 1
    fi
    format=""
    if [[ "${1:-}" == "-f" ]]; then
      format="${2:-}"
      shift 2 || true
    fi
    container="${1:-}"
    case "$container" in
      mcp-geo-postgis-claude|mcp-geo-postgis-codex|mcp-geo-postgis-gemini|benchmark-postgis)
        ;;
      *)
        exit 1
        ;;
    esac
    if [[ -z "$format" ]]; then
      exit 0
    fi
    if [[ "$format" == "{{.State.Running}}" ]]; then
      printf "true\\n"
      exit 0
    fi
    if [[ "$format" == '__PORT_BINDING_FORMAT__' ]]; then
      env_key="FAKE_PORT_${container//-/_}"
      printf "%s" "${!env_key:-}"
      exit 0
    fi
    exit 1
    ;;
  exec)
    container="${1:-}"
    shift || true
    query="${*: -1}"
    if [[ "$query" == *"FROM pg_extension"* ]]; then
      printf "postgis=3.4.3\\npgrouting=3.6.2\\n"
      exit 0
    fi
    printf "%s\\n" \
      "boundary_datasets=0" \
      "admin_boundaries=0" \
      "routing_graph_metadata=0" \
      "landis_products=16"
    exit 0
    ;;
  *)
    exit 1
    ;;
esac
""".replace("__PORT_BINDING_FORMAT__", port_binding_format)
    _write_executable(
        path,
        script,
    )


def test_check_shared_benchmark_cache_passes_in_isolated_mode(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "check_shared_benchmark_cache.sh"
    fake_docker = tmp_path / "docker"
    claude = tmp_path / "claude-wrapper.sh"
    codex = tmp_path / "codex-wrapper.sh"
    gemini = tmp_path / "gemini-wrapper.sh"

    _write_fake_docker(fake_docker)
    _write_fake_wrapper(claude, "mcp-geo-postgis-claude", "mcp-geo-claude")
    _write_fake_wrapper(codex, "mcp-geo-postgis-codex", "mcp-geo-codex")
    _write_fake_wrapper(gemini, "mcp-geo-postgis-gemini", "mcp-geo-gemini")

    env = os.environ.copy()
    env["MCP_GEO_DOCKER_BIN"] = str(fake_docker)
    env["MCP_GEO_BENCHMARK_CLAUDE_WRAPPER"] = str(claude)
    env["MCP_GEO_BENCHMARK_CODEX_WRAPPER"] = str(codex)
    env["MCP_GEO_BENCHMARK_GEMINI_WRAPPER"] = str(gemini)

    proc = subprocess.run(
      ["bash", str(script)],
      cwd=repo_root,
      env=env,
      capture_output=True,
      text=True,
      check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS: benchmark cache is ready" in proc.stdout
    assert "benchmark_cache_mode=isolated" in proc.stdout
    assert "claude_target=mcp-geo-postgis-claude" in proc.stdout
    assert "codex_target=mcp-geo-postgis-codex" in proc.stdout
    assert "gemini_target=mcp-geo-postgis-gemini" in proc.stdout


def test_check_shared_benchmark_cache_passes_in_shared_mode(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "check_shared_benchmark_cache.sh"
    fake_docker = tmp_path / "docker"
    claude = tmp_path / "claude-wrapper.sh"
    codex = tmp_path / "codex-wrapper.sh"
    gemini = tmp_path / "gemini-wrapper.sh"

    _write_fake_docker(fake_docker)
    _write_fake_wrapper(claude, "mcp-geo-postgis-claude", "mcp-geo-claude")
    _write_fake_wrapper(codex, "mcp-geo-postgis-codex", "mcp-geo-codex")
    _write_fake_wrapper(gemini, "mcp-geo-postgis-gemini", "mcp-geo-gemini")

    env = os.environ.copy()
    env["MCP_GEO_DOCKER_BIN"] = str(fake_docker)
    env["MCP_GEO_BENCHMARK_CACHE_MODE"] = "shared"
    env["MCP_GEO_BENCHMARK_POSTGIS_CONTAINER"] = "benchmark-postgis"
    env["MCP_GEO_BENCHMARK_CLAUDE_WRAPPER"] = str(claude)
    env["MCP_GEO_BENCHMARK_CODEX_WRAPPER"] = str(codex)
    env["MCP_GEO_BENCHMARK_GEMINI_WRAPPER"] = str(gemini)

    proc = subprocess.run(
      ["bash", str(script)],
      cwd=repo_root,
      env=env,
      capture_output=True,
      text=True,
      check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS: benchmark cache is ready" in proc.stdout
    assert "benchmark_cache_mode=shared" in proc.stdout
    assert "shared_postgis_container=benchmark-postgis" in proc.stdout


def test_check_shared_benchmark_cache_rejects_published_sidecar_ports(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "check_shared_benchmark_cache.sh"
    fake_docker = tmp_path / "docker"
    claude = tmp_path / "claude-wrapper.sh"
    codex = tmp_path / "codex-wrapper.sh"
    gemini = tmp_path / "gemini-wrapper.sh"

    _write_fake_docker(fake_docker)
    _write_fake_wrapper(claude, "mcp-geo-postgis-claude", "mcp-geo-claude")
    _write_fake_wrapper(codex, "mcp-geo-postgis-codex", "mcp-geo-codex")
    _write_fake_wrapper(gemini, "mcp-geo-postgis-gemini", "mcp-geo-gemini")

    env = os.environ.copy()
    env["MCP_GEO_DOCKER_BIN"] = str(fake_docker)
    env["MCP_GEO_BENCHMARK_CLAUDE_WRAPPER"] = str(claude)
    env["MCP_GEO_BENCHMARK_CODEX_WRAPPER"] = str(codex)
    env["MCP_GEO_BENCHMARK_GEMINI_WRAPPER"] = str(gemini)
    env["FAKE_PORT_mcp_geo_postgis_codex"] = "5432"

    proc = subprocess.run(
      ["bash", str(script)],
      cwd=repo_root,
      env=env,
      capture_output=True,
      text=True,
      check=False,
    )

    assert proc.returncode == 1
    assert "publishes host port 5432" in proc.stderr
