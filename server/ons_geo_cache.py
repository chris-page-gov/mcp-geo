from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from server.config import settings
from server.geography_levels import (
    AREA_LEVEL_COLUMN_MAP,
    infer_area_level_from_code as _infer_area_level_from_code,
    normalize_area_level,
)

KEY_TYPES = {"postcode", "uprn"}
DERIVATION_MODES = {"exact", "best_fit"}
POSTCODE_REGEX = re.compile(r"^[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}$")
SAFE_CACHE_DB_NAME_REGEX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

_GEOGRAPHY_SUFFIX_RE = re.compile(r"^(?P<stem>[A-Za-z0-9_]+?)(?P<suffix>CD|NM|NMW|NW)$")


def _resolve_path(raw: str | None, default: str) -> Path:
    value = str(raw or default)
    path = Path(value)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / value
    return path


def normalize_postcode(value: str) -> str | None:
    normalized = re.sub(r"\s+", "", value.strip().upper())
    if not POSTCODE_REGEX.match(normalized):
        return None
    return normalized


def normalize_uprn(value: str) -> str | None:
    normalized = re.sub(r"\s+", "", value.strip())
    if not normalized or not normalized.isdigit():
        return None
    return normalized


def normalize_key(key_type: str, value: str) -> str | None:
    kind = key_type.strip().lower()
    if kind == "postcode":
        return normalize_postcode(value)
    if kind == "uprn":
        return normalize_uprn(value)
    return None


def validate_cache_db_name(value: str) -> str:
    name = str(value or "").strip()
    path = Path(name)
    if (
        not name
        or path.is_absolute()
        or path.name != name
        or name in {".", ".."}
        or ".." in path.parts
        or not SAFE_CACHE_DB_NAME_REGEX.fullmatch(name)
    ):
        raise ValueError("ONS geo cache database name must be a safe filename")
    return name


def normalize_derivation_mode(value: str) -> str | None:
    mode = value.strip().lower()
    return mode if mode in DERIVATION_MODES else None


