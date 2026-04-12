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


def test_gemini_launcher_sets_dedicated_docker_sidecar_defaults(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "scripts" / "gemini-mcp-local"
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

    env = os.environ.copy()
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
    assert _plan_value(proc.stdout, "network") == "mcp-geo-gemini"
    assert _plan_value(proc.stdout, "postgis_container_name") == "mcp-geo-postgis-gemini"
    assert _plan_value(proc.stdout, "postgis_volume") == "mcp-geo-postgis-gemini"
    assert _plan_value(proc.stdout, "postgis_reuse_devcontainer") == "0"
