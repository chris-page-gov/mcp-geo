import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from server.main import app


def _bash_works(command: str) -> bool:
    normalized = command.replace("\\", "/").lower()
    if normalized.endswith("/windows/system32/bash.exe"):
        return False
    try:
        proc = subprocess.run(
            [command, "-lc", "exit 0"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _git_bash_dir() -> str | None:
    for candidate in (
        Path("C:/Program Files/Git/bin/bash.exe"),
        Path("C:/Program Files/Git/usr/bin/bash.exe"),
        Path.home() / "AppData/Local/Programs/Git/bin/bash.exe",
    ):
        if candidate.exists() and _bash_works(str(candidate)):
            return str(candidate.parent)
    return None


def _git_tool_dirs() -> list[str]:
    candidates = [
        Path("C:/Program Files/Git/usr/bin"),
        Path("C:/Program Files/Git/mingw64/bin"),
        Path.home() / "AppData/Local/Programs/Git/usr/bin",
        Path.home() / "AppData/Local/Programs/Git/mingw64/bin",
    ]
    return [str(path) for path in candidates if path.exists()]


def _usable_bash_command() -> str | None:
    git_bash_dir = _git_bash_dir()
    if git_bash_dir:
        return str(Path(git_bash_dir) / "bash.exe")

    bash = shutil.which("bash")
    if bash and _bash_works(bash):
        return bash
    return None


def _script_rewrite(command: str, bash: str) -> list[str] | None:
    path = Path(command)
    if not path.exists() or not path.is_file():
        return None
    try:
        first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
    except OSError:
        return None
    if not first_line:
        return None
    shebang = first_line[0].strip().lower()
    if not shebang.startswith("#!"):
        return None
    if "python" in shebang:
        return [sys.executable, str(path)]
    if "bash" in shebang or shebang.endswith("/sh") or " sh" in shebang:
        return [bash, str(path)]
    return None


@pytest.fixture
def mock_os_client(monkeypatch):
    import tools.os_common as os_common
    handlers: dict[str, Callable[[str, dict[str, Any]], tuple[int, dict[str, Any]]]] = {}
    # Avoid importlib.reload(os_common): tools import the shared client instance at import-time.
    # Reloading would create a new client object and break those references.
    monkeypatch.setattr(os_common.settings, "OS_API_KEY", "test-key", raising=False)
    os_common.client.api_key = "test-key"

    def fake_get_json(url: str, params: dict[str, Any] | None = None):  # type: ignore[override]
        for key, fn in handlers.items():
            if key in url:
                return fn(url, params or {})
        return 200, {"results": []}

    monkeypatch.setattr(os_common.client, "get_json", fake_get_json)
    return handlers

@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def disable_circuit_breaker(monkeypatch):
    from server.config import settings
    monkeypatch.setattr(settings, "CIRCUIT_BREAKER_ENABLED", False, raising=False)


@pytest.fixture(autouse=True)
def reset_rate_limit_state(monkeypatch):
    from server import main
    from server.config import settings

    monkeypatch.setattr(settings, "RATE_LIMIT_BYPASS", False, raising=False)
    with main._rate_lock:
        main._rate_counters.clear()


@pytest.fixture(autouse=True)
def reset_default_toolset_config(monkeypatch):
    from server.config import settings

    for name in (
        "MCP_TOOLS_DEFAULT_TOOLSET",
        "MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS",
        "MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS",
    ):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.setattr(settings, name, "", raising=False)


@pytest.fixture(autouse=True)
def prefer_usable_bash(monkeypatch):
    bash = _usable_bash_command()
    if not bash or (Path(bash).name.lower() == "bash" and _bash_works(bash)):
        return

    shim_dir = Path(tempfile.mkdtemp(prefix="pytest-bash-shims-"))
    python3_shim = shim_dir / "python3"
    python3_shim.write_text(
        "#!/usr/bin/env bash\n"
        f'exec "{sys.executable.replace("\\", "/")}" "$@"\n',
        encoding="utf-8",
    )
    python3_shim.chmod(0o755)

    original_run = subprocess.run

    def _patched_run(*popenargs, **kwargs):
        if popenargs:
            command = popenargs[0]
            if isinstance(command, (list, tuple)) and command:
                rewritten = None
                if command[0] == "bash":
                    rewritten = [bash, *command[1:]]
                elif isinstance(command[0], str):
                    prefix = _script_rewrite(command[0], bash)
                    if prefix is not None:
                        rewritten = [*prefix, *command[1:]]
                if rewritten is not None:
                    command = rewritten
                    popenargs = (command, *popenargs[1:])
                env = dict(kwargs.get("env") or os.environ)
                env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', '')}"
                env["MCP_GEO_BASH_BIN"] = bash
                kwargs["env"] = env
        return original_run(*popenargs, **kwargs)

    monkeypatch.setattr(subprocess, "run", _patched_run)


@pytest.fixture(autouse=True)
def prefer_git_toolchain(monkeypatch):
    extra_dirs = _git_tool_dirs()
    if not extra_dirs:
        return
    current_path = os.environ.get("PATH", "")
    merged = os.pathsep.join([*extra_dirs, current_path]) if current_path else os.pathsep.join(extra_dirs)
    monkeypatch.setenv("PATH", merged)
