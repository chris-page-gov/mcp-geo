from __future__ import annotations

import json
import sqlite3

from server.geography_levels import (
    AREA_SUMMARY_LEVEL_RANK,
    NOMIS_GEOGRAPHY_TYPE_MATCHERS,
    area_summary_target_is_compatible,
    boundary_search_priority_levels,
    infer_admin_levels_from_text,
    normalize_admin_level,
)
from server.ons_geo_cache import (
    ONSGeoCache,
    ONSGeoCacheReadError,
    ensure_schema,
    extract_geography_fields,
    infer_area_level_from_code,
    normalize_area_level,
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
    assert normalize_area_level("parncp") == "PARISH"
    assert normalize_area_level("non civil parished") == "PARISH"
    assert infer_area_level_from_code("E04000001") == "PARISH"
    assert infer_area_level_from_code("W04000001") == "PARISH"
    assert infer_area_level_from_code("E43000246") == "PARISH"


def test_shared_geography_level_registry_covers_parish_and_country_aliases() -> None:
    assert normalize_admin_level("parncp") == "PARISH"
    assert normalize_admin_level("non civil parished") == "PARISH"
    assert normalize_admin_level("country") == "NATION"
    assert infer_admin_levels_from_text("Nationwide statistics") == ["NATION"]
    assert infer_admin_levels_from_text("PARNCP boundary") == ["PARISH"]
    assert boundary_search_priority_levels()[:3] == ("WARD", "PARISH", "DISTRICT")
    assert "parish" in NOMIS_GEOGRAPHY_TYPE_MATCHERS["PARISH"]
    assert "PARISH" not in AREA_SUMMARY_LEVEL_RANK
    assert area_summary_target_is_compatible("MSOA", "REGION") is True
    assert area_summary_target_is_compatible("MSOA", "PARISH") is False
    assert area_summary_target_is_compatible("PARISH", "PARISH") is True
    assert area_summary_target_is_compatible("PARISH", "MSOA") is False


def test_extract_geography_fields_handles_code_name_pairs() -> None:
    fields = extract_geography_fields(
        {
            "LAD24CD": "E09000033",
            "LAD24NM": "Westminster",
            "MSOA11CD": "E02006800",
            "MSOA11NM": "Westminster 001",
            "PARNCP25CD": "E04000001",
            "PARNCP25NM": "Example Parish",
            "PARNCP25NW": "Plwyf Enghreifftiol",
            "ignored": "value",
        }
    )
    assert fields["lad24"]["code"] == "E09000033"
    assert fields["lad24"]["name"] == "Westminster"
    assert fields["msoa11"]["code"] == "E02006800"
    assert fields["msoa11"]["name"] == "Westminster 001"
    assert fields["parncp25"]["code"] == "E04000001"
    assert fields["parncp25"]["name"] == "Example Parish"
    assert fields["parncp25"]["nameWelsh"] == "Plwyf Enghreifftiol"
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
        SELECT uprn, lad_code, lad_name, postal_delivery, ward_code, country_code, region_code
        FROM ons_geo_uprn_index
        WHERE uprn = ?
        """,
        ("100023336959",),
    ).fetchone()
    tables = {
        item[0]
        for item in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    conn.close()
    assert row == ("100023336959", "E08000026", "Coventry", 1, None, None, None)
    assert "ons_geo_code_reference" in tables
    assert "ons_geo_msoa_display_names" in tables


def test_ensure_schema_migrates_legacy_uprn_index_before_creating_new_indexes(tmp_path) -> None:
    db_path = tmp_path / "ons_geo_cache.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE ons_geo_products (
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

        CREATE TABLE ons_geo_rows (
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
            PRIMARY KEY (product_id, key_norm)
        );

        CREATE TABLE ons_geo_uprn_index (
            product_id TEXT NOT NULL,
            derivation_mode TEXT NOT NULL,
            uprn TEXT NOT NULL,
            postcode TEXT,
            oa_code TEXT,
            lsoa_code TEXT,
            msoa_code TEXT,
            lad_code TEXT,
            lad_name TEXT,
            postal_delivery INTEGER,
            geographies_json TEXT,
            cached_at TEXT NOT NULL,
            PRIMARY KEY (product_id, uprn)
        );
        """
    )

    ensure_schema(conn)

    columns = {
        row[1]: row[2]
        for row in conn.execute("PRAGMA table_info(ons_geo_uprn_index)").fetchall()
    }
    indexes = {
        row[1]
        for row in conn.execute("PRAGMA index_list(ons_geo_uprn_index)").fetchall()
    }
    conn.close()

    expected_columns = {
        "ward_code",
        "ward_name",
        "parish_code",
        "parish_name",
        "parish_name_welsh",
        "country_code",
        "country_name",
        "region_code",
        "region_name",
    }
    assert expected_columns <= set(columns)
    assert "idx_ons_geo_uprn_by_mode_ward" in indexes
    assert "idx_ons_geo_uprn_by_mode_parish" in indexes
    assert "idx_ons_geo_uprn_by_mode_country" in indexes
    assert "idx_ons_geo_uprn_by_mode_region" in indexes


def test_lookup_decodes_normalized_payload(tmp_path) -> None:
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
            "ONSPD",
            "postcode",
            "exact",
            "2026-02",
            "ONSPD",
            "onspd.csv",
            "hash",
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
            normalized_json,
            cached_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ONSPD",
            "postcode",
            "SW1A1AA",
            "exact",
            "2026-02",
            "ONSPD",
            10,
            json.dumps({"LAD24CD": "E09000033", "LAD24NM": "Westminster"}),
            json.dumps(
                {
                    "semanticFields": {"postcode": "SW1A1AA"},
                    "geographies": {"lad": {"currentCode": "E09000033", "status": "current"}},
                    "codeStatusSummary": {"current": 1},
                }
            ),
            "2026-02-22T00:00:00Z",
        ),
    )
    conn.commit()
    conn.close()

    result = cache.lookup(key_type="postcode", key_value="SW1A 1AA", derivation_mode="exact")
    assert result is not None
    assert result.normalized["geographies"]["lad"]["currentCode"] == "E09000033"
    assert result.normalized["codeStatusSummary"]["current"] == 1


def test_lookup_migrates_empty_sqlite_cache_with_missing_schema(tmp_path) -> None:
    cache = ONSGeoCache(
        cache_dir=tmp_path,
        db_name="ons_geo_cache.sqlite",
        index_path=tmp_path / "ons_geo_cache_index.json",
    )
    conn = sqlite3.connect(str(cache.db_path))
    conn.execute("CREATE TABLE not_the_expected_schema (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

    assert cache.lookup(key_type="postcode", key_value="SW1A 1AA", derivation_mode="exact") is None

    conn = sqlite3.connect(str(cache.db_path))
    try:
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        conn.close()
    assert "ons_geo_rows" in tables
    assert "ons_geo_uprn_index" in tables


def test_lookup_raises_cache_read_error_when_sqlite_file_is_unreadable(tmp_path) -> None:
    cache = ONSGeoCache(
        cache_dir=tmp_path,
        db_name="ons_geo_cache.sqlite",
        index_path=tmp_path / "ons_geo_cache_index.json",
    )
    cache.db_path.write_text("not a sqlite database", encoding="utf-8")

    try:
        cache.lookup(key_type="postcode", key_value="SW1A 1AA", derivation_mode="exact")
    except ONSGeoCacheReadError as exc:
        assert "Failed to prepare cache database" in str(exc)
    else:
        raise AssertionError("Expected ONSGeoCacheReadError for unreadable cache file")