def infer_area_level_from_code(value: str) -> str | None:
    return _infer_area_level_from_code(value)


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _ensure_columns(
    conn: sqlite3.Connection,
    table_name: str,
    required_columns: dict[str, str],
) -> None:
    existing = _table_columns(conn, table_name)
    for column_name, column_sql in required_columns.items():
        if column_name in existing:
            continue
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ons_geo_products (
            product_id TEXT PRIMARY KEY,
            dataset_kind TEXT NOT NULL DEFAULT 'product',
            key_type TEXT,
            derivation_mode TEXT,
            release TEXT,
            resolved_release TEXT,
            source_name TEXT,
            source_path TEXT,
            resolved_source_url TEXT,
            resolver_type TEXT,
            source_format TEXT,
            source_sha256 TEXT,
            schema_fingerprint TEXT,
            schema_validation_json TEXT,
            record_count INTEGER NOT NULL DEFAULT 0,
            status TEXT,
            ingested_at TEXT NOT NULL,
            retrieved_at TEXT
        );

        CREATE TABLE IF NOT EXISTS ons_geo_rows (
            product_id TEXT NOT NULL,
            key_type TEXT NOT NULL,
            key_norm TEXT NOT NULL,
            derivation_mode TEXT NOT NULL,
            release TEXT,
            source_name TEXT,
            product_priority INTEGER NOT NULL DEFAULT 100,
            row_json TEXT NOT NULL,
            normalized_json TEXT,
            cached_at TEXT NOT NULL,
            PRIMARY KEY (product_id, key_norm),
            FOREIGN KEY (product_id) REFERENCES ons_geo_products(product_id)
        );

        CREATE INDEX IF NOT EXISTS idx_ons_geo_lookup
        ON ons_geo_rows (key_type, derivation_mode, key_norm, product_priority);

        CREATE TABLE IF NOT EXISTS ons_geo_uprn_index (
            product_id TEXT NOT NULL,
            derivation_mode TEXT NOT NULL,
            uprn TEXT NOT NULL,
            postcode TEXT,
            oa_code TEXT,
            lsoa_code TEXT,
            msoa_code TEXT,
            parish_code TEXT,
            parish_name TEXT,
            parish_name_welsh TEXT,
            lad_code TEXT,
            lad_name TEXT,
            ward_code TEXT,
            ward_name TEXT,
            country_code TEXT,
            country_name TEXT,
            region_code TEXT,
            region_name TEXT,
            postal_delivery INTEGER,
            geographies_json TEXT,
            cached_at TEXT NOT NULL,
            PRIMARY KEY (product_id, uprn),
            FOREIGN KEY (product_id) REFERENCES ons_geo_products(product_id)
        );

        CREATE INDEX IF NOT EXISTS idx_ons_geo_uprn_by_mode_uprn
        ON ons_geo_uprn_index (derivation_mode, uprn);

        CREATE INDEX IF NOT EXISTS idx_ons_geo_uprn_by_mode_postcode
        ON ons_geo_uprn_index (derivation_mode, postcode);

        CREATE INDEX IF NOT EXISTS idx_ons_geo_uprn_by_mode_oa
        ON ons_geo_uprn_index (derivation_mode, oa_code);

        CREATE INDEX IF NOT EXISTS idx_ons_geo_uprn_by_mode_lsoa
        ON ons_geo_uprn_index (derivation_mode, lsoa_code);

        CREATE INDEX IF NOT EXISTS idx_ons_geo_uprn_by_mode_msoa
        ON ons_geo_uprn_index (derivation_mode, msoa_code);

        CREATE INDEX IF NOT EXISTS idx_ons_geo_uprn_by_mode_lad
        ON ons_geo_uprn_index (derivation_mode, lad_code);

        CREATE TABLE IF NOT EXISTS ons_geo_msoa_display_names (
            dataset_id TEXT NOT NULL,
            msoa_code TEXT NOT NULL,
            official_name TEXT,
            official_name_welsh TEXT,
            display_name TEXT NOT NULL,
            display_name_welsh TEXT,
            local_authority_name TEXT,
            name_type TEXT,
            source_version TEXT,
            published_date TEXT,
            license TEXT,
            source_url TEXT,
            record_json TEXT NOT NULL,
            ingested_at TEXT NOT NULL,
            PRIMARY KEY (dataset_id, msoa_code)
        );

        CREATE INDEX IF NOT EXISTS idx_ons_geo_msoa_display_names_code
        ON ons_geo_msoa_display_names (msoa_code);

        CREATE TABLE IF NOT EXISTS ons_geo_code_reference (
            dataset_id TEXT NOT NULL,
            code TEXT NOT NULL,
            code_family TEXT,
            name TEXT,
            status TEXT NOT NULL,
            successor_code TEXT,
            successor_name TEXT,
            level TEXT,
            record_json TEXT NOT NULL,
            ingested_at TEXT NOT NULL,
            PRIMARY KEY (dataset_id, code)
        );

        CREATE INDEX IF NOT EXISTS idx_ons_geo_code_reference_code
        ON ons_geo_code_reference (code);

        CREATE INDEX IF NOT EXISTS idx_ons_geo_code_reference_status
        ON ons_geo_code_reference (status);
        """
    )

    _ensure_columns(
        conn,
        "ons_geo_products",
        {
            "dataset_kind": "TEXT NOT NULL DEFAULT 'product'",
            "resolved_release": "TEXT",
            "resolved_source_url": "TEXT",
            "resolver_type": "TEXT",
            "source_format": "TEXT",
            "schema_fingerprint": "TEXT",
            "schema_validation_json": "TEXT",
            "status": "TEXT",
            "retrieved_at": "TEXT",
        },
    )
    _ensure_columns(conn, "ons_geo_rows", {"normalized_json": "TEXT"})
    _ensure_columns(
        conn,
        "ons_geo_uprn_index",
        {
            "ward_code": "TEXT",
            "ward_name": "TEXT",
            "parish_code": "TEXT",
            "parish_name": "TEXT",
            "parish_name_welsh": "TEXT",
            "country_code": "TEXT",
            "country_name": "TEXT",
            "region_code": "TEXT",
            "region_name": "TEXT",
        },
    )
    # These indexes depend on migration-added columns for older cache files.
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_ons_geo_uprn_by_mode_ward
        ON ons_geo_uprn_index (derivation_mode, ward_code);

        CREATE INDEX IF NOT EXISTS idx_ons_geo_uprn_by_mode_parish
        ON ons_geo_uprn_index (derivation_mode, parish_code);

        CREATE INDEX IF NOT EXISTS idx_ons_geo_uprn_by_mode_country
        ON ons_geo_uprn_index (derivation_mode, country_code);

        CREATE INDEX IF NOT EXISTS idx_ons_geo_uprn_by_mode_region
        ON ons_geo_uprn_index (derivation_mode, region_code);
        """
    )
    conn.commit()


