#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agent_control_common import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    DEFAULT_OUTPUT_ROOT,
    build_control_vault,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the MCP Geo agent control vault.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Vault root to write.",
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Machine-readable control-vault manifest path.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = build_control_vault(
        REPO_ROOT,
        output_root=args.output_root,
        manifest_path=args.manifest_out,
    )
    print(f"Built agent control vault at {manifest['output_root']}")
    print(f"Manifest: {args.manifest_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
