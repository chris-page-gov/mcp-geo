#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.obsidian_kb_common import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    flatten_issues,
    validate_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the MCP Geo Obsidian knowledge base manifest."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Canonical manifest JSON path.",
    )
    parser.add_argument(
        "--fail-on",
        choices=["drift", "coverage", "recursion", "orphan"],
        nargs="+",
        default=["drift", "coverage", "recursion", "orphan"],
        help="Validation classes that should fail the command.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    issues = validate_manifest(
        REPO_ROOT,
        manifest,
        validate_drift=True,
        validate_coverage=True,
        validate_recursion=True,
        validate_orphans=True,
    )
    problems = flatten_issues(issues)
    if problems:
        for item in problems:
            print(item)
    else:
        print("Knowledge base manifest is valid.")

    failing = [name for name in args.fail_on if issues.get(name)]
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
