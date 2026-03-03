from __future__ import annotations

from typing import Any


def test_int_setting_handles_invalid_and_bounds() -> None:
    from tools import os_features

    assert os_features._int_setting("not-int", 7, minimum=1, maximum=10) == 7
    assert os_features._int_setting(-5, 7, minimum=1, maximum=10) == 1
    assert os_features._int_setting(25, 7, minimum=1, maximum=10) == 10
    assert os_features._int_setting(4, 7, minimum=1, maximum=10) == 4


def test_float_setting_handles_invalid_and_minimum() -> None:
    from tools import os_features

    assert os_features._float_setting("bad", 1.5, minimum=0.1) == 1.5
    assert os_features._float_setting(-4, 1.5, minimum=0.1) == 0.1
    assert os_features._float_setting(3.2, 1.5, minimum=0.1) == 3.2


def test_apply_collection_alias_variants() -> None:
    from tools import os_features

    assert os_features._apply_collection_alias("buildings") == "bld-fts-buildingpart-2"
    assert os_features._apply_collection_alias("trn-fts-roadlink-3") == "trn-ntwk-roadlink-3"
    assert os_features._apply_collection_alias("trn-fts-roadlink") == "trn-ntwk-roadlink-1"
    assert os_features._apply_collection_alias("  ") == ""
    assert os_features._apply_collection_alias("abc") == "abc"


def test_extract_unsupported_collection_cases() -> None:
    from tools import os_features

    msg = "Collection 'trn-ntwk-roadlink-99' is not a supported Collection."
    assert os_features._extract_unsupported_collection(msg) == "trn-ntwk-roadlink-99"
    assert os_features._extract_unsupported_collection(5) is None
    assert os_features._extract_unsupported_collection("other text") is None


def test_normalize_collection_tokens_removes_stopwords() -> None:
    from tools import os_features

    tokens = os_features._normalize_collection_tokens("os-trn-fts-roadlink-v1-items")
    assert "roadlink" in tokens
    assert "fts" not in tokens
    assert "items" not in tokens


def test_build_latest_by_base() -> None:
    from tools import os_features

    latest = os_features._build_latest_by_base(
        [
            "trn-ntwk-roadlink-1",
            "trn-ntwk-roadlink-7",
            "trn-ntwk-roadlink-3",
            "unversioned",
        ]
    )
    assert latest == {"trn-ntwk-roadlink": "trn-ntwk-roadlink-7"}


