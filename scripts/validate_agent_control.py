#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agent_control_common import (  # noqa: E402
    DEFAULT_ACTIVE_MODE_MANIFEST_PATH,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_OUTPUT_ROOT,
)
from scripts.obsidian_cli import (  # noqa: E402
    DEFAULT_OBSIDIAN_APP,
    DEFAULT_OBSIDIAN_USER_DATA,
    preflight,
)

OBSIDIAN_MODE_MARKERS = {
    "AGENTS.md": "obsidian` agent-control mode",
    "CLAUDE.md": "@AGENTS.md",
    "GEMINI.md": "@AGENTS.md",
    ".github/copilot-instructions.md": "Primary control surface",
    "CONTEXT.md": "Compatibility Summary",
    "PROGRESS.MD": "Compatibility Summary",
}

CLASSIC_TRACKER_FILES = {"CONTEXT.md", "PROGRESS.MD"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the MCP Geo agent control vault.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Agent control vault root.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Machine-readable control-vault manifest path.",
    )
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help="Skip the official Obsidian CLI preflight checks.",
    )
    parser.add_argument(
        "--app-path",
        type=Path,
        default=DEFAULT_OBSIDIAN_APP,
        help="Obsidian app bundle path for CLI preflight.",
    )
    parser.add_argument(
        "--cli-path",
        type=Path,
        default=None,
        help="Explicit Obsidian CLI binary path override.",
    )
    parser.add_argument(
        "--user-data-path",
        type=Path,
        default=DEFAULT_OBSIDIAN_USER_DATA,
        help="Obsidian user-data directory used to detect updated runtime packages.",
    )
    parser.add_argument(
        "--mode-manifest",
        type=Path,
        default=DEFAULT_ACTIVE_MODE_MANIFEST_PATH,
        help="Optional active-mode manifest path.",
    )
    return parser


def git_head_text(repo_root: Path, rel_path: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"HEAD:{rel_path}"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def validate_control_vault(
    repo_root: Path,
    output_root: Path,
    manifest_path: Path,
    *,
    check_cli: bool,
    app_path: Path,
    user_data_path: Path,
    cli_path: Path | None,
    mode_manifest_path: Path | None,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not manifest_path.exists():
        return [
            {
                "code": "MANIFEST_MISSING",
                "message": f"Control-vault manifest is missing: {manifest_path}",
            }
        ]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("curated_notes", []):
        note_path = output_root / entry["path"]
        if not note_path.exists():
            issues.append(
                {
                    "code": "CURATED_NOTE_MISSING",
                    "message": f"Required curated note is missing: {entry['path']}",
                }
            )
    for entry in manifest.get("generated_notes", []):
        note_path = output_root / entry["path"]
        if not note_path.exists():
            issues.append(
                {
                    "code": "GENERATED_NOTE_MISSING",
                    "message": f"Required generated note is missing: {entry['path']}",
                }
            )
    if mode_manifest_path and mode_manifest_path.exists():
        mode_manifest = json.loads(mode_manifest_path.read_text(encoding="utf-8"))
        mode = mode_manifest.get("mode")
        if mode == "obsidian":
            for rel_path, marker in OBSIDIAN_MODE_MARKERS.items():
                text = (repo_root / rel_path).read_text(encoding="utf-8")
                if marker not in text:
                    issues.append(
                        {
                            "code": "MODE_FILE_MISMATCH",
                            "message": (
                                f"{rel_path} does not match the active "
                                "obsidian-mode marker."
                            ),
                        }
                    )
        elif mode == "classic":
            for rel_path in mode_manifest.get("root_files", []):
                current = (repo_root / rel_path).read_text(encoding="utf-8")
                if rel_path in CLASSIC_TRACKER_FILES:
                    if OBSIDIAN_MODE_MARKERS[rel_path] in current:
                        issues.append(
                            {
                                "code": "CLASSIC_TRACKER_SHIM_ACTIVE",
                                "message": (
                                    f"{rel_path} still contains the obsidian-mode "
                                    "compatibility shim marker while classic mode is active."
                                ),
                            }
                        )
                    continue
                if current != git_head_text(repo_root, rel_path):
                    issues.append(
                        {
                            "code": "CLASSIC_RESTORE_MISMATCH",
                            "message": (
                                f"{rel_path} does not match the tracked "
                                "classic baseline at HEAD."
                            ),
                        }
                    )
    if check_cli:
        issues.extend(
            preflight(
                output_root,
                app_path=app_path,
                user_data_path=user_data_path,
                cli_path=cli_path,
            )["issues"]
        )
    return issues


def main() -> int:
    args = build_parser().parse_args()
    issues = validate_control_vault(
        REPO_ROOT,
        args.output_root,
        args.manifest,
        check_cli=not args.skip_cli,
        app_path=args.app_path,
        user_data_path=args.user_data_path,
        cli_path=args.cli_path,
        mode_manifest_path=args.mode_manifest,
    )
    if not issues:
        print("Agent control vault is valid.")
        return 0
    for issue in issues:
        print(f"{issue['code']}: {issue['message']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
