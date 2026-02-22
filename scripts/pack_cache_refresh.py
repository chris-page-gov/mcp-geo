#!/usr/bin/env python3
"""Refresh hybrid fetch cache indexes for boundary and code-list packs.

This script keeps the repo lightweight by caching downloaded pack artifacts under
`data/cache/packs/` (gitignored) while writing compact index metadata under
`resources/*_packs_index.json` for resource exposure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
RESOURCES_DIR = ROOT / "resources"
CACHE_DIR = ROOT / "data" / "cache" / "packs"

KIND_CONFIG = {
    "boundary": {
        "sources": RESOURCES_DIR / "boundary_pack_sources.json",
        "index": RESOURCES_DIR / "boundary_packs_index.json",
    },
    "code_lists": {
        "sources": RESOURCES_DIR / "code_list_pack_sources.json",
        "index": RESOURCES_DIR / "code_list_packs_index.json",
    },
}

FETCHABLE_SOURCE_TYPES = {"ons_api", "nomis_api", "direct", "arcgis_hub"}


@dataclass
class RefreshResult:
    id: str
    title: str
    status: str
    source_url: str
    cache_path: str | None = None
    sha256: str | None = None
    bytes: int | None = None
    error: str | None = None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_file(
    url: str,
    dest: Path,
    timeout: float,
    *,
    max_attempts: int = 8,
    wait_seconds: float = 5.0,
) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    current_url = url
    for attempt in range(1, max_attempts + 1):
        with requests.get(current_url, timeout=timeout, stream=True) as resp:
            resp.raise_for_status()
            content_type = str(resp.headers.get("Content-Type", "")).lower()
            if "application/json" in content_type:
                try:
                    payload = resp.json()
                except Exception:
                    payload = None
                if isinstance(payload, dict):
                    status = str(payload.get("status") or "").strip().lower()
                    download_url = payload.get("downloadUrl") or payload.get("url")
                    if isinstance(download_url, str) and download_url and download_url != current_url:
                        current_url = download_url
                        continue
                    if status in {"pending", "inprogress", "in_progress"}:
                        if attempt < max_attempts:
                            time.sleep(wait_seconds * attempt)
                            continue
                        raise RuntimeError(
                            f"Download stayed pending after {max_attempts} attempts: {current_url}"
                        )
                    with dest.open("wb") as handle:
                        handle.write(json.dumps(payload, ensure_ascii=True).encode("utf-8"))
                    return dest.stat().st_size

            with dest.open("wb") as handle:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        handle.write(chunk)
            return dest.stat().st_size
    raise RuntimeError(f"Failed to resolve download URL after {max_attempts} attempts: {url}")


def _refresh_kind(kind: str, *, timeout: float, dry_run: bool) -> dict[str, Any]:
    cfg = KIND_CONFIG[kind]
    source_doc = _load_json(cfg["sources"])
    packs = source_doc.get("packs") if isinstance(source_doc.get("packs"), list) else []

    results: list[RefreshResult] = []
    kind_cache_dir = CACHE_DIR / kind

    for raw in packs:
        if not isinstance(raw, dict):
            continue
        pack_id = str(raw.get("id") or "").strip()
        title = str(raw.get("title") or pack_id)
        source_url = str(raw.get("sourceUrl") or "").strip()
        source_type = str(raw.get("sourceType") or "").strip()
        if not pack_id or not source_url:
            continue

        if source_type not in FETCHABLE_SOURCE_TYPES:
            results.append(
                RefreshResult(
                    id=pack_id,
                    title=title,
                    status="manifest_only",
                    source_url=source_url,
                )
            )
            continue

        if dry_run:
            results.append(
                RefreshResult(
                    id=pack_id,
                    title=title,
                    status="dry_run",
                    source_url=source_url,
                )
            )
            continue

        suffix = Path(source_url).suffix or ".json"
        dest = kind_cache_dir / pack_id / f"{pack_id}{suffix}"
        try:
            byte_count = _download_file(source_url, dest, timeout)
            sha = _sha256_file(dest)
            results.append(
                RefreshResult(
                    id=pack_id,
                    title=title,
                    status="cached",
                    source_url=source_url,
                    cache_path=str(dest.relative_to(ROOT)),
                    sha256=sha,
                    bytes=byte_count,
                )
            )
        except Exception as exc:  # pragma: no cover - network variability
            results.append(
                RefreshResult(
                    id=pack_id,
                    title=title,
                    status="error",
                    source_url=source_url,
                    error=str(exc),
                )
            )

    payload = {
        "version": source_doc.get("version") or "unknown",
        "kind": kind,
        "cacheMode": "hybrid_fetch_cache",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "packs": [
            {
                "id": result.id,
                "title": result.title,
                "status": result.status,
                "cachePath": result.cache_path,
                "sha256": result.sha256,
                "bytes": result.bytes,
                "sourceUrl": result.source_url,
                "error": result.error,
            }
            for result in results
        ],
    }
    cfg["index"].write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh hybrid boundary/code-list pack cache indexes")
    parser.add_argument(
        "--kind",
        choices=["boundary", "code_lists", "all"],
        default="all",
        help="Which pack type to refresh",
    )
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout seconds")
    parser.add_argument("--dry-run", action="store_true", help="Do not download artifacts")
    args = parser.parse_args()

    kinds = ["boundary", "code_lists"] if args.kind == "all" else [args.kind]
    summary = {kind: _refresh_kind(kind, timeout=args.timeout, dry_run=args.dry_run) for kind in kinds}
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