@dataclass(frozen=True)
class ONSGeoLookup:
    product_id: str
    key_type: str
    derivation_mode: str
    release: str | None
    resolved_release: str | None
    source_name: str | None
    source_format: str | None
    schema_fingerprint: str | None
    resolved_source_url: str | None
    cached_at: str | None
    row: dict[str, Any]
    normalized: dict[str, Any]


class ONSGeoCacheReadError(RuntimeError):
    """Raised when the on-disk ONS geo cache exists but cannot be queried."""


class ONSGeoCache:
    def __init__(
        self,
        *,
        cache_dir: Path,
        db_name: str,
        index_path: Path,
    ) -> None:
        self.cache_dir = cache_dir
        self.db_name = db_name
        self.index_path = index_path

    @classmethod
    def from_settings(cls) -> ONSGeoCache:
        cache_dir = _resolve_path(
            getattr(settings, "ONS_GEO_CACHE_DIR", None),
            "data/cache/ons_geo",
        )
        db_name = str(
            getattr(settings, "ONS_GEO_CACHE_DB", "ons_geo_cache.sqlite")
            or "ons_geo_cache.sqlite"
        )
        db_name = validate_cache_db_name(db_name)
        index_path = _resolve_path(
            getattr(settings, "ONS_GEO_CACHE_INDEX_PATH", None),
            "resources/ons_geo_cache_index.json",
        )
        return cls(cache_dir=cache_dir, db_name=db_name, index_path=index_path)

    @property
    def db_path(self) -> Path:
        cache_dir = self.cache_dir.resolve()
        db_path = (cache_dir / validate_cache_db_name(self.db_name)).resolve()
        try:
            db_path.relative_to(cache_dir)
        except ValueError as exc:
            raise ValueError("ONS geo cache database path must stay inside cache_dir") from exc
        return db_path

    def available(self) -> bool:
        return self.db_path.exists() and self.db_path.is_file()

    def connect(self, *, row_factory: bool = False) -> sqlite3.Connection:
        """Open the cache and apply additive schema migrations before reads."""
        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            if row_factory:
                conn.row_factory = sqlite3.Row
            ensure_schema(conn)
            return conn
        except sqlite3.Error as exc:
            if conn is not None:
                conn.close()
            raise ONSGeoCacheReadError(
                f"Failed to prepare cache database at {self.db_path}: {exc}"
            ) from exc

    def load_index(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.index_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def lookup(self, *, key_type: str, key_value: str, derivation_mode: str) -> ONSGeoLookup | None:
        normalized_key_type = key_type.strip().lower()
        normalized_mode = normalize_derivation_mode(derivation_mode)
        if normalized_key_type not in KEY_TYPES or normalized_mode is None:
            return None

        key_norm = normalize_key(normalized_key_type, key_value)
        if key_norm is None:
            return None

        if not self.available():
            return None

        conn: sqlite3.Connection | None = None
        try:
            conn = self.connect(row_factory=True)
            row = conn.execute(
                """
                SELECT
                    r.product_id,
                    r.key_type,
                    r.derivation_mode,
                    COALESCE(p.release, r.release) AS release,
                    p.resolved_release,
                    COALESCE(p.source_name, r.source_name) AS source_name,
                    p.source_format,
                    p.schema_fingerprint,
                    p.resolved_source_url,
                    r.cached_at,
                    r.row_json,
                    r.normalized_json
                FROM ons_geo_rows AS r
                LEFT JOIN ons_geo_products AS p
                  ON p.product_id = r.product_id
                WHERE r.key_type = ?
                  AND r.derivation_mode = ?
                  AND r.key_norm = ?
                ORDER BY r.product_priority ASC, r.product_id ASC
                LIMIT 1
                """,
                (normalized_key_type, normalized_mode, key_norm),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ONSGeoCacheReadError(
                f"Failed to query cache database at {self.db_path}: {exc}"
            ) from exc
        finally:
            if conn is not None:
                conn.close()

        if row is None:
            return None

        payload = _decode_json_object(row["row_json"])
        normalized = _decode_json_object(row["normalized_json"])

        return ONSGeoLookup(
            product_id=str(row["product_id"]),
            key_type=str(row["key_type"]),
            derivation_mode=str(row["derivation_mode"]),
            release=_optional_text(row["release"]),
            resolved_release=_optional_text(row["resolved_release"]),
            source_name=_optional_text(row["source_name"]),
            source_format=_optional_text(row["source_format"]),
            schema_fingerprint=_optional_text(row["schema_fingerprint"]),
            resolved_source_url=_optional_text(row["resolved_source_url"]),
            cached_at=_optional_text(row["cached_at"]),
            row=payload,
            normalized=normalized,
        )

    def area_member_counts(
        self,
        *,
        area_code: str,
        area_level: str,
        derivation_mode: str,
    ) -> dict[str, int] | None:
        normalized_level = normalize_area_level(area_level)
        normalized_mode = normalize_derivation_mode(derivation_mode)
        if normalized_level is None or normalized_mode is None:
            return None
        column = AREA_LEVEL_COLUMN_MAP.get(normalized_level)
        if column is None:
            return None
        code = area_code.strip().upper()
        if not code:
            return None
        if not self.available():
            return None

        conn: sqlite3.Connection | None = None
        try:
            conn = self.connect()
            row = conn.execute(
                f"""
                SELECT
                    COUNT(*) AS uprn_count,
                    COUNT(DISTINCT postcode) AS postcode_count,
                    COALESCE(SUM(CASE WHEN postal_delivery = 1 THEN 1 ELSE 0 END), 0)
                        AS postal_delivery_uprn_count
                FROM ons_geo_uprn_index
                WHERE derivation_mode = ?
                  AND {column} = ?
                """,
                (normalized_mode, code),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ONSGeoCacheReadError(
                f"Failed to query cache database at {self.db_path}: {exc}"
            ) from exc
        finally:
            if conn is not None:
                conn.close()

        if row is None:
            return None
        return {
            "uprnCount": int(row[0] or 0),
            "postcodeCount": int(row[1] or 0),
            "postalDeliveryUprnCount": int(row[2] or 0),
        }


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decode_json_object(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    try:
        payload = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def extract_geography_fields(row: dict[str, Any]) -> dict[str, dict[str, str]]:
    geographies: dict[str, dict[str, str]] = {}
    for raw_key, raw_value in row.items():
        if raw_value is None:
            continue
        text_value = str(raw_value).strip()
        if not text_value:
            continue
        key = str(raw_key).strip()
        if not key:
            continue
        normalized_key = key.replace(" ", "").replace("-", "").upper()
        match = _GEOGRAPHY_SUFFIX_RE.match(normalized_key)
        if match is None:
            continue
        stem = match.group("stem").rstrip("_").lower()
        suffix = match.group("suffix")
        entry = geographies.setdefault(stem, {})
        if suffix == "CD":
            entry["code"] = text_value
        elif suffix == "NM":
            entry["name"] = text_value
        else:
            entry["nameWelsh"] = text_value
    return geographies
