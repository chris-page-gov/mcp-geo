from __future__ import annotations

from pathlib import Path


def test_os_map_file_and_string_helpers(tmp_path: Path) -> None:
    from tools import os_map

    target = tmp_path / "nested" / "payload.txt"
    os_map._atomic_write_text(target, "payload")
    assert target.read_text(encoding="utf-8") == "payload"
    assert os_map._now_iso().endswith("Z")

    assert os_map._normalize_export_id(123) is None
    assert os_map._normalize_export_id("  ") is None
    assert os_map._normalize_export_id("not-a-uuid") is None
    uuid_text = "12345678-1234-5678-1234-567812345678"
    assert os_map._normalize_export_id(uuid_text) == uuid_text
    assert os_map._stable_json_dumps({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert os_map._slugify_name("A Road / Main Street") == "a-road-main-street"
    assert os_map._slugify_name("!!!") == "road"
    assert os_map._escape_cql_literal("King's Road") == "King''s Road"


def test_os_map_geometry_helpers_cover_invalid_and_valid_shapes() -> None:
    from tools import os_map

    assert os_map._geometry_bbox(None) is None
    assert os_map._geometry_bbox({"coordinates": "bad"}) is None
    assert os_map._geometry_bbox({"coordinates": []}) is None
    assert os_map._geometry_bbox({"coordinates": [[0, 1], [2, 3]]}) == [0.0, 1.0, 2.0, 3.0]

    rect = os_map._rect_polygon_from_bbox([0.0, 1.0, 2.0, 3.0])
    assert rect["coordinates"][0][0] == [0.0, 1.0]
    assert os_map._expand_bbox_by_meters([0.0, 1.0, 2.0, 3.0], 0.0) == [
        0.0,
        1.0,
        2.0,
        3.0,
    ]
    expanded = os_map._expand_bbox_by_meters([0.0, 1.0, 2.0, 3.0], 100.0)
    assert expanded[0] < 0.0
    assert expanded[2] > 2.0

    polygon = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 0]]],
    }
    assert os_map._geometry_contains_point(polygon, (1.0, 0.5))
    assert not os_map._geometry_contains_point(polygon, (3.0, 3.0))


def test_os_map_building_anchor_fallbacks(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_map

    monkeypatch.setattr(os_map, "get_tool", lambda _name: None)
    geometry, warnings, meta = os_map._resolve_building_anchor_polygon(
        uprn="100",
        lon=-0.1,
        lat=51.5,
        search_meters=10,
        buffer_meters=5,
    )
    assert geometry["type"] == "Polygon"
    assert warnings == ["BUILDING_LOOKUP_TOOL_MISSING"]
    assert meta["anchorType"] == "point_buffer"

    class EmptyTool:
        @staticmethod
        def call(_payload):
            return 200, {"features": []}

    monkeypatch.setattr(os_map, "get_tool", lambda _name: EmptyTool())
    geometry, warnings, meta = os_map._resolve_building_anchor_polygon(
        uprn="100",
        lon=-0.1,
        lat=51.5,
        search_meters=10,
        buffer_meters=5,
    )
    assert geometry["type"] == "Polygon"
    assert warnings == ["BUILDING_ANCHOR_FALLBACK_POINT_BUFFER"]
    assert meta["anchorType"] == "point_buffer"


def test_os_map_simplify_and_format_helpers() -> None:
    from tools import os_map

    assert os_map._normalize_export_format(None) == "csv"
    assert os_map._normalize_export_format("json") == "json"
    assert os_map._normalize_export_format("xml") == "csv"
    assert os_map._normalize_road_export_format(None) == "geojson_bundle"
    assert os_map._normalize_road_export_format(123) is None
    assert os_map._normalize_road_export_format("nope") is None
    assert os_map._normalize_road_export_format("leaflet_snippet") == "leaflet_snippet"
    assert os_map._normalize_force_refresh(None) is False
    assert os_map._normalize_force_refresh(True) is True
    assert os_map._normalize_force_refresh("true") is None
    assert os_map._normalize_derivation_mode(None) == "exact"
    assert os_map._normalize_derivation_mode("best_fit") == "best_fit"
    assert os_map._normalize_derivation_mode("other") == "exact"
    assert os_map._parse_simplify_tolerance(None) == 0.0
    assert os_map._parse_simplify_tolerance(True) is None
    assert os_map._parse_simplify_tolerance("bad") is None
    assert os_map._parse_simplify_tolerance(-1) is None
    assert os_map._parse_simplify_tolerance("2.5") == 2.5
    assert os_map._meters_to_degrees(0) == 0.0
    assert os_map._meters_to_degrees(111_320) == 1.0
    assert os_map._point_segment_distance_sq((1, 1), (0, 0), (0, 0)) == 2
    assert os_map._point_segment_distance_sq((1, 1), (0, 0), (2, 0)) == 1

    coords = [[0.0, 0.0], [0.5, 0.001], [1.0, 0.0]]
    assert os_map._simplify_line_coords(coords, 0.0) is coords
    assert os_map._simplify_line_coords([[0.0, 0.0], ["bad", 1], [1.0, 0.0]], 1.0)
    simplified = os_map._simplify_line_coords(coords, 1.0)
    assert simplified == [[0.0, 0.0], [1.0, 0.0]]

    line = {"type": "LineString", "coordinates": coords}
    assert os_map._simplify_geometry(None, 10) is None
    assert os_map._simplify_geometry(line, 0) is line
    assert os_map._simplify_geometry(line, 111_320)["coordinates"] == [
        [0.0, 0.0],
        [1.0, 0.0],
    ]
    multi = {"type": "MultiLineString", "coordinates": [coords]}
    assert os_map._simplify_geometry(multi, 111_320)["coordinates"] == [
        [[0.0, 0.0], [1.0, 0.0]]
    ]
    bad_multi = {"type": "MultiLineString", "coordinates": ["bad"]}
    assert os_map._simplify_geometry(bad_multi, 111_320) is bad_multi
    polygon = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [0, 0]]]}
    assert os_map._simplify_geometry(polygon, 111_320) is polygon
