#!/usr/bin/env python3
"""Refresh the local ONS geography cache used by ons_geo.* tools.

Primary exact-mode products:
- ONSPD (postcode)
- ONSUD (UPRN)

Parallel best-fit products:
- NSPL (postcode)
- NSUL (UPRN)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import sqlite3
import time
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from server.ons_geo_cache import (
    DERIVATION_MODES,
    KEY_TYPES,
    ensure_schema,
    extract_geography_fields,
    normalize_derivation_mode,
    normalize_key,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES_PATH = ROOT / "resources" / "ons_geo_sources.json"
DEFAULT_CACHE_DIR = ROOT / "data" / "cache" / "ons_geo"
DEFAULT_INDEX_PATH = ROOT / "resources" / "ons_geo_cache_index.json"
DEFAULT_DB_NAME = "ons_geo_cache.sqlite"


@dataclass(frozen=True)
class ProductConfig:
    product_id: str
    key_type: str
    derivation_mode: str
    priority: int
    release: str
    title: str
    source_url: str
    key_candidates: list[str]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def _parse_map_args(values: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in values:
        key, sep, raw_value = item.partition("=")
        if not sep:
            raise ValueError(f"Expected KEY=VALUE format, got: {item}")
        key = key.strip().upper()
        value = raw_value.strip()
        if not key or not value:
            raise ValueError(f"Expected KEY=VALUE format, got: {item}")
        mapping[key] = value
    return mapping


def _load_products(path: Path) -> tuple[str, list[ProductConfig]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("sources manifest must be an object")
    version = str(payload.get("version") or "unknown")
    raw_products = payload.get("products")
    if not isinstance(raw_products, list):
        raise ValueError("sources manifest must include a products list")

    products: list[ProductConfig] = []
    for raw in raw_products:
        if not isinstance(raw, dict):
            continue
        product_id = str(raw.get("id") or "").strip().upper()
        key_type = str(raw.get("keyType") or "").strip().lower()
        derivation_mode = normalize_derivation_mode(str(raw.get("derivationMode") or ""))
        if not product_id or key_type not in KEY_TYPES or derivation_mode not in DERIVATION_MODES:
            continue
        priority_raw = raw.get("priority", 100)
        priority = int(priority_raw) if isinstance(priority_raw, int) else 100
        title = str(raw.get("title") or product_id)
        release = str(raw.get("release") or "unknown")
        source = raw.get("source")
        source_url = ""
        if isinstance(source, dict):
            source_url = str(source.get("downloadUrl") or "").strip()
        key_candidates = []
        fields = raw.get("fieldCandidates")
        if isinstance(fields, dict):
            candidates = fields.get("key")
            if isinstance(candidates, list):
                key_candidates = [str(item).strip() for item in candidates if str(item).strip()]
        if not key_candidates:
            key_candidates = (
                ["pcds", "pcd", "postcode"] if key_type == "postcode" else ["uprn", "UPRN"]
            )
        products.append(
            ProductConfig(
                product_id=product_id,
                key_type=key_type,
                derivation_mode=derivation_mode,
                priority=priority,
                release=release,
                title=title,
                source_url=source_url,
                key_candidates=key_candidates,
            )
        )
    return version, products


def _download(url: str, destination: Path, timeout: float) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, timeout=timeout, stream=True) as resp:
        resp.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return destination


@contextmanager
def _open_csv_rows(path: Path) -> Iterator[csv.DictReader]:
    suffix = path.suffix.lower()
    if suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            members = sorted(
                name
                for name in archive.namelist()
                if name.lower().endswith(".csv") and not name.endswith("/")
            )
            if not members:
                raise ValueError(f"No CSV file found in zip archive: {path}")
            with archive.open(members[0], "r") as raw:
                with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text_stream:
                    yield csv.DictReader(text_stream)
        return
    if suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
            yield csv.DictReader(stream)
        return
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        yield csv.DictReader(stream)


def _pick_key_field(reader: csv.DictReader, candidates: list[str]) -> str:
    if reader.fieldnames is None:
        raise ValueError("CSV has no header row")
    lookup = {name.lower(): name for name in reader.fieldnames if isinstance(name, str)}
    for candidate in candidates:
        chosen = lookup.get(candidate.lower())
        if chosen:
            return chosen
    raise ValueError(f"Could not find key column in CSV header using candidates {candidates}")


def _row_value_ci(row: dict[str, Any], candidates: list[str]) -> str | None:
    lower_lookup = {
        str(key).strip().lower(): value
        for key, value in row.items()
        if isinstance(key, str)
    }
    for candidate in candidates:
        value = lower_lookup.get(candidate.lower())
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _coerce_delivery_flag(row: dict[str, Any]) -> int | None:
    value = _row_value_ci(
        row,
        [
            "postal_delivery",
            "postaldelivery",
            "is_postal_delivery",
            "delivery",
            "delivery_point",
            "has_delivery_point",
            "receives_post",
            "postal_address",
        ],
    )
    if value is None:
        return None
    norm = value.strip().lower()
    if norm in {"1", "true", "t", "yes", "y"}:
        return 1
    if norm in {"0", "false", "f", "no", "n"}:
        return 0
    return None


def _code_from_geographies(
    geographies: dict[str, dict[str, str]],
    stems: list[str],
) -> str | None:
    for stem in stems:
        entry = geographies.get(stem)
        if not isinstance(entry, dict):
            continue
        code = entry.get("code")
        if isinstance(code, str) and code.strip():
            return code.strip()
    return None


def _name_from_geographies(
    geographies: dict[str, dict[str, str]],
    stems: list[str],
) -> str | None:
    for stem in stems:
        entry = geographies.get(stem)
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return None


def _insert_uprn_index_row(
    *,
    conn: sqlite3.Connection,
    product: ProductConfig,
    uprn: str,
    row: dict[str, Any],
    cached_at: str,
) -> None:
    geographies = extract_geography_fields(row)
    postcode_raw = _row_value_ci(row, ["pcds", "pcd", "postcode", "post_code"])
    postcode = normalize_key("postcode", postcode_raw) if postcode_raw else None

    oa_code = _code_from_geographies(geographies, ["oa21", "oa11", "oa"])
    lsoa_code = _code_from_geographies(geographies, ["lsoa21", "lsoa11", "lsoa01", "lsoa"])
    msoa_code = _code_from_geographies(geographies, ["msoa21", "msoa11", "msoa01", "msoa"])
    lad_code = _code_from_geographies(
        geographies,
        ["lad24", "lad23", "lad22", "lad21", "lad20", "lad19", "lad18", "lad17", "lad"],
    )
    lad_name = _name_from_geographies(
        geographies,
        ["lad24", "lad23", "lad22", "lad21", "lad20", "lad19", "lad18", "lad17", "lad"],
    )
    postal_delivery = _coerce_delivery_flag(row)

    conn.execute(
        """
        INSERT OR REPLACE INTO ons_geo_uprn_index (
            product_id,
            derivation_mode,
            uprn,
            postcode,
            oa_code,
            lsoa_code,
            msoa_code,
            lad_code,
            lad_name,
            postal_delivery,
            geographies_json,
            cached_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product.product_id,
            product.derivation_mode,
            uprn,
            postcode,
            oa_code,
            lsoa_code,
            msoa_code,
            lad_code,
            lad_name,
            postal_delivery,
            json.dumps(geographies, ensure_ascii=True, separators=(",", ":")),
            cached_at,
        ),
    )


