from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _plan_value(output: str, key: str) -> str:
    for line in output.splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1]
    raise AssertionError(f"missing plan value: {key}")


def _isolated_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["MCP_GEO_ENV_FILE"] = str(tmp_path / "missing.env")
    for key in (
        "LANDIS_LOCAL_DATA_ROOT",
        "LANDIS_PORTAL_ARCHIVE_DIR",
        "LANDIS_FULL_RELEASE_ARCHIVE_DIR",
        "ADDRESSBASE_PREMIUM_XREF_PATH",
        "ADDRESSBASE_PREMIUM_DUCKDB_THREADS",
        "ADDRESSBASE_PREMIUM_DUCKDB_MEMORY_LIMIT",
        "BOUNDARY_RUNS_DIR",
        "BOUNDARY_RUNS_SEARCH_DIRS",
        "MCP_GEO_LANDIS_DATA_ROOT",
    ):
        env.pop(key, None)
    return env


def test_mcp_docker_local_plan_enables_landis_mount_for_existing_data_root(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    landis_root = tmp_path / "Data"
    landis_root.mkdir()

    _write_executable(
        fake_docker,
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "info" ]]; then
  exit 0
fi
exit 1
""",
    )

    env = _isolated_env(tmp_path)
    env["MCP_GEO_DOCKER_BIN"] = str(fake_docker)
    env["MCP_GEO_DOCKER_PLAN_ONLY"] = "1"
    env["MCP_GEO_POSTGIS_REUSE_DEVCONTAINER"] = "0"
    env["MCP_GEO_LANDIS_DATA_ROOT"] = str(landis_root)

    proc = subprocess.run(
        ["bash", str(wrapper)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _plan_value(proc.stdout, "landis_host_data_root") == str(landis_root)
    assert _plan_value(proc.stdout, "landis_container_data_root") == "/landis-data"
    assert _plan_value(proc.stdout, "landis_mount_enabled") == "true"


def test_mcp_docker_local_plan_hydrates_path_settings_from_dotenv(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    env_file = tmp_path / "wrapper.env"
    landis_root = tmp_path / "ExtSSD-Data" / "Data"
    boundary_root = landis_root / "boundary_runs"
    addressbase_path = repo_root / "data" / "addressbase" / "xref_voa_os.parquet"
    os_api_key_file = tmp_path / "os_api_key.txt"

    boundary_root.mkdir(parents=True)
    landis_root.mkdir(exist_ok=True)
    os_api_key_file.write_text("test-key\n", encoding="utf-8")
    env_file.write_text(
        "\n".join(
            [
                f"OS_API_KEY_FILE={os_api_key_file}",
                f"LANDIS_LOCAL_DATA_ROOT={landis_root}",
                f"BOUNDARY_RUNS_SEARCH_DIRS={landis_root}",
                "ADDRESSBASE_PREMIUM_XREF_PATH=data/addressbase/xref_voa_os.parquet",
            ]
        ),
        encoding="utf-8",
    )

    _write_executable(
        fake_docker,
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "info" ]]; then
  exit 0
fi
exit 1
""",
    )

    env = _isolated_env(tmp_path)
    env["MCP_GEO_DOCKER_BIN"] = str(fake_docker)
    env["MCP_GEO_DOCKER_PLAN_ONLY"] = "1"
    env["MCP_GEO_POSTGIS_REUSE_DEVCONTAINER"] = "0"
    env["MCP_GEO_ENV_FILE"] = str(env_file)

    proc = subprocess.run(
        ["bash", str(wrapper)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _plan_value(proc.stdout, "landis_host_data_root") == str(landis_root)
    assert _plan_value(proc.stdout, "landis_mount_enabled") == "true"
    assert _plan_value(proc.stdout, "os_api_key_present") == "true"
    assert _plan_value(proc.stdout, "os_api_key_file_present") == "true"
    assert _plan_value(proc.stdout, "boundary_runs_mount_enabled") == "true"
    assert _plan_value(proc.stdout, "boundary_runs_search_host_paths") == str(landis_root)
    assert _plan_value(proc.stdout, "boundary_runs_search_container_paths") == str(landis_root)
    assert _plan_value(proc.stdout, "addressbase_xref_host_path") == str(addressbase_path)
    assert _plan_value(proc.stdout, "addressbase_xref_container_path") == (
        "/app/data/addressbase/xref_voa_os.parquet"
    )


def test_mcp_docker_local_plan_disables_landis_mount_when_root_missing(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    landis_root = tmp_path / "missing-data-root"

    _write_executable(
        fake_docker,
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "info" ]]; then
  exit 0
fi
exit 1
""",
    )

    env = _isolated_env(tmp_path)
    env["MCP_GEO_DOCKER_BIN"] = str(fake_docker)
    env["MCP_GEO_DOCKER_PLAN_ONLY"] = "1"
    env["MCP_GEO_POSTGIS_REUSE_DEVCONTAINER"] = "0"
    env["MCP_GEO_LANDIS_DATA_ROOT"] = str(landis_root)

    proc = subprocess.run(
        ["bash", str(wrapper)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _plan_value(proc.stdout, "landis_host_data_root") == str(landis_root)
    assert _plan_value(proc.stdout, "landis_mount_enabled") == "false"


def test_mcp_docker_local_plan_uses_dedicated_sidecar_defaults(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"

    _write_executable(
        fake_docker,
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "info" ]]; then
  exit 0
fi
exit 1
""",
    )

    env = _isolated_env(tmp_path)
    env["MCP_GEO_DOCKER_BIN"] = str(fake_docker)
    env["MCP_GEO_DOCKER_PLAN_ONLY"] = "1"
    env["MCP_GEO_POSTGIS_REUSE_DEVCONTAINER"] = "0"

    proc = subprocess.run(
        ["bash", str(wrapper)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _plan_value(proc.stdout, "network") == "mcp-geo-sidecar"
    assert _plan_value(proc.stdout, "postgis_container_name") == "mcp-geo-postgis-sidecar"
    assert _plan_value(proc.stdout, "postgis_volume") == "mcp-geo-postgis-sidecar"
    assert _plan_value(proc.stdout, "postgis_publish_port") == "0"


def test_mcp_docker_local_plan_enables_ons_geo_cache_mounts_when_present(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    cache_dir = tmp_path / "ons_geo_cache"
    index_path = tmp_path / "ons_geo_cache_index.json"
    cache_dir.mkdir()
    index_path.write_text("{}", encoding="utf-8")

    _write_executable(
        fake_docker,
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "info" ]]; then
  exit 0
fi
exit 1
""",
    )

    env = _isolated_env(tmp_path)
    env["MCP_GEO_DOCKER_BIN"] = str(fake_docker)
    env["MCP_GEO_DOCKER_PLAN_ONLY"] = "1"
    env["MCP_GEO_POSTGIS_REUSE_DEVCONTAINER"] = "0"
    env["MCP_GEO_HOST_ONS_GEO_CACHE_DIR"] = str(cache_dir)
    env["MCP_GEO_HOST_ONS_GEO_CACHE_INDEX_PATH"] = str(index_path)

    proc = subprocess.run(
        ["bash", str(wrapper)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _plan_value(proc.stdout, "ons_geo_host_cache_dir") == str(cache_dir)
    assert _plan_value(proc.stdout, "ons_geo_container_cache_dir") == "/app/data/cache/ons_geo"
    assert _plan_value(proc.stdout, "ons_geo_cache_mount_enabled") == "true"
    assert _plan_value(proc.stdout, "ons_geo_host_cache_index_path") == str(index_path)
    assert (
        _plan_value(proc.stdout, "ons_geo_container_cache_index_path")
        == "/app/resources/ons_geo_cache_index.json"
    )
    assert _plan_value(proc.stdout, "ons_geo_cache_index_mount_enabled") == "true"


def test_mcp_docker_local_plan_disables_ons_geo_cache_mounts_when_missing(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    cache_dir = tmp_path / "missing-cache"
    index_path = tmp_path / "missing-index.json"

    _write_executable(
        fake_docker,
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "info" ]]; then
  exit 0
fi
exit 1
""",
    )

    env = _isolated_env(tmp_path)
    env["MCP_GEO_DOCKER_BIN"] = str(fake_docker)
    env["MCP_GEO_DOCKER_PLAN_ONLY"] = "1"
    env["MCP_GEO_POSTGIS_REUSE_DEVCONTAINER"] = "0"
    env["MCP_GEO_HOST_ONS_GEO_CACHE_DIR"] = str(cache_dir)
    env["MCP_GEO_HOST_ONS_GEO_CACHE_INDEX_PATH"] = str(index_path)

    proc = subprocess.run(
        ["bash", str(wrapper)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _plan_value(proc.stdout, "ons_geo_host_cache_dir") == str(cache_dir)
    assert _plan_value(proc.stdout, "ons_geo_cache_mount_enabled") == "false"
    assert _plan_value(proc.stdout, "ons_geo_host_cache_index_path") == str(index_path)
    assert _plan_value(proc.stdout, "ons_geo_cache_index_mount_enabled") == "false"


def test_mcp_docker_local_plan_mounts_relative_boundary_runs_dir_from_repo(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    boundary_runs_dir = repo_root / "data" / "boundary_runs"
    created = False

    if not boundary_runs_dir.exists():
        boundary_runs_dir.mkdir(parents=True)
        created = True

    try:
        _write_executable(
            fake_docker,
            """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "info" ]]; then
  exit 0
fi
exit 1
""",
        )

        env = _isolated_env(tmp_path)
        env["MCP_GEO_DOCKER_BIN"] = str(fake_docker)
        env["MCP_GEO_DOCKER_PLAN_ONLY"] = "1"
        env["MCP_GEO_POSTGIS_REUSE_DEVCONTAINER"] = "0"

        proc = subprocess.run(
            ["bash", str(wrapper)],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        if created:
            boundary_runs_dir.rmdir()

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _plan_value(proc.stdout, "boundary_runs_mount_enabled") == "true"
    assert _plan_value(proc.stdout, "boundary_runs_primary_host_path") == str(boundary_runs_dir)
    assert _plan_value(proc.stdout, "boundary_runs_primary_container_path") == (
        "/app/data/boundary_runs"
    )
