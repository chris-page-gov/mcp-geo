#!/usr/bin/env python3
"""Validate the local ONS catalog index schema and metadata quality."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.config import settings
from tools.ons_catalog_validator import validate_catalog_file


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / raw
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ONS catalog schema and quality metadata")
    parser.add_argument(
        "--input",
        default=getattr(settings, "ONS_CATALOG_PATH", "resources/ons_catalog.json"),
        help="Catalog JSON path (default: settings ONS_CATALOG_PATH)",
    )
    parser.add_argument(
        "--min-items",
        type=int,
        default=1,
        help="Minimum expected dataset count for non-placeholder catalogs (default: 1)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output",
    )
    args = parser.parse_args(argv)

    path = _resolve_path(args.input)
    payload, errors = validate_catalog_file(path, min_items=max(args.min_items, 0))
    summary = {
        "path": str(path),
        "ok": not errors,
        "errorCount": len(errors),
        "items": len(payload.get("items") or []) if isinstance(payload, dict) else 0,
        "generatedAt": payload.get("generatedAt") if isinstance(payload, dict) else None,
        "source": payload.get("source") if isinstance(payload, dict) else None,
        "placeholder": payload.get("placeholder") if isinstance(payload, dict) else None,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=True, indent=2))
    else:
        status = "OK" if summary["ok"] else "INVALID"
        print(f"[ons-catalog] {status} :: {summary['path']}")
        print(
            f"items={summary['items']} generatedAt={summary['generatedAt']} "
            f"placeholder={summary['placeholder']}"
        )
        for error in errors[:25]:
            print(f"- {error}")
        if len(errors) > 25:
            print(f"... {len(errors) - 25} more errors")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
