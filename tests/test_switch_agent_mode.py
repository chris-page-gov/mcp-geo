from __future__ import annotations

import json
import plistlib
import subprocess
from pathlib import Path

from scripts.switch_agent_mode import switch_mode


def _run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_plist(path: Path, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        plistlib.dump({"CFBundleShortVersionString": version}, handle)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init")
    _run_git(repo, "config", "user.name", "Test User")
    _run_git(repo, "config", "user.email", "test@example.com")

    _write(repo / "AGENTS.md", "# Agents baseline\n")
    _write(repo / "CLAUDE.md", "# Claude baseline\n")
    _write(repo / "GEMINI.md", "# Gemini baseline\n")
    _write(repo / ".github" / "copilot-instructions.md", "# Copilot baseline\n")
    _write(repo / "CONTEXT.md", "# Context baseline\n\n## Verification Status\n\n- Green.\n")
    _write(repo / "PROGRESS.MD", "# Progress baseline\n")
    _write(repo / "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n### Added\n- Baseline.\n")
    _write(
        repo / "Plans" / "PLAN-Example.md",
        "# Example Plan\n\nDate: 2026-04-14\nStatus: in_progress\n",
    )
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-m", "Initial commit")
    return repo


def test_switch_obsidian_writes_root_adapters_and_manifest(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    app_path = tmp_path / "Obsidian.app"
    user_data_path = tmp_path / "userData"
    _write_plist(app_path / "Contents" / "Info.plist", "1.8.7")
    mode_manifest = repo / "data" / "agent_control" / "active_mode.json"

    manifest = switch_mode(
        repo,
        mode="obsidian",
        output_root=repo / "Obsidian" / "MCP Geo Agent Control",
        mode_manifest_path=mode_manifest,
        app_path=app_path,
        user_data_path=user_data_path,
        cli_path=None,
        require_cli=False,
    )

    assert manifest["mode"] == "obsidian"
    assert "Canonical vault instructions" in (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "@AGENTS.md" in (repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Compatibility Summary" in (repo / "CONTEXT.md").read_text(encoding="utf-8")
    saved = json.loads(mode_manifest.read_text(encoding="utf-8"))
    assert saved["cli_preflight"]["issues"][0]["code"] == "OBSIDIAN_VERSION_TOO_OLD"


def test_switch_classic_restores_head_versions(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    app_path = tmp_path / "Obsidian.app"
    user_data_path = tmp_path / "userData"
    _write_plist(app_path / "Contents" / "Info.plist", "1.8.7")
    mode_manifest = repo / "data" / "agent_control" / "active_mode.json"
    originals = {
        path: (repo / path).read_text(encoding="utf-8")
        for path in [
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            ".github/copilot-instructions.md",
            "CONTEXT.md",
            "PROGRESS.MD",
        ]
    }

    switch_mode(
        repo,
        mode="obsidian",
        output_root=repo / "Obsidian" / "MCP Geo Agent Control",
        mode_manifest_path=mode_manifest,
        app_path=app_path,
        user_data_path=user_data_path,
        cli_path=None,
        require_cli=False,
    )
    manifest = switch_mode(
        repo,
        mode="classic",
        output_root=repo / "Obsidian" / "MCP Geo Agent Control",
        mode_manifest_path=mode_manifest,
        app_path=app_path,
        user_data_path=user_data_path,
        cli_path=None,
        require_cli=False,
    )

    assert manifest["mode"] == "classic"
    for path, expected in originals.items():
        assert (repo / path).read_text(encoding="utf-8") == expected


def test_switch_obsidian_can_require_cli_readiness(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    app_path = tmp_path / "Obsidian.app"
    user_data_path = tmp_path / "userData"
    _write_plist(app_path / "Contents" / "Info.plist", "1.8.7")

    try:
        switch_mode(
            repo,
            mode="obsidian",
            output_root=repo / "Obsidian" / "MCP Geo Agent Control",
            mode_manifest_path=repo / "data" / "agent_control" / "active_mode.json",
            app_path=app_path,
            user_data_path=user_data_path,
            cli_path=None,
            require_cli=True,
        )
    except ValueError as exc:
        assert "OBSIDIAN_VERSION_TOO_OLD" in str(exc)
    else:
        raise AssertionError("Expected switch_mode to require a ready CLI preflight.")


def test_switch_obsidian_is_idempotent_for_generated_root_files(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    app_path = tmp_path / "Obsidian.app"
    user_data_path = tmp_path / "userData"
    _write_plist(app_path / "Contents" / "Info.plist", "1.8.7")
    mode_manifest = repo / "data" / "agent_control" / "active_mode.json"

    switch_mode(
        repo,
        mode="obsidian",
        output_root=repo / "Obsidian" / "MCP Geo Agent Control",
        mode_manifest_path=mode_manifest,
        app_path=app_path,
        user_data_path=user_data_path,
        cli_path=None,
        require_cli=False,
    )
    first = (repo / "AGENTS.md").read_text(encoding="utf-8")
    switch_mode(
        repo,
        mode="obsidian",
        output_root=repo / "Obsidian" / "MCP Geo Agent Control",
        mode_manifest_path=mode_manifest,
        app_path=app_path,
        user_data_path=user_data_path,
        cli_path=None,
        require_cli=False,
    )
    second = (repo / "AGENTS.md").read_text(encoding="utf-8")

    assert first == second
