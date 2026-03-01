from __future__ import annotations

import json
import sqlite3

from server.ons_geo_cache import (
    ONSGeoCache,
    ONSGeoCacheReadError,
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


def test_ensure_schema_creates_uprn_index_table(tmp_path) -> None:
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
            "ONSUD",
            "uprn",
            "exact",
            "2026-02",
            "ONSUD",
            "onsud.csv",
            "x",
            1,
            "2026-02-22T00:00:00Z",
        ),
    )
    conn.execute(
        """
        INSERT INTO ons_geo_uprn_index (
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
            "ONSUD",
            "exact",
            "100023336959",
            "CV12GT",
            "E001",
            "E0101",
            "E0201",
            "E08000026",
            "Coventry",
            1,
            "{}",
            "2026-02-22T00:00:00Z",
        ),
    )
    conn.commit()
    row = conn.execute(
        """
        SELECT uprn, lad_code, lad_name, postal_delivery
        FROM ons_geo_uprn_index
        WHERE uprn = ?
        """,
        ("100023336959",),
    ).fetchone()
    conn.close()
    assert row == ("100023336959", "E08000026", "Coventry", 1)


def test_lookup_raises_cache_read_error_when_schema_is_missing(tmp_path) -> None:
    cache = ONSGeoCache(
        cache_dir=tmp_path,
        db_name="ons_geo_cache.sqlite",
        index_path=tmp_path / "ons_geo_cache_index.json",
    )
    conn = sqlite3.connect(str(cache.db_path))
    conn.execute("CREATE TABLE not_the_expected_schema (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    try:
        cache.lookup(key_type="postcode", key_value="SW1A 1AA", derivation_mode="exact")
    except ONSGeoCacheReadError as exc:
        assert "Failed to query cache database" in str(exc)
    else:
        raise AssertionError("Expected ONSGeoCacheReadError for unreadable cache schema")
