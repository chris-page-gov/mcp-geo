#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


SCRIPT_TAG_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)


def strip_scripts(html: str) -> str:
    return SCRIPT_TAG_RE.sub("", html)


def process_snapshot(src_root: Path, dest_root: Path) -> int:
    count = 0
    for path in src_root.rglob("*.html"):
        data = path.read_text(encoding="utf-8", errors="replace")
        cleaned = strip_scripts(data)
        out_path = dest_root / path.relative_to(src_root)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(cleaned, encoding="utf-8")
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create script-free HTML copies for offline viewing."
    )
    parser.add_argument("src", help="Source snapshot directory (e.g. docs/vendor/openai/_snapshot)")
    parser.add_argument(
        "--dest",
        help="Destination directory for script-free copies (default: <src>_noscript)",
    )
    args = parser.parse_args()

    src_root = Path(args.src).resolve()
    if not src_root.exists():
        raise SystemExit(f"Source directory does not exist: {src_root}")
    if not src_root.is_dir():
        raise SystemExit(f"Source path is not a directory: {src_root}")

    dest_root = Path(args.dest).resolve() if args.dest else src_root.with_name(
        f"{src_root.name}_noscript"
    )
    if dest_root == src_root:
        raise SystemExit("Destination must be different from source.")

    count = process_snapshot(src_root, dest_root)
    print(f"Wrote {count} HTML files to {dest_root}")


if __name__ == "__main__":
    main()
