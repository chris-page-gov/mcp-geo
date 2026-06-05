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
        "MCP_GEO_DOCKER_TRANSPORT",
        "MCP_GEO_HTTP_HOST",
        "MCP_GEO_HTTP_PORT",
        "MCP_GEO_HTTP_CONTAINER_PORT",
        "MCP_GEO_HTTP_CONTAINER_NAME",
        "MCP_GEO_HTTP_REPLACE",
        "MCP_HTTP_AUTH_MODE",
        "MCP_HTTP_AUTH_TOKEN",
        "MCP_HTTP_AUTH_TOKEN_FILE",
        "MCP_HTTP_JWT_HS256_SECRET",
        "MCP_HTTP_JWT_HS256_SECRET_FILE",
        "MCP_HTTP_JWT_ISSUER",
        "MCP_HTTP_JWT_AUDIENCE",
        "MCP_HTTP_JWT_REQUIRED_SCOPES",
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


def test_mcp_docker_local_http_plan_mounts_demo_caches_and_key(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    env_file = tmp_path / "demo.env"
    os_api_key_file = tmp_path / "os_api_key.txt"
    ons_dataset_cache = tmp_path / "cache" / "ons"
    ons_geo_cache = tmp_path / "cache" / "ons_geo"
    os_data_cache = tmp_path / "cache" / "os"
    ons_geo_index = tmp_path / "ons_geo_cache_index.json"

    os_api_key_file.write_text("test-key\n", encoding="utf-8")
    ons_dataset_cache.mkdir(parents=True)
    ons_geo_cache.mkdir(parents=True)
    os_data_cache.mkdir(parents=True)
    ons_geo_index.write_text("{}", encoding="utf-8")
    env_file.write_text(
        "\n".join(
            [
                f"OS_API_KEY_FILE={os_api_key_file}",
                f"ONS_DATASET_CACHE_DIR={ons_dataset_cache}",
                f"ONS_GEO_CACHE_DIR={ons_geo_cache}",
                f"ONS_GEO_CACHE_INDEX_PATH={ons_geo_index}",
                f"OS_DATA_CACHE_DIR={os_data_cache}",
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
    env["MCP_GEO_DOCKER_TRANSPORT"] = "http"
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
    assert _plan_value(proc.stdout, "transport_mode") == "http"
    assert _plan_value(proc.stdout, "http_bind_host") == "127.0.0.1"
    assert _plan_value(proc.stdout, "http_port") == "8000"
    assert _plan_value(proc.stdout, "os_api_key_present") == "true"
    assert _plan_value(proc.stdout, "os_api_key_file_present") == "true"
    assert _plan_value(proc.stdout, "ons_dataset_host_cache_dir") == str(ons_dataset_cache)
    assert _plan_value(proc.stdout, "ons_dataset_cache_mount_enabled") == "true"
    assert _plan_value(proc.stdout, "ons_geo_host_cache_dir") == str(ons_geo_cache)
    assert _plan_value(proc.stdout, "ons_geo_cache_mount_enabled") == "true"
    assert _plan_value(proc.stdout, "ons_geo_host_cache_index_path") == str(ons_geo_index)
    assert _plan_value(proc.stdout, "ons_geo_cache_index_mount_enabled") == "true"
    assert _plan_value(proc.stdout, "os_data_host_cache_dir") == str(os_data_cache)
    assert _plan_value(proc.stdout, "os_data_cache_mount_enabled") == "true"


def test_mcp_docker_local_env_file_hydrates_http_transport_defaults(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    env_file = tmp_path / "demo.env"
    env_file.write_text(
        "\n".join(
            [
                "MCP_GEO_DOCKER_TRANSPORT=http",
                "MCP_GEO_HTTP_HOST=0.0.0.0",
                "MCP_GEO_HTTP_PORT=8787",
                "MCP_GEO_HTTP_CONTAINER_PORT=9000",
                "MCP_GEO_HTTP_CONTAINER_NAME=custom-http",
                "MCP_GEO_HTTP_REPLACE=0",
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
    assert _plan_value(proc.stdout, "transport_mode") == "http"
    assert _plan_value(proc.stdout, "http_bind_host") == "0.0.0.0"
    assert _plan_value(proc.stdout, "http_port") == "8787"
    assert _plan_value(proc.stdout, "http_container_port") == "9000"
    assert _plan_value(proc.stdout, "http_container_name") == "custom-http"
    assert _plan_value(proc.stdout, "http_replace_container") == "0"


def test_mcp_docker_local_env_file_hydrates_documented_host_cache_vars(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    env_file = tmp_path / "demo.env"
    ons_dataset_cache = tmp_path / "host-cache" / "ons"
    ons_geo_cache = tmp_path / "host-cache" / "ons_geo"
    os_data_cache = tmp_path / "host-cache" / "os"
    ons_geo_index = tmp_path / "host-cache" / "ons_geo_cache_index.json"

    ons_dataset_cache.mkdir(parents=True)
    ons_geo_cache.mkdir(parents=True)
    os_data_cache.mkdir(parents=True)
    ons_geo_index.write_text("{}", encoding="utf-8")
    env_file.write_text(
        "\n".join(
            [
                f"MCP_GEO_HOST_ONS_DATASET_CACHE_DIR={ons_dataset_cache}",
                f"MCP_GEO_HOST_ONS_GEO_CACHE_DIR={ons_geo_cache}",
                f"MCP_GEO_HOST_ONS_GEO_CACHE_INDEX_PATH={ons_geo_index}",
                f"MCP_GEO_HOST_OS_DATA_CACHE_DIR={os_data_cache}",
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
    env["MCP_GEO_DOCKER_TRANSPORT"] = "http"
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
    assert _plan_value(proc.stdout, "ons_dataset_host_cache_dir") == str(ons_dataset_cache)
    assert _plan_value(proc.stdout, "ons_dataset_cache_mount_enabled") == "true"
    assert _plan_value(proc.stdout, "ons_geo_host_cache_dir") == str(ons_geo_cache)
    assert _plan_value(proc.stdout, "ons_geo_cache_mount_enabled") == "true"
    assert _plan_value(proc.stdout, "ons_geo_host_cache_index_path") == str(ons_geo_index)
    assert _plan_value(proc.stdout, "ons_geo_cache_index_mount_enabled") == "true"
    assert _plan_value(proc.stdout, "os_data_host_cache_dir") == str(os_data_cache)
    assert _plan_value(proc.stdout, "os_data_cache_mount_enabled") == "true"


def test_mcp_docker_local_env_file_hydrates_rc_flags(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    env_file = tmp_path / "demo.env"
    env_file.write_text(
        "\n".join(
            [
                "MCP_2026_RC_ENABLED=1",
                "MCP_PROTOCOL_2026_07_28_ENABLED=1",
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
    assert _plan_value(proc.stdout, "mcp_2026_rc_enabled") == "1"
    assert _plan_value(proc.stdout, "mcp_protocol_2026_07_28_enabled") == "1"


def test_mcp_docker_local_env_file_hydrates_http_auth_secrets(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-docker-local"
    fake_docker = tmp_path / "docker"
    env_file = tmp_path / "demo.env"
    token_file = tmp_path / "http_token.txt"
    jwt_secret_file = tmp_path / "jwt_secret.txt"

    token_file.write_text("static-demo-token\n", encoding="utf-8")
    jwt_secret_file.write_text("jwt-demo-secret\n", encoding="utf-8")
    env_file.write_text(
        "\n".join(
            [
                "MCP_HTTP_AUTH_MODE=hs256_jwt",
                f"MCP_HTTP_AUTH_TOKEN_FILE={token_file}",
                f"MCP_HTTP_JWT_HS256_SECRET_FILE={jwt_secret_file}",
                "MCP_HTTP_JWT_ISSUER=https://issuer.example.test",
                "MCP_HTTP_JWT_AUDIENCE=mcp-geo-demo",
                "MCP_HTTP_JWT_REQUIRED_SCOPES=geo:read",
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
    assert _plan_value(proc.stdout, "mcp_http_auth_mode") == "hs256_jwt"
    assert _plan_value(proc.stdout, "mcp_http_auth_token_present") == "true"
    assert _plan_value(proc.stdout, "mcp_http_jwt_hs256_secret_present") == "true"
    assert "static-demo-token" not in proc.stdout + proc.stderr
    assert "jwt-demo-secret" not in proc.stdout + proc.stderr


def test_mcp_http_demo_local_sets_http_defaults(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-http-demo-local"
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

    proc = subprocess.run(
        ["bash", str(wrapper)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _plan_value(proc.stdout, "transport_mode") == "http"
    assert _plan_value(proc.stdout, "network") == "mcp-geo-http-demo"
    assert _plan_value(proc.stdout, "postgis_container_name") == "mcp-geo-postgis-http-demo"
    assert _plan_value(proc.stdout, "postgis_volume") == "mcp-geo-postgis-http-demo"
    assert _plan_value(proc.stdout, "http_container_name") == "mcp-geo-http-demo"


def test_mcp_http_demo_local_honors_dotenv_overrides(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-http-demo-local"
    fake_docker = tmp_path / "docker"
    env_file = tmp_path / "demo.env"
    env_file.write_text(
        "\n".join(
            [
                "MCP_GEO_DOCKER_NETWORK=custom-http-network",
                "MCP_GEO_POSTGIS_CONTAINER=custom-postgis",
                "MCP_GEO_POSTGIS_VOLUME=custom-postgis-volume",
                "MCP_GEO_HTTP_CONTAINER_NAME=custom-http",
                "MCP_GEO_HTTP_PORT=8787",
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
    assert _plan_value(proc.stdout, "transport_mode") == "http"
    assert _plan_value(proc.stdout, "network") == "custom-http-network"
    assert _plan_value(proc.stdout, "postgis_container_name") == "custom-postgis"
    assert _plan_value(proc.stdout, "postgis_volume") == "custom-postgis-volume"
    assert _plan_value(proc.stdout, "http_container_name") == "custom-http"
    assert _plan_value(proc.stdout, "http_port") == "8787"


def test_mcp_http_demo_local_forces_http_over_dotenv_transport(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "mcp-http-demo-local"
    fake_docker = tmp_path / "docker"
    env_file = tmp_path / "demo.env"
    env_file.write_text(
        "\n".join(
            [
                "MCP_GEO_DOCKER_TRANSPORT=stdio",
                "MCP_GEO_HTTP_PORT=8787",
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
    assert _plan_value(proc.stdout, "transport_mode") == "http"
    assert _plan_value(proc.stdout, "http_port") == "8787"


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
