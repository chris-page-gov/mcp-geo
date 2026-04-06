from __future__ import annotations

import json
from pathlib import Path

from scripts import landis_archive_triage, landis_ingest, landis_phase2_ingest


def _write_phase2_dataset(portal_root: Path, dataset_name: str) -> None:
    item_dir = portal_root / "data_source" / f"abc_{dataset_name}"
    feature_dir = item_dir / "feature_service"
    layers_dir = feature_dir / "layers" / dataset_name
    layers_dir.mkdir(parents=True)
    records_path = layers_dir / "records_batch_0001.geojson"
    records_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (item_dir / "inventory_record.json").write_text(
        json.dumps({"id": "abc", "title": dataset_name}) + "\n",
        encoding="utf-8",
    )
    (item_dir / "item_detail.json").write_text(
        json.dumps({"licenseInfo": "test"}) + "\n",
        encoding="utf-8",
    )
    (feature_dir / "download_summary.json").write_text(
        json.dumps(
            {
                "serviceUrl": f"https://example.test/{dataset_name}",
                "layers": [{"files": [str(records_path)]}],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _write_complete_portal_archive(portal_root: Path) -> None:
    portal_root.mkdir(parents=True, exist_ok=True)
    for dataset_name in landis_phase2_ingest._required_portal_dataset_names():
        _write_phase2_dataset(portal_root, dataset_name)


def test_normalize_soilscapes_feature_maps_expected_fields() -> None:
    row = landis_ingest._normalize_soilscapes_feature(
        {
            "type": "Feature",
            "properties": {
                "class_code": "12",
                "class_name": "Freely draining",
                "texture": "loamy",
                "drainage": "free",
                "carbon": "moderate",
                "habitat": "mixed arable",
            },
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        },
        dataset_version="2026-mvp",
        source_url="https://example.test/soilscapes",
        license_name="test-licence",
    )
    assert row["class_code"] == "12"
    assert row["class_name"] == "Freely draining"
    assert row["dominant_texture"] == "loamy"
    assert row["geom"].startswith("{")


def test_normalize_pipe_risk_feature_maps_expected_fields() -> None:
    row = landis_ingest._normalize_pipe_risk_feature(
        {
            "type": "Feature",
            "properties": {
                "shrink_code": "S2",
                "shrink_label": "Low",
                "shrink_score": 2,
                "corrosion_code": "C3",
                "corrosion_label": "Moderate",
                "corrosion_score": 3,
            },
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        },
        dataset_version="2026-mvp",
        source_url="https://example.test/pipe-risk",
        license_name="test-licence",
    )
    assert row["shrink_swell_code"] == "S2"
    assert row["corrosion_code"] == "C3"
    assert row["corrosion_score"] == 3


def test_load_geojson_features_rejects_non_feature_collection(tmp_path) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text('{"type":"Polygon"}', encoding="utf-8")
    try:
        landis_ingest._load_geojson_features(bad_path)
    except ValueError as exc:
        assert "FeatureCollection" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid GeoJSON payload")


def test_phase2_normalizers_map_expected_fields() -> None:
    natmap_row = landis_phase2_ingest._normalize_natmap_polygon_feature(
        {
            "type": "Feature",
            "properties": {
                "MUSID": "MU1",
                "MAP_SYMBOL": "SX1",
                "MU_NAME": "Freely draining loams",
                "DESC_": "desc",
                "SOILSCAPE": "Soilscape 8",
            },
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        },
        dataset_version="2026-03-31-portal",
        source_url="https://portal.landis.org.uk/",
        license_name="test",
        updated_at="2026-03-30T12:00:00+00:00",
    )
    assert natmap_row["map_unit_id"] == "MU1"
    assert natmap_row["soilscape"] == "Soilscape 8"
    assert natmap_row["updated_at"] == "2026-03-30T12:00:00+00:00"

    thematic_row = landis_phase2_ingest._normalize_thematic_feature(
        {
            "type": "Feature",
            "properties": {"WRBCODE": "LUV", "WRB06": "Luvisols", "EXTRA": 4},
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        },
        product_id="natmap-wrb2006",
        code_key="WRBCODE",
        label_key="WRB06",
        dataset_version="2026-03-31-portal",
        source_url="https://portal.landis.org.uk/",
        license_name="test",
        updated_at="2026-03-30T12:00:00+00:00",
    )
    assert thematic_row["product_id"] == "natmap-wrb2006"
    assert json.loads(thematic_row["metrics"]) == {"EXTRA": 4}
    assert thematic_row["updated_at"] == "2026-03-30T12:00:00+00:00"

    nsi_site_row = landis_phase2_ingest._normalize_nsi_site_feature(
        {
            "type": "Feature",
            "properties": {"NSI_ID": 101, "SERIESNAME": "Wickham", "SURVEYDATE": 1712188800000},
            "geometry": {"type": "Point", "coordinates": [-1.5, 52.2]},
        },
        dataset_version="2026-03-31-portal",
        source_url="https://portal.landis.org.uk/",
        license_name="test",
        updated_at="2026-03-30T12:00:00+00:00",
    )
    assert nsi_site_row["nsi_id"] == 101
    assert nsi_site_row["series_name"] == "Wickham"
    assert nsi_site_row["survey_date"] == "2024-04-04T00:00:00+00:00"
    assert nsi_site_row["updated_at"] == "2026-03-30T12:00:00+00:00"

    nsi_obs_row = landis_phase2_ingest._normalize_nsi_observation_feature(
        {
            "type": "Feature",
            "properties": {"NSI_ID": 101, "TEXTURE": "Clay", "UPPERDEPTH": 0, "LOWERDEPTH": 30},
            "geometry": {"type": "Point", "coordinates": [-1.5, 52.2]},
        },
        dataset_id="NSIprofile",
        dataset_version="2026-03-31-portal",
        source_url="https://portal.landis.org.uk/",
        license_name="test",
        updated_at="2026-03-30T12:00:00+00:00",
    )
    assert nsi_obs_row["dataset_id"] == "NSIprofile"
    assert nsi_obs_row["observation_label"] == "Clay 0-30cm"
    assert nsi_obs_row["updated_at"] == "2026-03-30T12:00:00+00:00"


def test_landis_archive_triage_build_manifest(tmp_path) -> None:
    portal_root = tmp_path / "portal"
    item_dir = portal_root / "data_source" / "abc_NationalSoilMap"
    feature_dir = item_dir / "feature_service"
    feature_dir.mkdir(parents=True)
    (item_dir / "inventory_record.json").write_text(
        json.dumps({"id": "abc", "title": "NationalSoilMap", "type": "Feature Service"}) + "\n",
        encoding="utf-8",
    )
    (item_dir / "item_detail.json").write_text(
        json.dumps({"tags": ["natmap"]}) + "\n",
        encoding="utf-8",
    )
    (feature_dir / "download_summary.json").write_text(
        json.dumps(
            {
                "serviceUrl": "https://portal.landis.org.uk/service",
                "layers": [{"recordCount": 42, "geometryType": "esriGeometryPolygon"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    release_root = tmp_path / "release"
    release_root.mkdir()
    (release_root / "full_release_manifest.json").write_text(
        json.dumps({"publicItems": [{"slug": "host"}], "dataGovPackages": [{"name": "pkg"}]})
        + "\n",
        encoding="utf-8",
    )

    manifest = landis_archive_triage.build_manifest(portal_root, release_root)
    assert manifest["summary"]["portalItems"] == 1
    assert manifest["portalItems"][0]["runtimeFamily"] == "natmap"
    assert manifest["portalItems"][0]["recordCount"] == 42


def test_execute_schema_splits_sql_into_individual_statements(tmp_path) -> None:
    schema_sql = tmp_path / "landis_schema.sql"
    schema_sql.write_text(
        "\n".join(
            [
                "CREATE SCHEMA IF NOT EXISTS landis;",
                "CREATE TABLE IF NOT EXISTS landis.sample (id integer);",
                "CREATE INDEX IF NOT EXISTS sample_idx ON landis.sample (id);",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    statements: list[str] = []

    class _Cursor:
        def __enter__(self) -> _Cursor:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def execute(self, statement: str) -> None:
            statements.append(statement)

    class _Conn:
        def cursor(self) -> _Cursor:
            return _Cursor()

    landis_ingest._execute_schema(_Conn(), schema_sql, "landis_test")

    assert statements == [
        "CREATE SCHEMA IF NOT EXISTS landis_test;",
        "CREATE TABLE IF NOT EXISTS landis_test.sample (id integer);",
        "CREATE INDEX IF NOT EXISTS sample_idx ON landis_test.sample (id);",
    ]


def test_localize_archive_path_maps_container_mount_from_host_archive() -> None:
    portal_root = Path("/landis-data/landis_portal_archive_2026-04-04")
    raw_path = (
        "/Users/crpage/Data/landis_portal_archive_2026-04-04/data_source/"
        "abc_NationalSoilMap/feature_service/layers/00_National_Soil_Map/records_batch_0001.geojson"
    )

    localized = landis_phase2_ingest._localize_archive_path(raw_path, portal_root=portal_root)

    assert localized == (
        portal_root
        / "data_source/abc_NationalSoilMap/feature_service/layers/00_National_Soil_Map/"
        "records_batch_0001.geojson"
    )


def test_latest_portal_archive_dir_prefers_newest_non_smoke(tmp_path: Path) -> None:
    _write_complete_portal_archive(tmp_path / "landis_portal_archive_2026-04-04")
    (tmp_path / "landis_portal_archive_2026-05-01-smoke").mkdir()
    newest = tmp_path / "landis_portal_archive_2026-05-01"
    _write_complete_portal_archive(newest)

    assert landis_phase2_ingest._latest_portal_archive_dir(tmp_path) == newest


def test_latest_portal_archive_dir_skips_incomplete_newer_archive(tmp_path: Path) -> None:
    older_complete = tmp_path / "landis_portal_archive_2026-04-04"
    _write_complete_portal_archive(older_complete)
    newer_incomplete = tmp_path / "landis_portal_archive_2026-05-01"
    newer_incomplete.mkdir()

    assert landis_phase2_ingest._latest_portal_archive_dir(tmp_path) == older_complete


def test_portal_archive_validation_errors_report_missing_required_datasets(tmp_path: Path) -> None:
    portal_root = tmp_path / "landis_portal_archive_2026-04-04"
    portal_root.mkdir()
    _write_phase2_dataset(portal_root, "NationalSoilMap")

    errors = landis_phase2_ingest._portal_archive_validation_errors(portal_root)

    assert any("NATMAPsoilscapes" in error for error in errors)
