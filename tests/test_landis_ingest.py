from __future__ import annotations

from scripts import landis_ingest


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