def test_suggest_collections_returns_empty_on_non_200(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    monkeypatch.setattr(os_features, "_client_get_json", lambda _u, _p: (500, {}), raising=True)
    assert os_features._suggest_collections_for_request("roadlink") == []


def test_suggest_collections_returns_empty_on_bad_payload(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    monkeypatch.setattr(
        os_features,
        "_client_get_json",
        lambda _u, _p: (200, {"collections": "bad"}),
        raising=True,
    )
    assert os_features._suggest_collections_for_request("roadlink") == []


def test_suggest_collections_scores_and_limits(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    def fake_get_json(_url: str, _params: dict[str, Any] | None = None):
        return 200, {
            "collections": [
                {"id": "trn-ntwk-roadlink-5"},
                {"id": "trn-ntwk-roadlink-4"},
                {"id": "trn-ntwk-pathlink-3"},
                {"id": "trn-fts-roadtrackorpath-3"},
                {"id": "bld-fts-buildingpart-2"},
                {"id": "unused"},
            ]
        }

    monkeypatch.setattr(os_features, "_client_get_json", fake_get_json, raising=True)
    out = os_features._suggest_collections_for_request("trn-fts-roadlink-99", max_items=3)
    assert out
    assert len(out) <= 3
    assert "trn-ntwk-roadlink-5" in out


def test_augment_unsupported_collection_error_passthrough_non_os_error() -> None:
    from tools import os_features

    body = {"code": "OTHER", "message": "x"}
    assert os_features._augment_unsupported_collection_error(
        body,
        requested_collection="abc",
        resolved_collection="abc",
    ) == body


def test_augment_unsupported_collection_error_passthrough_no_match() -> None:
    from tools import os_features

    body = {"code": "OS_API_ERROR", "message": "different error text"}
    assert os_features._augment_unsupported_collection_error(
        body,
        requested_collection="abc",
        resolved_collection="abc",
    ) == body


def test_augment_unsupported_collection_error_enriches_fields(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    body = {
        "code": "OS_API_ERROR",
        "message": "Collection 'trn-ntwk-roadlink-99' is not a supported Collection.",
    }
    monkeypatch.setattr(
        os_features,
        "_suggest_collections_for_request",
        lambda _value: ["trn-ntwk-roadlink-5", "trn-ntwk-pathlink-3"],
        raising=True,
    )
    out = os_features._augment_unsupported_collection_error(
        body,
        requested_collection="trn-fts-roadlink-99",
        resolved_collection="trn-ntwk-roadlink-99",
    )
    assert out["requestedCollection"] == "trn-fts-roadlink-99"
    assert out["resolvedCollection"] == "trn-ntwk-roadlink-99"
    assert out["suggestedCollections"][0] == "trn-ntwk-roadlink-5"


def test_parse_bbox_rejects_invalid_inputs() -> None:
    from tools import os_features

    assert os_features._parse_bbox([1, 2, 3]) is None
    assert os_features._parse_bbox(["x", 0, 1, 1]) is None
    assert os_features._parse_bbox([181, 0, 182, 1]) is None
    assert os_features._parse_bbox([0, 0, 0, 1]) is None


def test_parse_bbox_accepts_valid_input() -> None:
    from tools import os_features

    assert os_features._parse_bbox([-1, 50, -0.5, 50.5]) == (-1.0, 50.0, -0.5, 50.5)


def test_bbox_area_and_shrink_bbox() -> None:
    from tools import os_features

    bbox = (0.0, 0.0, 4.0, 2.0)
    assert os_features._bbox_area(bbox) == 8.0
    shrunk = os_features._shrink_bbox(bbox, factor=0.5)
    assert shrunk == (1.0, 0.5, 3.0, 1.5)


def test_clamp_bbox_area_allows_large_when_flag() -> None:
    from tools import os_features

    warnings: list[str] = []
    bbox = (0.0, 0.0, 20.0, 20.0)
    assert os_features._clamp_bbox_area(bbox, warnings=warnings, allow_large_bbox=True) == bbox
    assert warnings == []


def test_clamp_bbox_area_clamps_and_warns() -> None:
    from tools import os_features

    warnings: list[str] = []
    bbox = (0.0, 0.0, 20.0, 20.0)
    out = os_features._clamp_bbox_area(bbox, warnings=warnings, allow_large_bbox=False)
    assert out != bbox
    assert "BBOX_AREA_CLAMPED" in warnings


def test_bbox_param_roundtrip() -> None:
    from tools import os_features

    bbox = (-1.2, 52.0, -0.8, 52.3)
    encoded = os_features._bbox_to_param(bbox)
    decoded = os_features._parse_bbox_param(encoded)
    assert decoded == bbox
    assert os_features._parse_bbox_param("1,2,3") is None
    assert os_features._parse_bbox_param("a,b,c,d") is None


def test_parse_limit_behaviors() -> None:
    from tools import os_features

    warnings: list[str] = []
    assert os_features._parse_limit(None, warnings) == os_features._DEFAULT_LIMIT
    assert os_features._parse_limit(0, warnings) is None
    assert os_features._parse_limit(-1, warnings) is None
    clamped = os_features._parse_limit(os_features._MAX_LIMIT + 100, warnings)
    assert clamped == os_features._MAX_LIMIT
    assert "RESULT_LIMIT_CLAMPED" in warnings


def test_parse_offset_behaviors() -> None:
    from tools import os_features

    assert os_features._parse_offset(None) == 0
    assert os_features._parse_offset(5) == 5
    assert os_features._parse_offset(-1) is None
    assert os_features._parse_offset(" 7 ") == 7
    assert os_features._parse_offset("") == 0
    assert os_features._parse_offset("x") is None
    assert os_features._parse_offset(object()) is None


def test_parse_str_list_behaviors() -> None:
    from tools import os_features

    assert os_features._parse_str_list(None) == []
    assert os_features._parse_str_list([" a ", "b"]) == ["a", "b"]
    assert os_features._parse_str_list("bad") is None
    assert os_features._parse_str_list(["ok", ""]) is None
    assert os_features._parse_str_list(["ok", 5]) is None


def test_parse_sort_by_behaviors() -> None:
    from tools import os_features

    assert os_features._parse_sort_by(None) == []
    assert os_features._parse_sort_by("name,-height") == [("name", False), ("height", True)]
    assert os_features._parse_sort_by(["name", "-height"]) == [
        ("name", False),
        ("height", True),
    ]
    assert os_features._parse_sort_by([5]) is None
    assert os_features._parse_sort_by({"x": 1}) is None
    assert os_features._parse_sort_by("-") is None


def test_parse_polygon_rejects_non_collection_value() -> None:
    from tools import os_features

    points, error = os_features._parse_polygon("bad")
    assert points is None
    assert "polygon must be" in str(error)


def test_parse_polygon_rejects_bad_geojson_shape() -> None:
    from tools import os_features

    points, error = os_features._parse_polygon({"type": "Point", "coordinates": []})
    assert points is None
    assert error == "polygon.type must be 'Polygon'"

    points, error = os_features._parse_polygon({"type": "Polygon", "coordinates": []})
    assert points is None
    assert error == "polygon.coordinates must contain at least one ring"


def test_parse_polygon_rejects_small_or_unclosed_or_distinct() -> None:
    from tools import os_features

    points, error = os_features._parse_polygon([[0, 0], [1, 0], [0, 0]])
    assert points is None
    assert "at least 4" in str(error)

    points, error = os_features._parse_polygon([[0, 0], [1, 0], [1, 1], [0, 1]])
    assert points is None
    assert "must be closed" in str(error)

    points, error = os_features._parse_polygon([[0, 0], [0, 0], [0, 0], [0, 0]])
    assert points is None
    assert "3 distinct" in str(error)


def test_parse_polygon_rejects_bad_coordinates() -> None:
    from tools import os_features

    points, error = os_features._parse_polygon([[0, 0], [1], [0, 0], [0, 0]])
    assert points is None
    assert "[lon,lat]" in str(error)

    points, error = os_features._parse_polygon([[0, 0], ["a", 1], [1, 1], [0, 0]])
    assert points is None
    assert "numeric" in str(error)

    points, error = os_features._parse_polygon([[0, 0], [200, 1], [1, 1], [0, 0]])
    assert points is None
    assert "out of range" in str(error)


def test_parse_polygon_accepts_valid_ring_and_geojson() -> None:
    from tools import os_features

    ring = [[0, 0], [1, 0], [1, 1], [0, 0]]
    points, error = os_features._parse_polygon(ring)
    assert error is None
    assert points == [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0)]

    geo = {"type": "Polygon", "coordinates": [ring]}
    points2, error2 = os_features._parse_polygon(geo)
    assert error2 is None
    assert points2 == points


def test_bbox_from_polygon() -> None:
    from tools import os_features

    out = os_features._bbox_from_polygon([(2, 4), (-1, 7), (3, 2), (2, 4)])
    assert out == (-1, 2, 3, 7)


def test_point_in_polygon_true_false() -> None:
    from tools import os_features

    poly = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
    assert os_features._point_in_polygon((1, 1), poly)
    assert not os_features._point_in_polygon((3, 3), poly)


def test_feature_intersects_polygon_paths() -> None:
    from tools import os_features

    poly = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
    assert not os_features._feature_intersects_polygon({}, poly)
    assert not os_features._feature_intersects_polygon({"geometry": {}}, poly)

    feature = {
        "geometry": {
            "type": "LineString",
            "coordinates": [[3.0, 3.0], [1.0, 1.0]],
        }
    }
    assert os_features._feature_intersects_polygon(feature, poly)


def test_coerce_number_behaviors() -> None:
    from tools import os_features

    assert os_features._coerce_number(4) == 4.0
    assert os_features._coerce_number(4.2) == 4.2
    assert os_features._coerce_number("5.3") == 5.3
    assert os_features._coerce_number("bad") is None
    assert os_features._coerce_number([1]) is None


def test_match_filter_value_operators() -> None:
    from tools import os_features

    assert os_features._match_filter_value("a", "a")
    assert not os_features._match_filter_value("a", "b")
    assert os_features._match_filter_value(5, {"gt": 4, "lte": 5})
    assert not os_features._match_filter_value("x", {"gt": 1})
    assert os_features._match_filter_value("alpha", {"contains": "LPH"})
    assert os_features._match_filter_value(["a", "b"], {"contains": "a"})
    assert not os_features._match_filter_value(7, {"contains": "7"})
    assert os_features._match_filter_value("x", {"in": ["x", "y"]})
    assert not os_features._match_filter_value("x", {"in": "bad"})
    assert not os_features._match_filter_value("x", {"ne": "x"})


def test_feature_matches_filter_behaviors() -> None:
    from tools import os_features

    feature = {"properties": {"status": "active", "height": 12}}
    assert os_features._feature_matches_filter(feature, {"status": "active"})
    assert not os_features._feature_matches_filter(feature, {"missing": 1})
    assert not os_features._feature_matches_filter({"properties": []}, {"status": "active"})


def test_project_properties_behaviors() -> None:
    from tools import os_features

    assert os_features._project_properties([], [], [], thin_mode=True) == ({}, False)

    props = {f"k{i}": i for i in range(20)}
    projected, trimmed = os_features._project_properties(props, [], [], thin_mode=True)
    assert trimmed
    assert len(projected) == os_features._THIN_PROPERTY_LIMIT

    projected2, trimmed2 = os_features._project_properties(
        {"a": 1, "b": 2, "c": 3},
        ["a", "c"],
        ["c"],
        thin_mode=False,
    )
    assert projected2 == {"a": 1}
    assert not trimmed2


def test_upstream_has_more_branches() -> None:
    from tools import os_features

    assert os_features._upstream_has_more({"numberMatched": 12}, page_size=5, offset=0, limit=5)
    assert not os_features._upstream_has_more(
        {"numberMatched": 5},
        page_size=5,
        offset=0,
        limit=5,
    )
    assert os_features._upstream_has_more({}, page_size=10, offset=0, limit=10)
    assert not os_features._upstream_has_more({}, page_size=0, offset=0, limit=10)


def test_client_get_json_typeerror_fallback(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    calls: list[dict[str, Any]] = []

    def fake_get_json(url: str, params: dict[str, Any] | None = None, **kwargs: Any):
        calls.append({"url": url, "params": params or {}, "kwargs": kwargs})
        if kwargs:
            raise TypeError("legacy signature")
        return 200, {"ok": True}

    monkeypatch.setattr(os_features.client, "get_json", fake_get_json, raising=True)
    status, body = os_features._client_get_json("u", {"a": 1}, timeout=(1, 1), retries=1)
    assert status == 200
    assert body == {"ok": True}
    assert len(calls) == 2


def test_fetch_feature_page_success_path(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    monkeypatch.setattr(
        os_features,
        "_client_get_json",
        lambda *_a, **_k: (200, {"features": []}),
        raising=True,
    )
    status, body, warnings, degraded = os_features._fetch_feature_page(
        url="u",
        params={"bbox": "0,0,1,1", "limit": 10},
        policy={"connectTimeoutSeconds": 1, "readTimeoutSeconds": 1, "retries": 2},
    )
    assert status == 200
    assert body == {"features": []}
    assert warnings == []
    assert not degraded


def test_fetch_feature_page_timeout_degrade_and_retry_paths(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    sequence = [
        (501, {"code": "UPSTREAM_CONNECT_ERROR", "message": "timeout"}),
        (200, {"features": [{"id": "f1"}]}),
    ]
    observed_params: list[dict[str, Any]] = []

    def fake_client_get_json(
        _url: str,
        params: dict[str, Any] | None,
        **_kwargs: Any,
    ) -> tuple[int, dict[str, Any]]:
        observed_params.append(dict(params or {}))
        return sequence.pop(0)

    monkeypatch.setattr(os_features, "_client_get_json", fake_client_get_json, raising=True)
    status, body, warnings, degraded = os_features._fetch_feature_page(
        url="u",
        params={"bbox": "0,0,4,4", "limit": 50},
        policy={
            "connectTimeoutSeconds": 1,
            "readTimeoutSeconds": 1,
            "retries": 2,
            "degradedLimit": 10,
        },
    )
    assert status == 200
    assert body == {"features": [{"id": "f1"}]}
    assert degraded
    assert "TIMEOUT_DEGRADE_APPLIED" in warnings
    assert "TIMEOUT_LIMIT_REDUCED" in warnings
    assert "TIMEOUT_BBOX_REDUCED" in warnings
    assert observed_params[1]["limit"] == 10


def test_features_collections_error_and_success_paths(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    monkeypatch.setattr(
        os_features.client,
        "get_json",
        lambda _url, _params=None: (500, {"isError": True, "code": "OS_API_ERROR"}),
        raising=True,
    )
    status, body = os_features._features_collections({})
    assert status == 501
    assert body["code"] == "OS_API_ERROR"

    def fake_get_json(_url: str, _params: dict[str, Any] | None = None):
        return 200, {
            "collections": [
                {"id": "trn-ntwk-roadlink-4", "title": "Road", "description": "v4"},
                {"id": "trn-ntwk-roadlink-2", "title": "Road", "description": "v2"},
                {"id": "abc", "title": "A", "description": "B"},
                {"id": "", "title": "skip", "description": "skip"},
                "bad",
            ]
        }

    monkeypatch.setattr(os_features.client, "get_json", fake_get_json, raising=True)
    status2, body2 = os_features._features_collections({"q": "road"})
    assert status2 == 200
    assert body2["count"] == 2
    assert body2["collections"][0]["id"] == "trn-ntwk-roadlink-2"
    assert body2["latestByBaseId"]["trn-ntwk-roadlink"] == "trn-ntwk-roadlink-4"


def test_wfs_capabilities_common_branches(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    status, body = os_features._wfs_capabilities_common("/x", {"delivery": "bad"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status2, body2 = os_features._wfs_capabilities_common("/x", {"inlineMaxBytes": 0})
    assert status2 == 400
    assert body2["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        os_features.client,
        "get_bytes",
        lambda _u, _p=None: (500, {"isError": True, "code": "OS_API_ERROR"}),
        raising=True,
    )
    status3, body3 = os_features._wfs_capabilities_common("/x", {})
    assert status3 == 500
    assert body3["code"] == "OS_API_ERROR"

    monkeypatch.setattr(
        os_features.client,
        "get_bytes",
        lambda _u, _p=None: (200, {"contentType": "application/xml", "content": "bad"}),
        raising=True,
    )
    status4, body4 = os_features._wfs_capabilities_common("/x", {})
    assert status4 == 500
    assert body4["code"] == "INTEGRATION_ERROR"

    monkeypatch.setattr(
        os_features.client,
        "get_bytes",
        lambda _u, _p=None: (200, {"contentType": "application/xml", "content": b"<WFS/>"}),
        raising=True,
    )
    monkeypatch.setattr(os_features, "select_delivery_mode", lambda **_k: "resource", raising=True)
    monkeypatch.setattr(
        os_features,
        "write_resource_payload",
        lambda **_k: {
            "resourceUri": "resource://mcp-geo/os-exports/wfs.json",
            "bytes": 7,
            "sha256": "abc",
            "path": "/tmp/wfs.json",
        },
        raising=True,
    )
    status5, body5 = os_features._wfs_capabilities_common(
        "https://api.os.uk/features/v1/wfs/archive",
        {"version": " 2.0.0 "},
    )
    assert status5 == 200
    assert body5["delivery"] == "resource"
    assert body5["resourceUri"].endswith("wfs.json")


def test_features_query_invalid_toggle_inputs() -> None:
    from tools import os_features

    base = {"collection": "buildings", "bbox": [0, 0, 1, 1]}

    status, body = os_features._features_query({**base, "includeGeometry": "yes"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = os_features._features_query({**base, "thinMode": "yes"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = os_features._features_query({**base, "includeQueryables": "yes"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = os_features._features_query({**base, "allowLargeBbox": "yes"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = os_features._features_query({**base, "scanPageBudget": "2"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"


def test_features_query_invalid_controls() -> None:
    from tools import os_features

    base = {"collection": "buildings", "bbox": [0, 0, 1, 1]}

    status, body = os_features._features_query({**base, "delivery": "bad"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = os_features._features_query({**base, "inlineMaxBytes": 0})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = os_features._features_query({**base, "resultType": "bad"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = os_features._features_query({**base, "cql": 123})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = os_features._features_query({**base, "limit": 0})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"


def test_features_query_invalid_bbox_and_polygon_paths() -> None:
    from tools import os_features

    status, body = os_features._features_query({"collection": "buildings", "bbox": [0, 0, 0, 1]})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = os_features._features_query({"collection": "buildings"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = os_features._features_query({"collection": "buildings", "polygon": "bad"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"


def test_features_query_degrade_disables_geometry_and_queryables(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    def fake_fetch_feature_page(**_kwargs: Any):
        return 200, {
            "numberMatched": 1,
            "features": [
                {
                    "id": "f1",
                    "geometry": {"type": "Point", "coordinates": [0.2, 0.2]},
                    "properties": {"name": "A"},
                }
            ],
        }, [], True

    monkeypatch.setattr(os_features, "_fetch_feature_page", fake_fetch_feature_page, raising=True)
    monkeypatch.setattr(
        os_features,
        "_client_get_json",
        lambda *_a, **_k: (500, {"isError": True}),
        raising=True,
    )

    status, body = os_features._features_query(
        {
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "includeGeometry": True,
            "includeQueryables": True,
        }
    )
    assert status == 200
    assert "TIMEOUT_GEOMETRY_DISABLED" in body["hints"]["warnings"]
    assert "QUERYABLES_UNAVAILABLE" in body["hints"]["warnings"]
    assert "geometry" not in body["features"][0]
    assert body["queryables"]["isError"] is True


def test_features_query_hits_local_scan_abort(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_features

    def fake_fetch_feature_page(**_kwargs: Any):
        return 200, {
            "features": [
                {
                    "id": "f1",
                    "geometry": {"type": "Point", "coordinates": [0.2, 0.2]},
                    "properties": {"status": "active"},
                }
            ],
        }, [], False

    monkeypatch.setattr(os_features, "_fetch_feature_page", fake_fetch_feature_page, raising=True)
    monkeypatch.setattr(
        os_features,
        "_client_get_json",
        lambda *_a, **_k: (500, {"isError": True, "code": "OS_API_ERROR"}),
        raising=True,
    )

    status, body = os_features._features_query(
        {
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "resultType": "hits",
            "limit": 1,
            "scanPageBudget": 2,
            "filter": {"status": "active"},
        }
    )
    assert status == 200
    assert body["resultType"] == "hits"
    assert body["count"] == 1
    assert body["hints"]["scan"]["partial"] is True
    assert "LOCAL_SCAN_ABORTED" in body["hints"]["warnings"]
    assert "LOCAL_FILTER_PARTIAL_SCAN" in body["hints"]["warnings"]
    assert "HITS_COUNT_LOWER_BOUND" in body["hints"]["warnings"]
