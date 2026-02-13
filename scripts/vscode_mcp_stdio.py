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


def main() -> int:
    python = _pick_python()
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