def _ingest_product(
    *,
    conn: sqlite3.Connection,
    product: ProductConfig,
    source_path: Path,
    max_rows: int | None,
) -> tuple[int, str]:
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    inserted = 0
    chosen_key_field = ""
    with _open_csv_rows(source_path) as reader:
        chosen_key_field = _pick_key_field(reader, product.key_candidates)
        conn.execute("DELETE FROM ons_geo_rows WHERE product_id = ?", (product.product_id,))
        if product.key_type == "uprn":
            conn.execute("DELETE FROM ons_geo_uprn_index WHERE product_id = ?", (product.product_id,))
        for row in reader:
            if not isinstance(row, dict):
                continue
            raw_key = row.get(chosen_key_field)
            if raw_key is None:
                continue
            key_norm = normalize_key(product.key_type, str(raw_key))
            if key_norm is None:
                continue
            row_json = json.dumps(row, ensure_ascii=True, separators=(",", ":"))
            conn.execute(
                """
                INSERT OR REPLACE INTO ons_geo_rows (
                    product_id,
                    key_type,
                    key_norm,
                    derivation_mode,
                    release,
                    source_name,
                    product_priority,
                    row_json,
                    cached_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product.product_id,
                    product.key_type,
                    key_norm,
                    product.derivation_mode,
                    product.release,
                    product.title,
                    product.priority,
                    row_json,
                    now_iso,
                ),
            )
            if product.key_type == "uprn":
                _insert_uprn_index_row(
                    conn=conn,
                    product=product,
                    uprn=key_norm,
                    row=row,
                    cached_at=now_iso,
                )
            inserted += 1
            if max_rows is not None and inserted >= max_rows:
                break
    conn.execute(
        """
        INSERT OR REPLACE INTO ons_geo_products (
            product_id,
            key_type,
            derivation_mode,
            release,
            source_name,
            source_path,
            source_sha256,
            record_count,
            ingested_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product.product_id,
            product.key_type,
            product.derivation_mode,
            product.release,
            product.title,
            str(source_path),
            _sha256_file(source_path),
            inserted,
            now_iso,
        ),
    )
    return inserted, chosen_key_field


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh local ONS geography cache for ONSPD/ONSUD/NSPL/NSUL."
    )
    parser.add_argument(
        "--sources",
        default=str(DEFAULT_SOURCES_PATH),
        help="Path to ons geo sources manifest JSON",
    )
    parser.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        help="Directory for cache artifacts",
    )
    parser.add_argument(
        "--index-path",
        default=str(DEFAULT_INDEX_PATH),
        help="Path to write cache index JSON",
    )
    parser.add_argument("--db-name", default=DEFAULT_DB_NAME, help="SQLite database filename")
    parser.add_argument(
        "--product-file",
        action="append",
        default=[],
        help="Product input override as PRODUCT_ID=/path/to/file (repeatable)",
    )
    parser.add_argument(
        "--product-url",
        action="append",
        default=[],
        help="Product URL override as PRODUCT_ID=https://... (repeatable)",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional row limit per product",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="HTTP timeout seconds for downloads",
    )
    parser.add_argument("--dry-run", action="store_true", help="Resolve sources but do not ingest")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources_path = Path(args.sources).resolve()
    cache_dir = Path(args.cache_dir).resolve()
    index_path = Path(args.index_path).resolve()
    db_name = str(args.db_name)
    raw_dir = cache_dir / "raw"

    try:
        file_overrides = _parse_map_args(args.product_file)
        url_overrides = _parse_map_args(args.product_url)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    version, products = _load_products(sources_path)
    if not products:
        raise SystemExit("No valid products found in sources manifest")

    cache_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    summary_products: list[dict[str, Any]] = []
    db_path = cache_dir / db_name

    conn: sqlite3.Connection | None = None
    if not args.dry_run:
        conn = sqlite3.connect(str(db_path))
        ensure_schema(conn)

    for product in products:
        status = "skipped"
        source_path: Path | None = None
        error: str | None = None
        record_count = 0
        key_field = ""

        if product.product_id in file_overrides:
            source_path = Path(file_overrides[product.product_id]).expanduser().resolve()
            if not source_path.exists():
                error = f"Missing override file: {source_path}"
        else:
            source_url = url_overrides.get(product.product_id, product.source_url)
            if source_url:
                try:
                    suffix = Path(source_url).suffix or ".csv"
                    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
                    target = raw_dir / f"{product.product_id}-{timestamp}{suffix}"
                    source_path = _download(source_url, target, timeout=float(args.timeout))
                except Exception as exc:  # pragma: no cover - network variability
                    error = str(exc)
            else:
                error = "No source provided. Use --product-file or --product-url."

        if error is not None:
            status = "error"
        elif args.dry_run:
            status = "resolved"
        elif source_path is None:
            status = "error"
            error = "Source path could not be resolved."
        else:
            assert conn is not None
            try:
                record_count, key_field = _ingest_product(
                    conn=conn,
                    product=product,
                    source_path=source_path,
                    max_rows=args.max_rows,
                )
                conn.commit()
                status = "ingested"
            except Exception as exc:
                conn.rollback()
                status = "error"
                error = str(exc)

        summary_products.append(
            {
                "id": product.product_id,
                "title": product.title,
                "keyType": product.key_type,
                "derivationMode": product.derivation_mode,
                "priority": product.priority,
                "release": product.release,
                "status": status,
                "records": record_count,
                "keyField": key_field or None,
                "sourcePath": _display_path(source_path) if source_path else None,
                "sourceSha256": (
                    _sha256_file(source_path)
                    if source_path and source_path.exists()
                    else None
                ),
                "error": error,
            }
        )

    if conn is not None:
        conn.close()

    payload = {
        "version": version,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cache": {
            "cacheDir": _display_path(cache_dir),
            "dbPath": _display_path(db_path),
        },
        "products": summary_products,
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
