from __future__ import annotations

import json
import os
import subprocess
import tomllib
from collections.abc import Mapping
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOTENV_PATH = REPO_ROOT / ".env"
CLAUDE_DESKTOP_CONFIG_PATH = (
    Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
)
CODEX_CONFIG_PATH = Path.home() / ".codex" / "config.toml"

FORWARDED_KEYS = (
    "OS_API_KEY",
    "OS_API_KEY_FILE",
    "ONS_LIVE_ENABLED",
    "STDIO_KEY",
    "BEARER_TOKENS",
    "MCP_GEO_DOCKER_BUILD",
    "MCP_TOOLS_DEFAULT_TOOLSET",
    "MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS",
    "MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS",
)


def _normalize_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.startswith("${env:") and text.endswith("}"):
        return None
    return text


def _launchctl_getenv(key: str) -> str | None:
    if os.name != "posix":
        return None
    try:
        proc = subprocess.run(
            ["launchctl", "getenv", key],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    return _normalize_value(proc.stdout)


def _dotenv_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = raw_value.strip()
        is_quoted = (
            len(value) >= 2
            and (
                (value.startswith('"') and value.endswith('"'))
                or (value.startswith("'") and value.endswith("'"))
            )
        )
        if is_quoted:
            value = value[1:-1]
        normalized = _normalize_value(value)
        if normalized is not None:
            values[key] = normalized
    return values


def _claude_desktop_env() -> dict[str, str]:
    if not CLAUDE_DESKTOP_CONFIG_PATH.exists():
        return {}
    try:
        payload = json.loads(CLAUDE_DESKTOP_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    servers = payload.get("mcpServers")
    if not isinstance(servers, dict):
        return {}
    server = servers.get("mcp-geo")
    if not isinstance(server, dict):
        return {}
    env = server.get("env")
    if not isinstance(env, dict):
        return {}
    return {
        key: normalized
        for key, value in env.items()
        if (normalized := _normalize_value(value)) is not None
    }


def _codex_env() -> dict[str, str]:
    if not CODEX_CONFIG_PATH.exists():
        return {}
    try:
        payload = tomllib.loads(CODEX_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    servers = payload.get("mcp_servers")
    if not isinstance(servers, dict):
        return {}
    server = servers.get("mcp-geo")
    if not isinstance(server, dict):
        return {}
    env = server.get("env")
    if not isinstance(env, dict):
        return {}
    return {
        key: normalized
        for key, value in env.items()
        if (normalized := _normalize_value(value)) is not None
    }


def resolve_inherited_env(base_env: Mapping[str, str] | None = None) -> dict[str, str]:
    source_env = dict(base_env or os.environ)
    env_values = {
        key: value
        for key in FORWARDED_KEYS
        if (value := _normalize_value(source_env.get(key))) is not None
    }
    launchctl_values = {
        key: value for key in FORWARDED_KEYS if (value := _launchctl_getenv(key)) is not None
    }
    dotenv_values = {
        key: value
        for key, value in _dotenv_values(DEFAULT_DOTENV_PATH).items()
        if key in FORWARDED_KEYS
    }
    claude_values = {
        key: value for key, value in _claude_desktop_env().items() if key in FORWARDED_KEYS
    }
    codex_values = {
        key: value for key, value in _codex_env().items() if key in FORWARDED_KEYS
    }
    sources: list[dict[str, str]] = [
        env_values,
        launchctl_values,
        dotenv_values,
        claude_values,
        codex_values,
    ]

    resolved: dict[str, str] = {}
    source_rank: dict[str, int] = {}
    for key in FORWARDED_KEYS:
        for idx, values in enumerate(sources):
            value = values.get(key)
            if value is None:
                continue
            resolved[key] = value
            source_rank[key] = idx
            break

    file_rank = source_rank.get("OS_API_KEY_FILE")
    key_rank = source_rank.get("OS_API_KEY")
    if file_rank is not None and key_rank is not None and key_rank > file_rank:
        resolved.pop("OS_API_KEY", None)
    return resolved


def resolved_process_env(base_env: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    env.update(resolve_inherited_env(base_env))
    return env
