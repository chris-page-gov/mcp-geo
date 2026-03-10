from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency fallback
    psycopg = None  # type: ignore[assignment]

from server.config import settings
from server.security import configured_secrets, mask_in_text, mask_in_value
from tools.os_common import client

_DOWNLOADS_BASE = "https://api.os.uk/downloads/v1"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_SQL = _REPO_ROOT / "scripts" / "route_graph_schema.sql"
_PRODUCT_FIELDS = (
    "id",
    "name",
    "title",
    "description",
    "license",
    "version",
)
_DOWNLOAD_FIELDS = (
    "id",
    "name",
    "fileName",
    "title",
    "description",
    "releaseDate",
    "release_date",
    "created",
    "createdAt",
    "updated",
    "publishedAt",
    "publicationDate",
    "fileSize",
    "size",
    "checksum",
    "sha256",
    "sha1",
    "md5",
    "format",
    "mediaType",
    "mimeType",
    "coverage",
)
_DROPPED_FIELD_MARKERS = (
    "password",
    "token",
    "secret",
    "signature",
    "authorization",
    "url",
    "uri",
    "href",
    "link",
)


def _runtime_dir() -> Path:
    raw = str(getattr(settings, "ROUTE_GRAPH_RUNTIME_DIR", "data/runtime/routing"))
    path = Path(raw)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path


def _default_dsn() -> str:
    return (
        os.getenv("ROUTE_GRAPH_DSN")
        or getattr(settings, "ROUTE_GRAPH_DSN", "")
        or os.getenv("BOUNDARY_CACHE_DSN")
        or getattr(settings, "BOUNDARY_CACHE_DSN", "")
    )


def _downloads_get(path: str) -> tuple[int, Any]:
    return client.get_json(f"{_DOWNLOADS_BASE}{path}", None)


def _is_dropped_field_name(key: object) -> bool:
    if not isinstance(key, str):
        return False
    normalized = key.strip().lower().replace("-", "_")
    return any(marker in normalized for marker in _DROPPED_FIELD_MARKERS)


def _sanitize_nested(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _sanitize_nested(item)
            for key, item in value.items()
            if not _is_dropped_field_name(key)
        }
    if isinstance(value, list):
        return [_sanitize_nested(item) for item in value]
    return value


