#!/usr/bin/env python3
"""Download authenticated LandIS portal items to local storage.

The script reuses the Atlas-authenticated LandIS portal route. It expects the
user to have an active LandIS portal session in ChatGPT Atlas, then mirrors the
catalog metadata and item payloads to a destination directory. Feature services
are exported as raw service metadata plus per-layer GeoJSON/JSON batches.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.landis_portal_inventory import (  # noqa: E402
    SERVICE_TIMEOUT,
    SHARING_BASE_URL,
    arcgis_get,
    arcgis_service_get,
    discover_atlas_token,
)

DEFAULT_INVENTORY = REPO_ROOT / "research/landis-data-source/landis_portal_inventory_2026-04-04.json"
DEFAULT_DESTINATION = Path("/Volumes/ExtSSD-Data/Data/landis_portal_archive_2026-04-04")
SAFE_NAME_REGEX = re.compile(r"[^A-Za-z0-9._-]+")
DEFAULT_FEATURE_BATCH_SIZE = 100


def _http_timeout() -> int:
    value = os.environ.get("LANDIS_PORTAL_HTTP_TIMEOUT")
    if not value:
        return SERVICE_TIMEOUT
    try:
        timeout = int(value)
    except ValueError:
        return SERVICE_TIMEOUT
    return timeout if timeout > 0 else SERVICE_TIMEOUT


def _force_offset_paging() -> bool:
    value = os.environ.get("LANDIS_PORTAL_FORCE_OFFSET", "")
    return value.lower() in {"1", "true", "yes", "on"}


def _safe_name(value: str) -> str:
    cleaned = SAFE_NAME_REGEX.sub("_", value.strip()).strip("._")
    return cleaned or "item"


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": "mcp-geo-landis-downloader/1.0",
            "Accept": "*/*",
        },
    )


def _fetch_bytes(url: str) -> tuple[bytes, dict[str, str], str]:
    with urllib.request.urlopen(_request(url), timeout=_http_timeout()) as response:
        return response.read(), dict(response.headers.items()), response.geturl()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _detect_extension(content_type: str, fallback: str) -> str:
    content_type = (content_type or "").lower()
    if "application/json" in content_type:
        return ".json"
    if "application/pdf" in content_type:
        return ".pdf"
    if "image/png" in content_type:
        return ".png"
    if "image/jpeg" in content_type:
        return ".jpg"
    if "image/gif" in content_type:
        return ".gif"
    if "text/html" in content_type:
        return ".html"
    if "text/plain" in content_type:
        return ".txt"
    return fallback


def _sanitize_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _load_inventory(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_selected_items(
    items: list[dict[str, Any]],
    *,
    item_ids: set[str] | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    selected = [item for item in items if item_ids is None or item["id"] in item_ids]
    return selected[:limit] if limit is not None else selected


def _download_item_data(item: dict[str, Any], token: str, destination: Path) -> dict[str, Any]:
    params = urllib.parse.urlencode({"token": token})
    url = f"{item['dataUrl']}?{params}"
    try:
        payload, headers, final_url = _fetch_bytes(url)
    except urllib.error.HTTPError as exc:
        return {"status": "error", "message": f"item data download failed: HTTP {exc.code}"}
    except urllib.error.URLError as exc:
        return {"status": "error", "message": f"item data download failed: {exc.reason}"}

    content_type = headers.get("Content-Type", "")
    extension = _detect_extension(content_type, ".bin")
    filename = f"item_data{extension}"
    path = destination / filename
    path.write_bytes(payload)

    return {
        "status": "ok",
        "path": str(path),
        "contentType": content_type,
        "contentLength": len(payload),
        "finalUrl": _sanitize_url(final_url),
    }


def _service_object_ids(service_url: str, layer_id: int, token: str) -> list[int]:
    payload = arcgis_service_get(
        f"{service_url}/{layer_id}/query",
        token,
        where="1=1",
        returnIdsOnly="true",
    )
    object_ids = payload.get("objectIds") or []
    return sorted(int(object_id) for object_id in object_ids)


def _service_record_count(service_url: str, layer_id: int, token: str) -> int:
    payload = arcgis_service_get(
        f"{service_url}/{layer_id}/query",
        token,
        where="1=1",
        returnCountOnly="true",
    )
    return int(payload.get("count") or 0)


def _download_service_records(
    service_url: str,
    layer_id: int,
    *,
    token: str,
    destination: Path,
    geometry: bool,
    batch_size: int,
) -> dict[str, Any]:
    files: list[str] = []
    preferred_format = (
        "json" if _force_offset_paging() else ("geojson" if geometry else "json")
    )
    query_url = f"{service_url}/{layer_id}/query"

    def timed_out(exc: BaseException) -> bool:
        if isinstance(exc, (TimeoutError, socket.timeout)):
            return True
        return isinstance(exc, urllib.error.URLError) and "timed out" in str(exc.reason).lower()

    def fetch_batch_by_ids(
        batch_ids: list[int], fmt: str | None = None
    ) -> list[tuple[dict[str, Any], str]]:
        actual_format = fmt or preferred_format
        query = {
            "objectIds": ",".join(str(object_id) for object_id in batch_ids),
            "outFields": "*",
            "returnGeometry": "true" if geometry else "false",
            "outSR": 4326,
        }
        try:
            payload = arcgis_service_get(query_url, token, **query, f=actual_format)
            return [(payload, actual_format)]
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and len(batch_ids) > 1:
                midpoint = len(batch_ids) // 2
                return fetch_batch_by_ids(batch_ids[:midpoint]) + fetch_batch_by_ids(
                    batch_ids[midpoint:]
                )
            raise
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            if geometry and actual_format == "geojson" and timed_out(exc):
                return fetch_batch_by_ids(batch_ids, fmt="json")
            raise

    def write_payload(payload: dict[str, Any], file_index: int, payload_format: str) -> int:
        filename = destination / f"records_batch_{file_index:04d}.{payload_format}"
        _write_json(filename, payload)
        files.append(str(filename))
        return file_index + 1

    def fetch_batch_by_offset(
        offset: int, record_count: int, fmt: str | None = None
    ) -> tuple[dict[str, Any], str]:
        actual_format = fmt or preferred_format
        query = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true" if geometry else "false",
            "resultOffset": offset,
            "resultRecordCount": record_count,
        }
        if geometry:
            query["outSR"] = 4326
        try:
            return arcgis_service_get(query_url, token, **query, f=actual_format), actual_format
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            if geometry and actual_format == "geojson" and timed_out(exc):
                return fetch_batch_by_offset(offset, record_count, fmt="json")
            raise

    object_ids: list[int] = []
    if not _force_offset_paging():
        try:
            object_ids = _service_object_ids(service_url, layer_id, token)
        except (TimeoutError, socket.timeout, urllib.error.URLError):
            object_ids = []

    if object_ids:
        file_index = 1
        for batch_index in range(0, len(object_ids), batch_size):
            seed_batch_ids = object_ids[batch_index : batch_index + batch_size]
            for payload, payload_format in fetch_batch_by_ids(seed_batch_ids):
                file_index = write_payload(payload, file_index, payload_format)
        return {
            "recordCount": len(object_ids),
            "files": files,
            "pagingMode": "objectIds",
        }

    total_records = _service_record_count(service_url, layer_id, token)
    if total_records == 0:
        return {"recordCount": 0, "files": [], "pagingMode": "offset"}

    file_index = 1
    for offset in range(0, total_records, batch_size):
        payload, payload_format = fetch_batch_by_offset(offset, batch_size)
        file_index = write_payload(payload, file_index, payload_format)
    return {"recordCount": total_records, "files": files, "pagingMode": "offset"}


def _download_feature_service(
    item: dict[str, Any],
    *,
    token: str,
    destination: Path,
    batch_size: int,
) -> dict[str, Any]:
    service_url = item["url"]
    service_json = arcgis_service_get(service_url, token)
    _write_json(destination / "service.json", service_json)
    service_summary: dict[str, Any] = {
        "serviceUrl": service_url,
        "layers": [],
        "tables": [],
    }

    for collection_name in ("layers", "tables"):
        for entry in service_json.get(collection_name, []):
            layer_id = int(entry["id"])
            layer_json = arcgis_service_get(f"{service_url}/{layer_id}", token)
            layer_dir = destination / collection_name / f"{layer_id:02d}_{_safe_name(entry.get('name') or entry.get('title') or str(layer_id))}"
            _write_json(layer_dir / "metadata.json", layer_json)
            geometry_type = layer_json.get("geometryType")
            records_info = _download_service_records(
                service_url,
                layer_id,
                token=token,
                destination=layer_dir,
                geometry=bool(geometry_type),
                batch_size=batch_size,
            )
            summary_entry = {
                "id": layer_id,
                "name": entry.get("name"),
                "geometryType": geometry_type,
                "recordCount": records_info["recordCount"],
                "files": records_info["files"],
                "pagingMode": records_info.get("pagingMode"),
            }
            service_summary[collection_name].append(summary_entry)

    _write_json(destination / "download_summary.json", service_summary)
    return service_summary


def download_item(
    item: dict[str, Any],
    *,
    token: str,
    destination_root: Path,
    batch_size: int,
) -> dict[str, Any]:
    item_dir = destination_root / item["classification"] / f"{item['id']}_{_safe_name(item['title'])}"
    item_dir.mkdir(parents=True, exist_ok=True)
    _write_json(item_dir / "inventory_record.json", item)

    arcgis_detail = arcgis_get(f"/content/items/{item['id']}", token)
    _write_json(item_dir / "item_detail.json", arcgis_detail)

    result: dict[str, Any] = {
        "id": item["id"],
        "title": item["title"],
        "type": item["type"],
        "classification": item["classification"],
        "path": str(item_dir),
    }

    if item["type"] == "Feature Service":
        result["serviceExport"] = _download_feature_service(
            item,
            token=token,
            destination=item_dir / "feature_service",
            batch_size=batch_size,
        )
    else:
        result["itemData"] = _download_item_data(item, token, item_dir)

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=DEFAULT_INVENTORY,
        help="Path to the generated LandIS portal inventory JSON.",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=DEFAULT_DESTINATION,
        help="Destination directory for the downloaded archive.",
    )
    parser.add_argument(
        "--item-id",
        action="append",
        dest="item_ids",
        default=None,
        help="Optional ArcGIS item ID to download. Repeat for multiple items.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on the number of items to download after filtering.",
    )
    parser.add_argument(
        "--feature-batch-size",
        type=int,
        default=DEFAULT_FEATURE_BATCH_SIZE,
        help="Number of records to request per feature-service query batch.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional ArcGIS token. If omitted, discover from the Atlas session.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inventory = _load_inventory(args.inventory)
    token = args.token or discover_atlas_token()

    destination = args.destination
    destination.mkdir(parents=True, exist_ok=True)
    selected_items = _iter_selected_items(
        inventory["items"],
        item_ids=set(args.item_ids) if args.item_ids else None,
        limit=args.limit,
    )

    results = []
    for index, item in enumerate(selected_items, start=1):
        try:
            result = download_item(
                item,
                token=token,
                destination_root=destination,
                batch_size=args.feature_batch_size,
            )
        except Exception as exc:  # pragma: no cover - runtime guard for long archive jobs
            result = {
                "id": item["id"],
                "title": item["title"],
                "type": item["type"],
                "classification": item["classification"],
                "status": "error",
                "message": str(exc),
            }
            print(
                f"[{index}/{len(selected_items)}] failed {item['title']} ({item['id']}): {exc}",
                flush=True,
            )
        else:
            print(
                f"[{index}/{len(selected_items)}] downloaded {item['title']} ({item['id']})",
                flush=True,
            )
        results.append(result)

    manifest = {
        "generatedFromInventory": str(args.inventory),
        "destination": str(destination),
        "downloadedAtItemCount": len(results),
        "results": results,
    }
    _write_json(destination / "download_manifest.json", manifest)
    print(
        json.dumps(
            {
                "destination": str(destination),
                "downloadedItems": len(results),
                "manifest": str(destination / "download_manifest.json"),
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
