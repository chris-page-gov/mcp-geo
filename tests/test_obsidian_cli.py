from __future__ import annotations

import plistlib
import subprocess
from pathlib import Path

from scripts.agent_control_common import build_control_vault
from scripts.obsidian_cli import preflight, version_at_least
from scripts.validate_agent_control import validate_control_vault


def _write_plist(path: Path, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        plistlib.dump({"CFBundleShortVersionString": version}, handle)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _init_minimal_repo(repo_root: Path) -> None:
    _write(repo_root / "AGENTS.md", "# Agents\n")
    _write(repo_root / "CLAUDE.md", "# Claude\n")
    _write(repo_root / "GEMINI.md", "# Gemini\n")
    _write(repo_root / ".github" / "copilot-instructions.md", "# Copilot\n")
    _write(repo_root / "CONTEXT.md", "# Context\n\n## Verification Status\n\n- Green.\n")
    _write(repo_root / "PROGRESS.MD", "# Progress\n\nValidated with `pytest -q`.\n")
    _write(
        repo_root / "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n### Added\n- Baseline.\n\n"
        "## [0.1.0] - 2026-01-01\n",
    )
    _write(repo_root / "Plans" / "PLAN-Example.md", "# Example Plan\n")


def test_version_at_least_uses_minimum_cli_version() -> None:
    assert not version_at_least("1.8.7")
    assert version_at_least("1.12.7")
    assert version_at_least("1.13.0")


def test_preflight_reports_version_too_old_before_cli_checks(tmp_path: Path) -> None:
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    app_path = tmp_path / "Obsidian.app"
    _write_plist(app_path / "Contents" / "Info.plist", "1.8.7")

    result = preflight(vault_path, app_path=app_path)

    assert result["ready"] is False
    assert result["issues"][0]["code"] == "OBSIDIAN_VERSION_TOO_OLD"


def test_preflight_requires_registered_cli_when_version_is_new_enough(tmp_path: Path) -> None:
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    app_path = tmp_path / "Obsidian.app"
    _write_plist(app_path / "Contents" / "Info.plist", "1.12.7")
    bundled = app_path / "Contents" / "MacOS" / "obsidian-cli"
    bundled.parent.mkdir(parents=True, exist_ok=True)
    bundled.write_text("", encoding="utf-8")

    result = preflight(vault_path, app_path=app_path)

    codes = [issue["code"] for issue in result["issues"]]
    assert "OBSIDIAN_CLI_NOT_REGISTERED" in codes


def test_preflight_runs_help_read_and_search_with_registered_cli(
    tmp_path: Path,
    monkeypatch,
) -> None:
    vault_path = tmp_path / "vault"
    _init_minimal_repo(tmp_path)
    build_control_vault(tmp_path, output_root=vault_path, manifest_path=tmp_path / "manifest.json")
    app_path = tmp_path / "Obsidian.app"
    _write_plist(app_path / "Contents" / "Info.plist", "1.12.7")
    bundled = app_path / "Contents" / "MacOS" / "obsidian-cli"
    bundled.parent.mkdir(parents=True, exist_ok=True)
    bundled.write_text("", encoding="utf-8")
    cli_path = tmp_path / "bin" / "obsidian"
    cli_path.parent.mkdir(parents=True, exist_ok=True)
    cli_path.write_text("", encoding="utf-8")

    def fake_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        if cmd[1] == "help":
            return subprocess.CompletedProcess(cmd, 0, stdout="help output", stderr="")
        if cmd[1] == "read":
            return subprocess.CompletedProcess(cmd, 0, stdout="# Agent Home", stderr="")
        if cmd[1] == "search":
            return subprocess.CompletedProcess(cmd, 0, stdout="Agent Home result", stderr="")
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr("scripts.obsidian_cli.subprocess.run", fake_run)

    result = preflight(vault_path, app_path=app_path, cli_path=cli_path)

    assert result["ready"] is True
    assert result["help_ok"] is True
    assert result["read_ok"] is True
    assert result["search_ok"] is True


def test_validate_control_vault_merges_manifest_and_cli_issues(tmp_path: Path) -> None:
    vault_path = tmp_path / "vault"
    manifest_path = tmp_path / "manifest.json"
    _init_minimal_repo(tmp_path)
    build_control_vault(tmp_path, output_root=vault_path, manifest_path=manifest_path)
    app_path = tmp_path / "Obsidian.app"
    _write_plist(app_path / "Contents" / "Info.plist", "1.8.7")

    issues = validate_control_vault(
        tmp_path,
        vault_path,
        manifest_path,
        check_cli=True,
        app_path=app_path,
        cli_path=None,
        mode_manifest_path=None,
    )

    assert any(issue["code"] == "OBSIDIAN_VERSION_TOO_OLD" for issue in issues)


def test_validate_control_vault_allows_live_classic_tracker_updates(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _run_git(repo_root, "init")
    _run_git(repo_root, "config", "user.name", "Test User")
    _run_git(repo_root, "config", "user.email", "test@example.com")
    _init_minimal_repo(repo_root)
    _run_git(repo_root, "add", ".")
    _run_git(repo_root, "commit", "-m", "Initial commit")

    vault_path = repo_root / "vault"
    manifest_path = repo_root / "manifest.json"
    build_control_vault(repo_root, output_root=vault_path, manifest_path=manifest_path)
    _write(
        repo_root / "data" / "agent_control" / "active_mode.json",
        '{\n  "mode": "classic",\n  "root_files": [\n'
        '    "AGENTS.md",\n    "CLAUDE.md",\n    "GEMINI.md",\n'
        '    ".github/copilot-instructions.md",\n    "CONTEXT.md",\n    "PROGRESS.MD"\n'
        "  ]\n}\n",
    )

    _write(
        repo_root / "CONTEXT.md",
        "# Context\n\n## Current Focus\n\n- Updated during the live workstream.\n",
    )
    _write(
        repo_root / "PROGRESS.MD",
        "# Progress\n\n- Tracker updated after the last milestone.\n",
    )

    issues = validate_control_vault(
        repo_root,
        vault_path,
        manifest_path,
        check_cli=False,
        app_path=tmp_path / "Obsidian.app",
        cli_path=None,
        mode_manifest_path=repo_root / "data" / "agent_control" / "active_mode.json",
    )

    assert not any(issue["code"] == "CLASSIC_RESTORE_MISMATCH" for issue in issues)
    assert not any(issue["code"] == "CLASSIC_TRACKER_SHIM_ACTIVE" for issue in issues)
