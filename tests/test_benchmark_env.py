from __future__ import annotations

import json
from pathlib import Path

import scripts.benchmark_env as benchmark_env


def test_resolve_inherited_env_prefers_key_file_over_lower_priority_raw_key(
    monkeypatch,
    tmp_path: Path,
) -> None:
    claude_config = tmp_path / "claude_desktop_config.json"
    claude_config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "mcp-geo": {
                        "env": {
                            "OS_API_KEY_FILE": str(tmp_path / "os_api_key.txt"),
                            "ONS_LIVE_ENABLED": "true",
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    codex_config = tmp_path / "config.toml"
    codex_config.write_text(
        """
[mcp_servers.mcp-geo]
command = "python3"

[mcp_servers.mcp-geo.env]
OS_API_KEY = "raw-codex-key"
MCP_TOOLS_DEFAULT_TOOLSET = "starter"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(benchmark_env, "CLAUDE_DESKTOP_CONFIG_PATH", claude_config)
    monkeypatch.setattr(benchmark_env, "CODEX_CONFIG_PATH", codex_config)
    monkeypatch.setattr(benchmark_env, "DEFAULT_DOTENV_PATH", tmp_path / "missing.env")
    monkeypatch.setattr(benchmark_env, "_launchctl_getenv", lambda _key: None)

    resolved = benchmark_env.resolve_inherited_env({"DUMMY": "1"})

    assert resolved["OS_API_KEY_FILE"] == str(tmp_path / "os_api_key.txt")
    assert "OS_API_KEY" not in resolved
    assert resolved["ONS_LIVE_ENABLED"] == "true"
    assert resolved["MCP_TOOLS_DEFAULT_TOOLSET"] == "starter"


def test_resolve_inherited_env_prefers_explicit_env_key_over_client_fallbacks(
    monkeypatch,
    tmp_path: Path,
) -> None:
    claude_config = tmp_path / "claude_desktop_config.json"
    claude_config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "mcp-geo": {
                        "env": {
                            "OS_API_KEY_FILE": str(tmp_path / "os_api_key.txt"),
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(benchmark_env, "CLAUDE_DESKTOP_CONFIG_PATH", claude_config)
    monkeypatch.setattr(benchmark_env, "CODEX_CONFIG_PATH", tmp_path / "missing.toml")
    monkeypatch.setattr(benchmark_env, "DEFAULT_DOTENV_PATH", tmp_path / "missing.env")
    monkeypatch.setattr(benchmark_env, "_launchctl_getenv", lambda _key: None)

    resolved = benchmark_env.resolve_inherited_env({"OS_API_KEY": "shell-key"})

    assert resolved["OS_API_KEY"] == "shell-key"
    assert resolved["OS_API_KEY_FILE"] == str(tmp_path / "os_api_key.txt")


def test_resolve_inherited_env_prefers_launchctl_shared_key_file_and_toolset_defaults(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "OS_API_KEY=dotenv-key",
                "MCP_TOOLS_DEFAULT_TOOLSET=maps_tiles",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(benchmark_env, "CLAUDE_DESKTOP_CONFIG_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(benchmark_env, "CODEX_CONFIG_PATH", tmp_path / "missing.toml")
    monkeypatch.setattr(benchmark_env, "DEFAULT_DOTENV_PATH", dotenv_path)

    def fake_launchctl(key: str) -> str | None:
        mapping = {
            "OS_API_KEY_FILE": str(tmp_path / "launchctl_os_api_key.txt"),
            "MCP_TOOLS_DEFAULT_TOOLSET": "starter",
            "MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS": "ons_geo_lookup,property_tax",
        }
        return mapping.get(key)

    monkeypatch.setattr(benchmark_env, "_launchctl_getenv", fake_launchctl)

    resolved = benchmark_env.resolve_inherited_env({"DUMMY": "1"})

    assert resolved["OS_API_KEY_FILE"] == str(tmp_path / "launchctl_os_api_key.txt")
    assert "OS_API_KEY" not in resolved
    assert resolved["MCP_TOOLS_DEFAULT_TOOLSET"] == "starter"
    assert resolved["MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS"] == "ons_geo_lookup,property_tax"


def test_resolve_inherited_env_does_not_invent_docker_build_mode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(benchmark_env, "CLAUDE_DESKTOP_CONFIG_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(benchmark_env, "CODEX_CONFIG_PATH", tmp_path / "missing.toml")
    monkeypatch.setattr(benchmark_env, "DEFAULT_DOTENV_PATH", tmp_path / "missing.env")
    monkeypatch.setattr(benchmark_env, "_launchctl_getenv", lambda _key: None)

    resolved = benchmark_env.resolve_inherited_env({"DUMMY": "1"})

    assert "MCP_GEO_DOCKER_BUILD" not in resolved


def test_resolve_inherited_env_preserves_explicit_docker_build_mode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(benchmark_env, "CLAUDE_DESKTOP_CONFIG_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(benchmark_env, "CODEX_CONFIG_PATH", tmp_path / "missing.toml")
    monkeypatch.setattr(benchmark_env, "DEFAULT_DOTENV_PATH", tmp_path / "missing.env")
    monkeypatch.setattr(benchmark_env, "_launchctl_getenv", lambda _key: None)

    resolved = benchmark_env.resolve_inherited_env({"MCP_GEO_DOCKER_BUILD": "always"})

    assert resolved["MCP_GEO_DOCKER_BUILD"] == "always"
