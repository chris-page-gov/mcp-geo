from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _run_wrapper(
    tmp_path: Path,
    script_name: str,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_executable(
        bin_dir / "uv",
        "#!/usr/bin/env bash\n"
        "printf 'argc=%s\\n' \"$#\"\n"
        "for arg in \"$@\"; do\n"
        "  printf 'arg=%s\\n' \"$arg\"\n"
        "done\n",
    )
    env = os.environ.copy()
    env["MCP_GEO_LOCAL_TOOL_MODE"] = "uv"
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    return subprocess.run(
        [str(ROOT_DIR / "scripts" / script_name), *args],
        cwd=ROOT_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_ruff_local_zero_arg_dispatches_via_uv(tmp_path: Path) -> None:
    result = _run_wrapper(tmp_path, "ruff-local")

    assert result.returncode == 0
    assert "mcp-geo: ruff via uv run" in result.stderr
    assert "arg=run" in result.stdout
    assert "arg=--with" in result.stdout
    assert "arg=check" in result.stdout
    assert "arg=ruff" in result.stdout
    assert "arg=server/mcp/tools.py" in result.stdout


def test_mypy_local_zero_arg_dispatches_via_uv(tmp_path: Path) -> None:
    result = _run_wrapper(tmp_path, "mypy-local")

    assert result.returncode == 0
    assert "mcp-geo: mypy via uv run" in result.stderr
    assert "arg=run" in result.stdout
    assert "arg=--with" in result.stdout
    assert "arg=--follow-imports=skip" in result.stdout
    assert "arg=mypy" in result.stdout
    assert "arg=types-requests" in result.stdout
    assert "arg=server/mcp/resource_catalog.py" in result.stdout


def test_mypy_local_forwards_args_via_uv(tmp_path: Path) -> None:
    result = _run_wrapper(
        tmp_path,
        "mypy-local",
        "--follow-imports=skip",
        "server/security.py",
    )

    assert result.returncode == 0
    assert "arg=--follow-imports=skip" in result.stdout
    assert "arg=server/security.py" in result.stdout
    assert "arg=server/mcp/resource_catalog.py" not in result.stdout


def test_ruff_local_path_args_prepend_check_via_uv(tmp_path: Path) -> None:
    result = _run_wrapper(tmp_path, "ruff-local", "server/security.py")

    assert result.returncode == 0
    assert "arg=check" in result.stdout
    assert "arg=server/security.py" in result.stdout
