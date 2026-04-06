from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.obsidian_kb_common import build_vault, validate_manifest


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
    _run_git(repo, "remote", "add", "origin", "https://github.com/example/mcp-geo.git")

    _write(repo / "README.md", "# Repo\n")
    _write(repo / "AGENTS.md", "# Agents\n")
    _write(repo / "CONTEXT.md", "# Context\n")
    _write(repo / "PROGRESS.MD", "# Progress\n")
    _write(repo / "CHANGELOG.md", "# Changelog\n")
    _write(repo / "RELEASE_NOTES" / "0.1.0.md", "# Release 0.1.0\n")
    _write(repo / "server" / "main.py", '"""HTTP entrypoint."""\n')
    _write(repo / "server" / "mcp" / "tools.py", '"""MCP tools."""\n')
    _write(repo / "tools" / "os_places.py", '"""Places tool."""\n')
    _write(repo / "scripts" / "trace_session.py", '"""Trace session helper."""\n')
    _write(repo / "ui" / "demo.html", "<title>Demo</title>\n")
    _write(repo / "playground" / "src" / "App.svelte", "<script></script>\n")
    _write(repo / "resources" / "catalog.json", '{"name": "catalog"}\n')
    _write(repo / "tests" / "test_main.py", "from server import main\n")
    _write(repo / "docs" / "reports" / "report_2026-04-06.md", "# Report\n\nBody.\n")
    _write(repo / "research" / "landis-data-source" / "report.md", "# Research\n")
    _write(repo / "skills" / "sample" / "SKILL.md", "---\nname: sample\ndescription: sample\n---\n")
    _write(repo / "Obsidian" / "LandIS Knowledge Base" / "00 - Home.md", "# Existing vault\n")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-m", "Initial commit")
    return repo


def test_build_vault_excludes_obsidian_sources_and_writes_pinned_urls(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    output_root = repo / "Obsidian" / "MCP Geo Knowledge Base"
    manifest_path = repo / "data" / "knowledge_base" / "obsidian_kb_manifest.json"

    manifest = build_vault(
        repo,
        mode="canon",
        output_root=output_root,
        manifest_path=manifest_path,
    )

    assert output_root.exists()
    assert (output_root / "00 Home" / "00 - Home.md").exists()
    assert "Obsidian/LandIS Knowledge Base/00 - Home.md" not in manifest["source_index"]

    server_main = manifest["source_index"]["server/main.py"]
    assert "/blob/" in server_main["source_url"]
    assert manifest["source_commit"] in server_main["source_url"]

    issues = validate_manifest(repo, manifest)
    assert issues == {"drift": [], "coverage": [], "recursion": [], "orphan": []}


def test_validate_manifest_detects_drift_and_new_tracked_sources(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    output_root = repo / "Obsidian" / "MCP Geo Knowledge Base"
    manifest_path = repo / "data" / "knowledge_base" / "obsidian_kb_manifest.json"
    manifest = build_vault(repo, mode="canon", output_root=output_root, manifest_path=manifest_path)

    _write(repo / "server" / "main.py", '"""Changed HTTP entrypoint."""\n')
    _write(repo / "tools" / "landis_catalog.py", '"""LandIS catalog."""\n')
    _run_git(repo, "add", "server/main.py", "tools/landis_catalog.py")

    issues = validate_manifest(repo, manifest)
    assert any("server/main.py" in item for item in issues["drift"])
    assert any("tools/landis_catalog.py" in item for item in issues["coverage"])


def test_validate_manifest_detects_missing_note_file_as_orphan(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    output_root = repo / "Obsidian" / "MCP Geo Knowledge Base"
    manifest_path = repo / "data" / "knowledge_base" / "obsidian_kb_manifest.json"
    manifest = build_vault(repo, mode="canon", output_root=output_root, manifest_path=manifest_path)

    note_name = next(
        note_path
        for note_path in manifest["note_index"]
        if note_path.startswith("20 Code/") and note_path != "20 Code/20 - Code Hub.md"
    )
    note_path = output_root / note_name
    note_path.unlink()

    issues = validate_manifest(repo, manifest)
    assert any(note_name in item for item in issues["orphan"])


def test_build_vault_overlay_mode_generates_local_session_notes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    output_root = repo / "Obsidian" / "MCP Geo Knowledge Base"
    manifest_path = repo / "data" / "knowledge_base" / "obsidian_kb_manifest.json"
    overlay_manifest_path = repo / "data" / "knowledge_base" / "obsidian_kb_overlay_manifest.json"

    session_dir = repo / "logs" / "sessions" / "20260406T090000Z"
    _write(session_dir / "session.json", '{"id": "s1"}\n')
    _write(repo / "logs" / "codex-trace.jsonl", "{}\n")

    manifest = build_vault(
        repo,
        mode="all",
        output_root=output_root,
        manifest_path=manifest_path,
        include_local_evidence=True,
        overlay_manifest_path=overlay_manifest_path,
    )

    overlay_readme = output_root / "98 Local Overlay" / "98 - Local Overlay.md"
    overlay_session = output_root / "98 Local Overlay" / "Sessions" / "20260406T090000Z.md"
    assert overlay_readme.exists()
    assert overlay_session.exists()
    assert manifest["overlay"]["session_count"] == 1

    overlay_manifest = json.loads(overlay_manifest_path.read_text(encoding="utf-8"))
    assert overlay_manifest["overlay"]["log_files"] == 1
