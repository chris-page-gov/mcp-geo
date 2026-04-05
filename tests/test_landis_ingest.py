from __future__ import annotations

import json

from scripts import landis_ingest
from scripts import landis_archive_triage, landis_phase2_ingest


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
    (item_dir / "item_detail.json").write_text(json.dumps({"tags": ["natmap"]}) + "\n", encoding="utf-8")
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
        json.dumps({"publicItems": [{"slug": "host"}], "dataGovPackages": [{"name": "pkg"}]}) + "\n",
        encoding="utf-8",
    )

    manifest = landis_archive_triage.build_manifest(portal_root, release_root)
    assert manifest["summary"]["portalItems"] == 1
    assert manifest["portalItems"][0]["runtimeFamily"] == "natmap"
    assert manifest["portalItems"][0]["recordCount"] == 42
