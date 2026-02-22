from __future__ import annotations

import json
import sqlite3

from server.ons_geo_cache import (
    ONSGeoCache,
    ensure_schema,
    extract_geography_fields,
    normalize_derivation_mode,
    normalize_postcode,
    normalize_uprn,
)


def test_normalize_postcode_and_uprn() -> None:
    assert normalize_postcode(" sw1a 1aa ") == "SW1A1AA"
    assert normalize_postcode("not-a-postcode") is None
    assert normalize_uprn(" 100023336959 ") == "100023336959"
    assert normalize_uprn("abc123") is None
    assert normalize_derivation_mode("best_fit") == "best_fit"
    assert normalize_derivation_mode("invalid") is None


def test_extract_geography_fields_handles_code_name_pairs() -> None:
    fields = extract_geography_fields(
        {
            "LAD24CD": "E09000033",
            "LAD24NM": "Westminster",
            "MSOA11CD": "E02006800",
            "MSOA11NM": "Westminster 001",
            "ignored": "value",
        }
    )
    assert fields["lad24"]["code"] == "E09000033"
    assert fields["lad24"]["name"] == "Westminster"
    assert fields["msoa11"]["code"] == "E02006800"
    assert fields["msoa11"]["name"] == "Westminster 001"
    assert "ignored" not in fields


def test_lookup_prefers_higher_priority_product(tmp_path) -> None:
    cache = ONSGeoCache(
        cache_dir=tmp_path,
        db_name="ons_geo_cache.sqlite",
        index_path=tmp_path / "ons_geo_cache_index.json",
    )
    conn = sqlite3.connect(str(cache.db_path))
    ensure_schema(conn)
    conn.execute(
        """
        INSERT INTO ons_geo_products (
            product_id,
            key_type,
            derivation_mode,
            release,
            source_name,
            source_path,
            source_sha256,
            record_count,
            ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ONSPD_SECONDARY",
            "postcode",
            "exact",
            "2026-02",
            "ONSPD Secondary",
            "onspd_secondary.csv",
            "a",
            1,
            "2026-02-22T00:00:00Z",
        ),
    )
    conn.execute(
        """
        INSERT INTO ons_geo_products (
            product_id,
            key_type,
            derivation_mode,
            release,
            source_name,
            source_path,
            source_sha256,
            record_count,
            ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ONSPD_PRIMARY",
            "postcode",
            "exact",
            "2026-02",
            "ONSPD Primary",
            "onspd_primary.csv",
            "b",
            1,
            "2026-02-22T00:00:00Z",
        ),
    )
    conn.execute(
        """
        INSERT INTO ons_geo_rows (
            product_id,
            key_type,
            key_norm,
            derivation_mode,
            release,
            source_name,
            product_priority,
            row_json,
            cached_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ONSPD_SECONDARY",
            "postcode",
            "SW1A1AA",
            "exact",
            "2026-02",
            "ONSPD Secondary",
            20,
            json.dumps({"LAD24CD": "E09000033", "LAD24NM": "Westminster"}),
            "2026-02-22T00:00:00Z",
        ),
    )
    conn.execute(
        """
        INSERT INTO ons_geo_rows (
            product_id,
            key_type,
            key_norm,
            derivation_mode,
            release,
            source_name,
            product_priority,
            row_json,
            cached_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ONSPD_PRIMARY",
            "postcode",
            "SW1A1AA",
            "exact",
            "2026-02",
            "ONSPD Primary",
            10,
            json.dumps({"LAD24CD": "E09000044", "LAD24NM": "City of London"}),
            "2026-02-22T00:00:00Z",
        ),
    )
    conn.commit()
    conn.close()

    result = cache.lookup(key_type="postcode", key_value="SW1A 1AA", derivation_mode="exact")
    assert result is not None
    assert result.row["LAD24CD"] == "E09000044"
