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

    # On macOS, prefer the repo venv if present to avoid missing deps.
    if sys.platform == "darwin":
        venv_py = _repo_root() / ".venv" / "bin" / "python"
        if venv_py.exists():
            return str(venv_py)

    # On Linux (devcontainer) and other platforms, `sys.executable` should be
    # the python with dependencies installed.
    return sys.executable


def _python_has_module(python: str, module: str) -> bool:
    probe = subprocess.run(
        [python, "-c", f"import {module}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return probe.returncode == 0


def _user_site_for_python(python: str) -> str:
    probe = subprocess.run(
        [python, "-c", "import site; print(site.getusersitepackages() or '')"],
        capture_output=True,
        text=True,
        check=False,
    )
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


def main() -> int:
    python = _pick_python()
    _ensure_user_site(python)
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
