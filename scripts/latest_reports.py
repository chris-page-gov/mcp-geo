#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:  # Suppress loguru default sink during report runs.
    from loguru import logger

    logger.remove()
except Exception:  # pragma: no cover - loguru not installed
    logger = None  # type: ignore[assignment]

try:
    from server.boundary_cache import BoundaryCache
except ImportError:  # pragma: no cover - optional dependency fallback
    BoundaryCache = None  # type: ignore[assignment]


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _latest_run_report(run_root: Path) -> Path | None:
    if not run_root.exists():
        return None
    candidates = sorted(run_root.glob("*/run_report.json"))
    if not candidates:
        return None
    return candidates[-1]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _cache_status() -> dict[str, Any]:
    configured = bool(os.getenv("BOUNDARY_CACHE_ENABLED", ""))
    dsn_set = bool(os.getenv("BOUNDARY_CACHE_DSN", ""))
    if BoundaryCache is None:
        return {
            "enabled": False,
            "configured": configured,
            "dsnSet": dsn_set,
            "error": "Boundary cache module unavailable.",
            "hint": "Ensure repo imports are used and optional boundary deps are installed.",
        }
    if os.getenv("boundary_cache_enabled") or os.getenv("boundary_cache_dsn"):
        if not os.getenv("BOUNDARY_CACHE_ENABLED") and not os.getenv("BOUNDARY_CACHE_DSN"):
            print(
                "Warning: lowercase boundary_cache_* env vars detected; "
                "use BOUNDARY_CACHE_ENABLED/BOUNDARY_CACHE_DSN instead."
            )
    cache = BoundaryCache.from_settings()
    if not cache.enabled():
        return {
            "enabled": False,
            "configured": configured,
            "dsnSet": dsn_set,
            "message": "Boundary cache is disabled.",
            "hint": "Set BOUNDARY_CACHE_ENABLED=true and BOUNDARY_CACHE_DSN=postgresql://...",
        }
    status = cache.status()
    if status is None:
        return {
            "enabled": True,
            "configured": configured,
            "dsnSet": dsn_set,
            "error": "Boundary cache query failed.",
            "hint": "Ensure psycopg is installed and PostGIS is reachable.",
        }
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print latest boundary reports.")
    parser.add_argument("--boundary", action="store_true", help="Include boundary pipeline report")
    parser.add_argument("--cache", action="store_true", help="Include boundary cache status")
    parser.add_argument("--workdir", default="data/boundary_runs")
    parser.add_argument("--cache-out", default="data/cache_reports")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    include_boundary = args.boundary or (not args.boundary and not args.cache)
    include_cache = args.cache or (not args.boundary and not args.cache)
    output: dict[str, Any] = {}

    if include_boundary:
        run_root = Path(args.workdir)
        latest = _latest_run_report(run_root)
        output["boundary_pipeline_latest"] = str(latest) if latest else None

    if include_cache:
        cache_status = _cache_status()
        cache_root = Path(args.cache_out)
        timestamp = _timestamp_slug()
        cache_path = cache_root / timestamp / "cache_status.json"
        _write_json(cache_path, cache_status)
        output["cache_status_latest"] = str(cache_path)

    print(json.dumps(output, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
