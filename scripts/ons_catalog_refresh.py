#!/usr/bin/env python3
"""Refresh the local ONS dataset catalog index.

Usage:
  python3 scripts/ons_catalog_refresh.py
  python3 scripts/ons_catalog_refresh.py --output resources/ons_catalog.json
  python3 scripts/ons_catalog_refresh.py --max-items 500
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.config import settings
from tools.ons_common import ONSClient


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / raw
    return path


def _build_entry(item: dict[str, Any]) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "id": item.get("id"),
        "title": item.get("title"),
        "description": item.get("description"),
        "keywords": item.get("keywords") or [],
        "state": item.get("state"),
        "links": item.get("links") or {},
    }
    for key in ("themes", "topic", "topics", "taxonomies"):
        if key in item:
            entry["themes"] = item.get(key)
            break
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh ONS dataset catalog index")
    parser.add_argument(
        "--output",
        default=getattr(settings, "ONS_CATALOG_PATH", "resources/ons_catalog.json"),
        help="Output JSON path (default: settings ONS_CATALOG_PATH)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="Optional cap on number of datasets (0 = no cap)",
    )
    args = parser.parse_args()

    client = ONSClient()
    base_api = getattr(settings, "ONS_DATASET_API_BASE", "https://api.beta.ons.gov.uk/v1")
    url = f"{base_api}/datasets"
    status, items = client.get_all_pages(url, params={"limit": 1000, "page": 1})
    if status != 200:
        raise SystemExit(f"ONS API error while fetching datasets: {items}")
    if not isinstance(items, list):
        raise SystemExit("Unexpected ONS datasets response")

    max_items = max(0, args.max_items)
    if max_items:
        items = items[:max_items]

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": base_api,
        "placeholder": False,
        "items": [_build_entry(item) for item in items if isinstance(item, dict)],
    }

    out_path = _resolve_path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload['items'])} entries to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
