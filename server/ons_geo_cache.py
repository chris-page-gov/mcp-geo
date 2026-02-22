from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from server.config import settings

KEY_TYPES = {"postcode", "uprn"}
DERIVATION_MODES = {"exact", "best_fit"}
POSTCODE_REGEX = re.compile(r"^[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}$")


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


def normalize_derivation_mode(value: str) -> str | None:
    mode = value.strip().lower()
    return mode if mode in DERIVATION_MODES else None


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ons_geo_products (
            product_id TEXT PRIMARY KEY,
            key_type TEXT NOT NULL,
            derivation_mode TEXT NOT NULL,
            release TEXT,
            source_name TEXT,
            source_path TEXT,
            source_sha256 TEXT,
            record_count INTEGER NOT NULL DEFAULT 0,
            ingested_at TEXT NOT NULL
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
            cached_at TEXT NOT NULL,
            PRIMARY KEY (product_id, key_norm),
            FOREIGN KEY (product_id) REFERENCES ons_geo_products(product_id)
        );

        CREATE INDEX IF NOT EXISTS idx_ons_geo_lookup
        ON ons_geo_rows (key_type, derivation_mode, key_norm, product_priority);
        """
    )
    conn.commit()


@dataclass(frozen=True)
class ONSGeoLookup:
    product_id: str
    key_type: str
    derivation_mode: str
    release: str | None
    source_name: str | None
    cached_at: str | None
    row: dict[str, Any]


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
        index_path = _resolve_path(
            getattr(settings, "ONS_GEO_CACHE_INDEX_PATH", None),
            "resources/ons_geo_cache_index.json",
        )
        return cls(cache_dir=cache_dir, db_name=db_name, index_path=index_path)

    @property
    def db_path(self) -> Path:
        return self.cache_dir / self.db_name

    def available(self) -> bool:
        return self.db_path.exists() and self.db_path.is_file()

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

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                """
                SELECT
                    product_id,
                    key_type,
                    derivation_mode,
                    release,
                    source_name,
                    cached_at,
                    row_json
                FROM ons_geo_rows
                WHERE key_type = ?
                  AND derivation_mode = ?
                  AND key_norm = ?
                ORDER BY product_priority ASC, product_id ASC
                LIMIT 1
                """,
                (normalized_key_type, normalized_mode, key_norm),
            ).fetchone()
        except sqlite3.Error:
            return None
        finally:
            conn.close()

        if row is None:
            return None

        try:
            payload = json.loads(str(row["row_json"]))
        except json.JSONDecodeError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}

        return ONSGeoLookup(
            product_id=str(row["product_id"]),
            key_type=str(row["key_type"]),
            derivation_mode=str(row["derivation_mode"]),
            release=str(row["release"]) if row["release"] is not None else None,
            source_name=str(row["source_name"]) if row["source_name"] is not None else None,
            cached_at=str(row["cached_at"]) if row["cached_at"] is not None else None,
            row=payload,
        )


_GEOGRAPHY_SUFFIX_RE = re.compile(r"^(?P<stem>[A-Za-z0-9_]+?)(?P<suffix>CD|NM)$")


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
        else:
            entry["name"] = text_value
    return geographies
