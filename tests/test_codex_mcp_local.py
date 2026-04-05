from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def test_codex_launcher_falls_back_to_local_stdio_when_docker_unavailable(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "codex-mcp-local"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_local = tmp_path / "fake-local.sh"

    _write_executable(
        fake_docker,
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "info" ]]; then
  exit 1
fi
exit 1
""",
    )
    _write_executable(
        fake_local,
        """#!/usr/bin/env bash
set -euo pipefail
printf 'local-stdio\\n'
""",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["MCP_GEO_CODEX_LOCAL_WRAPPER"] = str(fake_local)
    env["MCP_GEO_CODEX_LAUNCHER"] = "auto"
    env.pop("REMOTE_CONTAINERS", None)
    env.pop("DEVCONTAINER", None)

    proc = subprocess.run(
        ["bash", str(wrapper)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.strip() == "local-stdio"


def test_codex_launcher_honors_explicit_docker_override(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "codex-mcp-local"
    fake_docker_wrapper = tmp_path / "fake-docker-wrapper.sh"

    _write_executable(
        fake_docker_wrapper,
        """#!/usr/bin/env bash
set -euo pipefail
printf 'docker-wrapper\\n'
""",
    )

    env = os.environ.copy()
    env["MCP_GEO_CODEX_DOCKER_WRAPPER"] = str(fake_docker_wrapper)
    env["MCP_GEO_CODEX_LAUNCHER"] = "docker"

    proc = subprocess.run(
        ["bash", str(wrapper)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.strip() == "docker-wrapper"


def test_codex_launcher_sets_dedicated_docker_sidecar_defaults(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "codex-mcp-local"
    fake_docker_wrapper = tmp_path / "fake-docker-wrapper.sh"

    _write_executable(
        fake_docker_wrapper,
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "${MCP_GEO_DOCKER_NETWORK:-}"
printf '%s\\n' "${MCP_GEO_POSTGIS_CONTAINER:-}"
printf '%s\\n' "${MCP_GEO_POSTGIS_VOLUME:-}"
printf '%s\\n' "${MCP_GEO_POSTGIS_REUSE_DEVCONTAINER:-}"
""",
    )

    env = os.environ.copy()
    env["MCP_GEO_CODEX_DOCKER_WRAPPER"] = str(fake_docker_wrapper)
    env["MCP_GEO_CODEX_LAUNCHER"] = "docker"

    proc = subprocess.run(
        ["bash", str(wrapper)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.splitlines() == [
        "mcp-geo-codex",
        "mcp-geo-postgis-codex",
        "mcp-geo-postgis-codex",
        "auto",
    ]
