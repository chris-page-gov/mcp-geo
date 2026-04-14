#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agent_control_common import DEFAULT_MANIFEST_PATH, DEFAULT_OUTPUT_ROOT  # noqa: E402
from scripts.obsidian_cli import DEFAULT_OBSIDIAN_APP, preflight  # noqa: E402


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
    return parser


def validate_control_vault(
    output_root: Path,
    manifest_path: Path,
    *,
    check_cli: bool,
    app_path: Path,
    cli_path: Path | None,
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
    if check_cli:
        issues.extend(preflight(output_root, app_path=app_path, cli_path=cli_path)["issues"])
    return issues


def main() -> int:
    args = build_parser().parse_args()
    issues = validate_control_vault(
        args.output_root,
        args.manifest,
        check_cli=not args.skip_cli,
        app_path=args.app_path,
        cli_path=args.cli_path,
    )
    if not issues:
        print("Agent control vault is valid.")
        return 0
    for issue in issues:
        print(f"{issue['code']}: {issue['message']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
