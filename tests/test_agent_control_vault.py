from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.agent_control_common import build_control_vault


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


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init")
    _run_git(repo, "config", "user.name", "Test User")
    _run_git(repo, "config", "user.email", "test@example.com")

    _write(repo / "AGENTS.md", "# Agents\n")
    _write(repo / "CONTEXT.md", "# Context\n\n## Verification Status\n\n- Baseline green.\n")
    _write(repo / "PROGRESS.MD", "# Progress\n\nValidated with `pytest -q`.\n")
    _write(
        repo / "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n### Added\n- Baseline.\n\n"
        "## [0.1.0] - 2026-01-01\n",
    )
    _write(
        repo / "Plans" / "PLAN-Example.md",
        "# Example Plan\n\nDate: 2026-04-14\nStatus: in_progress\n\n### Slice 1\n- Do work.\n",
    )
    _write(repo / "server" / "main.py", '"""App."""\n')
    _write(repo / "tools" / "sample.py", '"""Tool."""\n')
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-m", "Initial commit")
    return repo


def test_build_control_vault_creates_curated_and_generated_notes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    output_root = repo / "Obsidian" / "MCP Geo Agent Control"
    manifest_path = repo / "data" / "agent_control" / "control_vault_manifest.json"

    manifest = build_control_vault(repo, output_root=output_root, manifest_path=manifest_path)

    assert (output_root / "00 Home" / "00 - Agent Home.md").exists()
    assert (output_root / "10 State" / "Current Focus.md").exists()
    assert (output_root / "20 Generated" / "Repo Map Digest.md").exists()
    assert manifest["curated_notes"]
    assert manifest["generated_notes"]

    saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved_manifest["generated_notes"][0]["path"] == "20 Generated/Repo Map Digest.md"


def test_build_control_vault_preserves_curated_notes_on_rebuild(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    output_root = repo / "Obsidian" / "MCP Geo Agent Control"
    manifest_path = repo / "data" / "agent_control" / "control_vault_manifest.json"

    build_control_vault(repo, output_root=output_root, manifest_path=manifest_path)

    curated_path = output_root / "10 State" / "Current Focus.md"
    curated_path.write_text("# Current Focus\n\nCustom note.\n", encoding="utf-8")

    build_control_vault(repo, output_root=output_root, manifest_path=manifest_path)

    assert curated_path.read_text(encoding="utf-8") == "# Current Focus\n\nCustom note.\n"


def test_build_control_vault_refreshes_generated_notes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    output_root = repo / "Obsidian" / "MCP Geo Agent Control"
    manifest_path = repo / "data" / "agent_control" / "control_vault_manifest.json"

    build_control_vault(repo, output_root=output_root, manifest_path=manifest_path)
    release_note = output_root / "20 Generated" / "Release Summary.md"
    before = release_note.read_text(encoding="utf-8")

    _write(
        repo / "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n### Added\n- Updated release note.\n\n"
        "## [0.1.0] - 2026-01-01\n",
    )

    build_control_vault(repo, output_root=output_root, manifest_path=manifest_path)
    after = release_note.read_text(encoding="utf-8")

    assert before != after
    assert "Updated release note." in after


def test_build_control_vault_keeps_multiline_changelog_bullets_intact(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    output_root = repo / "Obsidian" / "MCP Geo Agent Control"
    manifest_path = repo / "data" / "agent_control" / "control_vault_manifest.json"

    _write(
        repo / "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n### Added\n"
        "- Added a long wrapped item\n"
        "  that continues on the next line.\n\n"
        "## [0.1.0] - 2026-01-01\n",
    )

    build_control_vault(repo, output_root=output_root, manifest_path=manifest_path)
    release_note = output_root / "20 Generated" / "Release Summary.md"
    rendered = release_note.read_text(encoding="utf-8")

    assert "Added a long wrapped item that continues on the next line." in rendered
