#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.obsidian_kb_common import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_OVERLAY_MANIFEST_PATH,
    WORKTREE_REF,
    build_vault,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the MCP Geo Obsidian knowledge base.")
    parser.add_argument(
        "--mode",
        choices=["canon", "overlay", "all"],
        default="canon",
        help="Which portion of the vault to build.",
    )
    parser.add_argument(
        "--git-ref",
        default=WORKTREE_REF,
        help="Git ref to read canonical content from. Use WORKTREE to read current files.",
    )
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
        help="Canonical manifest JSON output path.",
    )
    parser.add_argument(
        "--overlay-manifest-out",
        type=Path,
        default=DEFAULT_OVERLAY_MANIFEST_PATH,
        help="Overlay manifest JSON output path.",
    )
    parser.add_argument(
        "--include-local-evidence",
        action="store_true",
        help="Include local `logs/` evidence when building overlay notes.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = build_vault(
        REPO_ROOT,
        mode=args.mode,
        git_ref=args.git_ref,
        output_root=args.output_root,
        manifest_path=args.manifest_out,
        include_local_evidence=args.include_local_evidence,
        overlay_manifest_path=args.overlay_manifest_out,
    )
    print(f"Built vault at {args.output_root}")
    print(f"Manifest: {args.manifest_out}")
    if manifest.get("overlay") is not None:
        print(f"Overlay manifest: {args.overlay_manifest_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
