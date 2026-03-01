#!/usr/bin/env python3
"""VS Code MCP stdio entrypoint that works on both host macOS and Linux devcontainers.

VS Code runs MCP stdio servers by executing a command locally in the current
extension host environment (local window, SSH, devcontainer, etc).

This repo commonly has two different Python environments:
1) macOS host: a project venv at `.venv/` (recommended) with deps installed.
2) Linux devcontainer: system `python3` inside the container with deps installed
   via `postCreateCommand`.

If VS Code is opened locally on macOS, calling `python3 scripts/os-mcp` will
fail unless the global python has dependencies. This wrapper keeps the MCP
command stable by delegating to the appropriate interpreter.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _pick_python() -> str:
    # If we're already inside a venv, keep it.
    if os.environ.get("VIRTUAL_ENV"):
        return sys.executable

    # Prefer repo venv when present and likely healthier than global python.
    venv_py = _repo_root() / ".venv" / "bin" / "python"
    if venv_py.exists():
        if _python_has_module(str(venv_py), "loguru"):
            return str(venv_py)
        if not _python_has_module(sys.executable, "loguru"):
            return str(venv_py)

    # On Linux (devcontainer) and other platforms, `sys.executable` should be
    # the python with dependencies installed.
    return sys.executable


def _python_has_module(python: str, module: str) -> bool:
    try:
        probe = subprocess.run(
            [python, "-c", f"import {module}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return probe.returncode == 0


def _user_site_for_python(python: str) -> str:
    try:
        probe = subprocess.run(
            [python, "-c", "import site; print(site.getusersitepackages() or '')"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    if probe.returncode != 0:
        return ""
    return probe.stdout.strip()


def _ensure_user_site(python: str) -> None:
    # Keep startup deterministic: only relax PYTHONNOUSERSITE if the selected
    # interpreter cannot import required dependencies.
    if _python_has_module(python, "loguru"):
        return
    os.environ.pop("PYTHONNOUSERSITE", None)
    user_site = _user_site_for_python(python)
    if not user_site:
        return

    current = os.environ.get("PYTHONPATH", "")
    paths = [p for p in current.split(os.pathsep) if p]
    if user_site not in paths:
        paths.insert(0, user_site)
        os.environ["PYTHONPATH"] = os.pathsep.join(paths)


def _bootstrap_runtime_deps(python: str) -> bool:
    if _python_has_module(python, "loguru"):
        return True
    repo = _repo_root()
    cmd = [
        python,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "-e",
        str(repo),
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(
            (
                "mcp-geo: failed to execute bootstrap command "
                f"`{' '.join(cmd)}`: {exc}"
            ),
            file=sys.stderr,
        )
        return False
    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "").splitlines()[-3:]
        detail = " | ".join(tail) if tail else "unknown install error"
        print(
            (
                "mcp-geo: failed to bootstrap runtime dependencies with "
                f"`{' '.join(cmd)}`: {detail}"
            ),
            file=sys.stderr,
        )
        return False
    return _python_has_module(python, "loguru")


def main() -> int:
    python = _pick_python()
    _ensure_user_site(python)
    if not _python_has_module(python, "loguru"):
        _bootstrap_runtime_deps(python)
    if not _python_has_module(python, "loguru"):
        print(
            (
                "mcp-geo: runtime dependency `loguru` is still missing for "
                f"{python}. Run: {python} -m pip install -e ."
            ),
            file=sys.stderr,
        )
        return 2
    server = _repo_root() / "scripts" / "os-mcp"
    if not server.exists():
        print(f"mcp-geo: missing stdio entrypoint at {server}", file=sys.stderr)
        return 2

    # `-u` ensures unbuffered IO for stdio framing.
    argv = [python, "-u", str(server), *sys.argv[1:]]
    os.execv(python, argv)
    return 0  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
