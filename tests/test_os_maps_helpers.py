from __future__ import annotations


def test_os_maps_feature_normalizers_cover_invalid_and_wrapped_shapes() -> None:
    from tools import os_maps

    assert os_maps._feature_point("bad") is None
    assert os_maps._feature_point({"type": "Feature", "geometry": {"type": "LineString"}}) is None
    assert os_maps._feature_point({"coordinates": ["bad", 51.5]}) is None
    point = os_maps._feature_point({"lng": "-0.1", "lat": "51.5", "properties": {"kind": "p"}})
    assert point == {
        "type": "Feature",
        "properties": {"kind": "p"},
        "geometry": {"type": "Point", "coordinates": [-0.1, 51.5]},
    }

    assert os_maps._feature_line("bad") is None
    assert os_maps._feature_line({"type": "Feature", "geometry": {"type": "Point"}}) is None
    line = os_maps._feature_line(
        {
            "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
            "properties": {"kind": "l"},
        }
    )
    assert line is not None
    assert line["properties"] == {"kind": "l"}

    assert os_maps._feature_polygon("bad") is None
    assert os_maps._feature_polygon({"type": "Feature", "geometry": {"type": "Point"}}) is None
    polygon = os_maps._feature_polygon(
        {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
            },
            "properties": {"kind": "poly"},
        }
    )
    assert polygon is not None
    assert polygon["properties"] == {"kind": "poly"}


def test_os_maps_collection_normalizers_cover_empty_inputs() -> None:
    from tools import os_maps

    assert os_maps._normalize_feature_collection(None, kind="point") == []
    assert os_maps._normalize_feature_collection({"type": "FeatureCollection"}, kind="point") == []
    assert os_maps._normalize_feature_collection("bad", kind="point") == []
    assert os_maps._normalize_feature_collection([{"coordinates": [1, 2]}], kind="point")
    assert os_maps._normalize_feature_collection(
        [{"geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}}],
        kind="line",
    )
    assert os_maps._normalize_feature_collection(
        [
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                }
            }
        ],
        kind="polygon",
    )
    assert os_maps._normalize_feature_collection([{"coordinates": [1, 2]}], kind="other") == []


def test_os_maps_build_uprn_features_filters_bad_rows() -> None:
    from tools import os_maps

    assert os_maps._build_uprn_features("bad") == []
    features = os_maps._build_uprn_features(
        [
            "bad",
            {"uprn": "missing-lon", "lat": 51.5},
            {"uprn": "missing-lat", "lon": -0.1},
            {"uprn": "ok", "lon": "-0.1", "lat": "51.5", "address": "1 Test Street"},
        ]
    )
    assert len(features) == 1
    assert features[0]["properties"]["uprn"] == "ok"