def _pick_fields(item: dict[str, Any], allowed_fields: tuple[str, ...]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for field in allowed_fields:
        if field not in item:
            continue
        value = _sanitize_nested(item[field])
        if value in (None, "", [], {}):
            continue
        safe[field] = value
    return safe


def _safe_product_record(product: dict[str, Any]) -> dict[str, Any]:
    return _pick_fields(product, _PRODUCT_FIELDS)


def _safe_download_record(download: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(download, dict):
        return None
    return _pick_fields(download, _DOWNLOAD_FIELDS)


def _output_secrets(dsn: str = "") -> list[str]:
    secrets: list[str] = []
    seen: set[str] = set()
    for raw in configured_secrets(settings):
        if raw and raw not in seen:
            secrets.append(raw)
            seen.add(raw)
    if dsn and dsn not in seen:
        secrets.append(dsn)
        seen.add(dsn)
    if dsn:
        parsed = urlparse(dsn)
        if parsed.password and parsed.password not in seen:
            secrets.append(parsed.password)
    return secrets


def _bootstrap_schema(dsn: str) -> dict[str, Any]:
    if not dsn:
        raise RuntimeError("Missing ROUTE_GRAPH_DSN/BOUNDARY_CACHE_DSN")
    if psycopg is None:
        raise RuntimeError("psycopg is not installed")
    sql_text = _SCHEMA_SQL.read_text(encoding="utf-8")
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_text)
    return {"dsnConfigured": True, "schemaSql": str(_SCHEMA_SQL), "status": "bootstrapped"}


def _capture_provenance(product_query: str, *, limit: int, output_path: Path) -> dict[str, Any]:
    status, products = _downloads_get("/products")
    if status != 200:
        raise RuntimeError(f"Unable to list OS download products: {products}")
    if not isinstance(products, list):
        raise RuntimeError("Unexpected OS Downloads products payload")

    query_lower = product_query.lower()
    matches = [
        product
        for product in products
        if isinstance(product, dict)
        and query_lower
        in " ".join(
            str(product.get(key, "")) for key in ("id", "name", "title", "description")
        ).lower()
    ]
    if not matches:
        raise RuntimeError(f"No OS Downloads product matched '{product_query}'")

    selected = matches[0]
    product_id = str(selected.get("id") or "")
    if not product_id:
        raise RuntimeError("Matched OS Downloads product has no id")

    status, downloads = _downloads_get(f"/products/{product_id}/downloads")
    if status != 200:
        raise RuntimeError(f"Unable to list downloads for {product_id}: {downloads}")
    if not isinstance(downloads, list):
        raise RuntimeError("Unexpected OS Downloads downloads payload")

    sorted_downloads = sorted(
        [item for item in downloads if isinstance(item, dict)],
        key=_download_sort_key,
        reverse=True,
    )
    latest = sorted_downloads[0] if sorted_downloads else None
    safe_selected = _safe_product_record(selected)
    safe_downloads = [_safe_download_record(item) for item in sorted_downloads[:limit]]
    payload = {
        "capturedAt": datetime.now(timezone.utc).isoformat(),
        "productQuery": product_query,
        "selectedProduct": safe_selected,
        "latestDownload": _safe_download_record(latest),
        "downloads": [item for item in safe_downloads if item],
        "downloadCount": len(sorted_downloads),
        "notes": [
            "This captures MRN package provenance and schema bootstrap state.",
            "Populate routing.graph_nodes / routing.graph_edges from the selected package before enabling live routing.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return payload


def _download_sort_key(item: dict[str, Any]) -> tuple[str, str]:
    for key in (
        "releaseDate",
        "release_date",
        "created",
        "createdAt",
        "updated",
        "publishedAt",
        "publicationDate",
    ):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip(), str(item.get("id") or item.get("name") or "")
    return "", str(item.get("id") or item.get("name") or "")


def _upsert_metadata(dsn: str, *, provenance_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if not dsn:
        return {"status": "skipped", "reason": "no_dsn"}
    if psycopg is None:
        return {"status": "skipped", "reason": "psycopg_missing"}
    latest = payload.get("latestDownload") if isinstance(payload, dict) else {}
    latest = latest if isinstance(latest, dict) else {}
    graph_version = str(latest.get("id") or latest.get("name") or "mrn-provenance")
    built_at = datetime.now(timezone.utc).isoformat()
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(_SCHEMA_SQL.read_text(encoding="utf-8"))
            cur.execute(
                """
                INSERT INTO routing.graph_metadata (
                    graph_version,
                    is_active,
                    built_at,
                    source_product,
                    source_release_date,
                    source_download_id,
                    source_download_name,
                    source_license,
                    provenance_path,
                    status
                )
                VALUES (%s, FALSE, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (graph_version)
                DO UPDATE SET
                    built_at = EXCLUDED.built_at,
                    source_product = EXCLUDED.source_product,
                    source_release_date = EXCLUDED.source_release_date,
                    source_download_id = EXCLUDED.source_download_id,
                    source_download_name = EXCLUDED.source_download_name,
                    source_license = EXCLUDED.source_license,
                    provenance_path = EXCLUDED.provenance_path,
                    status = EXCLUDED.status;
                """,
                (
                    graph_version,
                    built_at,
                    str((payload.get("selectedProduct") or {}).get("name") or "OS MRN"),
                    (latest.get("releaseDate") or latest.get("release_date") or None),
                    str(latest.get("id") or "") or None,
                    str(latest.get("name") or latest.get("fileName") or "") or None,
                    str((payload.get("selectedProduct") or {}).get("license") or "") or None,
                    str(provenance_path),
                    "provenance_captured",
                ),
            )
    return {"status": "updated", "graphVersion": graph_version}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap the routing schema and capture OS MRN download provenance."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser("bootstrap", help="Create routing schema and tables")
    bootstrap_parser.add_argument("--dsn", default=_default_dsn())

    capture_parser = subparsers.add_parser(
        "capture-provenance",
        help="Capture MRN download metadata to the routing runtime directory",
    )
    capture_parser.add_argument("--dsn", default=_default_dsn())
    capture_parser.add_argument(
        "--product-query",
        default="multi modal routing network",
        help="Case-insensitive OS Downloads product search term",
    )
    capture_parser.add_argument("--limit", type=int, default=25)
    capture_parser.add_argument(
        "--output",
        default=str(_runtime_dir() / getattr(settings, "ROUTE_GRAPH_PROVENANCE_FILE", "os_mrn_downloads.json")),
    )

    args = parser.parse_args()
    try:
        if args.command == "bootstrap":
            result = _bootstrap_schema(args.dsn)
        else:
            output_path = Path(args.output)
            if not output_path.is_absolute():
                output_path = _REPO_ROOT / output_path
            payload = _capture_provenance(args.product_query, limit=args.limit, output_path=output_path)
            metadata_result = _upsert_metadata(args.dsn, provenance_path=output_path, payload=payload)
            result = {
                "status": "captured",
                "output": str(output_path),
                "product": payload.get("selectedProduct"),
                "latestDownload": payload.get("latestDownload"),
                "metadata": metadata_result,
            }
    except Exception as exc:
        safe_message = mask_in_text(str(exc), _output_secrets(getattr(args, "dsn", "")))
        print(json.dumps({"status": "error", "message": safe_message}, ensure_ascii=True))
        return 1

    safe_result = mask_in_value(result, _output_secrets(getattr(args, "dsn", "")))
    print(json.dumps(safe_result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
