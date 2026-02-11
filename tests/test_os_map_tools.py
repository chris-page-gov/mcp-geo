from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _install_os_stubs(  # type: ignore[no-untyped-def]
    monkeypatch, mock_os_client
) -> list[tuple[str, dict[str, Any]]]:
    from tools import os_common, os_features, os_places_extra

    fake_client = os_common.client
    monkeypatch.setattr(os_places_extra, "client", fake_client)
    monkeypatch.setattr(os_features, "client", fake_client)

    # Avoid cross-test pollution from in-process caches.
    from tools import os_map

    os_map._NGD_COLLECTION_CACHE["stored_at"] = 0.0
    os_map._NGD_COLLECTION_CACHE["latest_by_base"] = {}

    def places_bbox_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        return 200, {
            "results": [
                {
                    "DPA": {
                        "UPRN": "1000000001",
                        "ADDRESS": "1 Example Street, London SW1A 1AA",
                        "LAT": 51.5001,
                        "LNG": -0.1101,
                        "CLASS": "R",
                    }
                },
                {
                    "DPA": {
                        "UPRN": "1000000002",
                        "ADDRESS": "2 Example Street, London SW1A 1AA",
                        "LAT": 51.5002,
                        "LNG": -0.1102,
                        "CLASS": "R",
                    }
                },
            ]
        }

    ngd_calls: list[tuple[str, dict[str, Any]]] = []

    def ngd_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        ngd_calls.append((url, dict(params or {})))
        if url.endswith("/collections"):
            return 200, {
                "collections": [
                    {"id": "bld-fts-buildingpart-1", "title": "Building Part", "description": ""},
                    {"id": "trn-ntwk-roadlink-5", "title": "RoadLink", "description": ""},
                    {"id": "trn-ntwk-pathlink-2", "title": "PathLink", "description": ""},
                ]
            }

        # /collections/{collection}/items
        parts = url.split("/collections/", 1)
        coll = parts[1].split("/", 1)[0] if len(parts) == 2 else "unknown"
        offset = int(params.get("offset", 0) or 0)
        limit = int(params.get("limit", 100) or 100)

        def _feature(fid: str, geom_type: str) -> dict[str, Any]:
            geom: dict[str, Any]
            if geom_type == "LineString":
                geom = {"type": "LineString", "coordinates": [[-0.1105, 51.5005], [-0.1100, 51.5008]]}
            else:
                geom = {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-0.1105, 51.5005],
                            [-0.1100, 51.5005],
                            [-0.1100, 51.5008],
                            [-0.1105, 51.5008],
                            [-0.1105, 51.5005],
                        ]
                    ],
                }
            return {"id": fid, "geometry": geom, "properties": {"collection": coll, "fid": fid}}

        if coll.startswith("bld-fts-buildingpart"):
            total = 2
            feats = [_feature("b1", "Polygon"), _feature("b2", "Polygon")]
        elif coll.startswith("trn-ntwk-roadlink"):
            total = 5
            feats = [_feature(f"r{i}", "LineString") for i in range(1, total + 1)]
        else:
            total = 1
            feats = [_feature("p1", "LineString")]

        sliced = feats[offset:offset + limit]
        return 200, {"features": sliced, "numberMatched": total}

    mock_os_client["places/v1/bbox"] = places_bbox_handler
    mock_os_client["features/ngd/ofa/v1/collections"] = ngd_handler
    return ngd_calls


def test_os_map_inventory_orchestrates_layers_and_geometry_flags(client, monkeypatch, mock_os_client) -> None:  # type: ignore[no-untyped-def]
    ngd_calls = _install_os_stubs(monkeypatch, mock_os_client)

    bbox = [-0.12, 51.5, -0.11, 51.51]
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_map.inventory",
            "bbox": bbox,
            "layers": ["uprns", "buildings", "road_links", "path_links"],
            "limits": {"uprns": 1, "buildings": 2, "road_links": 2, "path_links": 1},
            "pageTokens": {"road_links": "2"},
            "includeGeometry": {"buildings": False, "road_links": True, "path_links": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["bbox"] == bbox

    uprns = body["layers"]["uprns"]
    assert uprns["count"] == 1
    assert uprns["truncated"] is True

    buildings = body["layers"]["buildings"]
    assert buildings["collection"].startswith("bld-fts-buildingpart")
    assert buildings["count"] == 2
    assert buildings["features"]
    assert "geometry" not in buildings["features"][0]  # includeGeometry false

    road_links = body["layers"]["road_links"]
    assert road_links["collection"].startswith("trn-ntwk-roadlink")
    assert road_links["offset"] == 2  # pageTokens -> offset
    assert road_links["features"]
    assert "geometry" in road_links["features"][0]  # includeGeometry true

    # Ensure we called both collections discovery and items endpoints.
    urls = [u for (u, _params) in ngd_calls]
    assert any(u.endswith("/collections") for u in urls)
    assert any("/items" in u for u in urls)


def test_os_map_export_writes_file_and_is_readable_via_resource_uri(
    client, monkeypatch, mock_os_client, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    _install_os_stubs(monkeypatch, mock_os_client)

    from server.mcp import resource_catalog
    from tools import os_map

    exports_dir = tmp_path / "exports"
    monkeypatch.setattr(os_map, "_EXPORTS_DIR", exports_dir)
    monkeypatch.setattr(resource_catalog, "EXPORTS_DIR", exports_dir)

    bbox = [-0.12, 51.5, -0.11, 51.51]
    resp = client.post(
        "/tools/call",
        json={"tool": "os_map.export", "bbox": bbox, "name": "test-export"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["uri"].startswith("resource://mcp-geo/exports/")

    export_path = Path(body["path"])
    assert export_path.exists()

    read = client.get("/resources/read", params={"uri": body["uri"]})
    assert read.status_code == 200
    contents = read.json()["contents"]
    payload = json.loads(contents[0]["text"])
    assert payload["exportId"] == body["exportId"]
    assert payload["name"] == "test-export"
    assert payload["inventory"]["bbox"] == bbox

    traversal = client.get("/resources/read", params={"uri": "resource://mcp-geo/exports/../nope.json"})
    assert traversal.status_code == 200
    traversal_payload = json.loads(traversal.json()["contents"][0]["text"])
    assert traversal_payload.get("code") == "INVALID_INPUT"


def test_os_map_parsers_cover_edge_cases() -> None:
    from tools import os_map

    assert os_map._parse_bbox("nope") is None
    assert os_map._parse_bbox([1, 2, 3]) is None
    assert os_map._parse_bbox([1, 2, "x", 4]) is None
    assert os_map._parse_bbox([0, 0, 0, 1]) is None  # minLon >= maxLon
    assert os_map._parse_bbox([0, 1, 2, 0]) is None  # minLat >= maxLat

    assert os_map._parse_layers("uprns, buildings, nope") == ["uprns", "buildings"]
    assert os_map._parse_layers(123) is None

    limits = os_map._parse_limits({"uprns": "x", "buildings": 0, "road_links": 999999, "nope": 1})
    assert limits["uprns"] == os_map._DEFAULT_LIMITS["uprns"]
    assert limits["buildings"] == os_map._DEFAULT_LIMITS["buildings"]
    assert limits["road_links"] == os_map._MAX_LIMIT

    tokens = os_map._parse_layer_tokens({"buildings": " 10 ", "road_links": 2.7, "nope": "x"})
    assert tokens == {"buildings": "10", "road_links": "2"}

    bools = os_map._parse_bool_map({"buildings": "nope", "road_links": True, "nope": True})
    assert bools == {"road_links": True}

    cols = os_map._parse_collections_override({"buildings": " bld-123 ", "nope": "x"})
    assert cols == {"buildings": "bld-123"}


def test_os_map_latest_ngd_collection_ids_error_branches(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_map

    os_map._NGD_COLLECTION_CACHE["stored_at"] = 0.0
    os_map._NGD_COLLECTION_CACHE["latest_by_base"] = {}

    orig_get_tool = os_map.get_tool

    def patched_none(name: str):  # type: ignore[no-untyped-def]
        if name == "os_features.collections":
            return None
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", patched_none)
    assert os_map._get_latest_ngd_collection_ids() == {}

    class DummyTool:
        def __init__(self, result: tuple[int, Any]):
            self._result = result

        def call(self, args: dict[str, Any]):  # noqa: ARG002
            return self._result

    def patched_bad_status(name: str):  # type: ignore[no-untyped-def]
        if name == "os_features.collections":
            return DummyTool((500, {"isError": True}))
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", patched_bad_status)
    assert os_map._get_latest_ngd_collection_ids() == {}

    def patched_bad_data(name: str):  # type: ignore[no-untyped-def]
        if name == "os_features.collections":
            return DummyTool((200, "nope"))
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", patched_bad_data)
    assert os_map._get_latest_ngd_collection_ids() == {}

    def patched_bad_latest(name: str):  # type: ignore[no-untyped-def]
        if name == "os_features.collections":
            return DummyTool((200, {"latestByBaseId": "nope"}))
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", patched_bad_latest)
    assert os_map._get_latest_ngd_collection_ids() == {}


def test_os_map_resolve_collection_id_override_and_unknown() -> None:
    from tools import os_map

    assert os_map._resolve_collection_id("buildings", {"buildings": "custom"}) == "custom"
    assert os_map._resolve_collection_id("nope", {}) is None


def test_os_maps_render_overlay_contract_without_inventory(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_maps.render",
            "bbox": [-0.12, 51.5, -0.11, 51.51],
            "size": 512,
            "overlays": {
                "points": [
                    {"lat": 51.5005, "lon": -0.1105, "properties": {"label": "A"}},
                    {"coordinates": [-0.1102, 51.5006], "properties": {"label": "B"}},
                ],
                "polygons": [
                    {
                        "type": "Feature",
                        "properties": {"name": "poly"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [-0.1108, 51.5003],
                                    [-0.1100, 51.5003],
                                    [-0.1100, 51.5009],
                                    [-0.1108, 51.5009],
                                    [-0.1108, 51.5003],
                                ]
                            ],
                        },
                    }
                ],
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["render"]["imageWidth"] == 512
    assert body["render"]["imageHeight"] == 512
    layers = {row["id"]: row for row in body["overlayLayers"]}
    assert layers["input_points"]["kind"] == "point"
    assert layers["input_points"]["count"] == 2
    assert layers["input_polygons"]["kind"] == "polygon"
    collections = {row["id"]: row for row in body["overlayCollections"]}
    assert collections["input_points"]["featureCollection"]["type"] == "FeatureCollection"
    assert len(collections["input_points"]["featureCollection"]["features"]) == 2
    assert "inventory" in body and body["inventory"] is None


def test_os_maps_render_inventory_alignment(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_maps

    class DummyTool:
        def call(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            assert args["tool"] == "os_map.inventory"
            assert args["bbox"] == [-0.12, 51.5, -0.11, 51.51]
            return 200, {
                "bbox": args["bbox"],
                "layers": {
                    "uprns": {
                        "results": [
                            {"uprn": "1001", "lat": 51.5001, "lon": -0.1101},
                            {"uprn": "1002", "lat": 51.5002, "lon": -0.1102},
                        ]
                    },
                    "buildings": {
                        "collection": "bld-fts-buildingpart-1",
                        "features": [
                            {
                                "type": "Feature",
                                "id": "b1",
                                "geometry": {"type": "Polygon", "coordinates": []},
                                "properties": {"name": "b1"},
                            }
                        ],
                    },
                    "road_links": {
                        "collection": "trn-ntwk-roadlink-1",
                        "features": [
                            {
                                "type": "Feature",
                                "id": "r1",
                                "geometry": {"type": "LineString", "coordinates": []},
                                "properties": {"name": "r1"},
                            }
                        ],
                        "nextPageToken": "1",
                    },
                },
            }

    monkeypatch.setattr(os_maps, "get_tool", lambda name: DummyTool() if name == "os_map.inventory" else None)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_maps.render",
            "bbox": [-0.12, 51.5, -0.11, 51.51],
            "includeInventory": True,
            "inventory": {"layers": ["uprns", "buildings", "road_links"]},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["inventory"]["layers"]["uprns"]["results"][0]["uprn"] == "1001"
    layers = {row["id"]: row for row in body["overlayLayers"]}
    assert layers["inventory_uprns"]["kind"] == "point"
    assert layers["inventory_uprns"]["count"] == 2
    assert layers["inventory_buildings"]["collection"] == "bld-fts-buildingpart-1"
    assert layers["inventory_road_links"]["nextPageToken"] == "1"


def test_os_map_inventory_error_branches(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_map

    bbox = [-0.12, 51.5, -0.11, 51.51]
    bad_bbox = [-0.12, 51.5, -0.12, 51.51]  # minLon == maxLon

    status, payload = os_map._inventory({"bbox": bad_bbox})
    assert status == 400
    assert payload.get("code") == "INVALID_INPUT"

    # Missing os_places.within tool.
    orig_get_tool = os_map.get_tool

    def missing_places(name: str):  # type: ignore[no-untyped-def]
        if name == "os_places.within":
            return None
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", missing_places)
    status, payload = os_map._inventory({"bbox": bbox, "layers": ["uprns"]})
    assert status == 200
    assert payload["layers"]["uprns"]["code"] == "MISSING_TOOL"

    class DummyTool:
        def __init__(self, result: tuple[int, Any]):
            self._result = result

        def call(self, args: dict[str, Any]):  # noqa: ARG002
            return self._result

    # Upstream failure from os_places.within should be passed through as the layer payload.
    def failing_places(name: str):  # type: ignore[no-untyped-def]
        if name == "os_places.within":
            return DummyTool((500, {"isError": True, "code": "OS_API_ERROR", "message": "fail"}))
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", failing_places)
    status, payload = os_map._inventory({"bbox": bbox, "layers": ["uprns"]})
    assert status == 200
    assert payload["layers"]["uprns"]["code"] == "OS_API_ERROR"

    # Non-list results from a successful places call should normalize to [].
    def weird_places(name: str):  # type: ignore[no-untyped-def]
        if name == "os_places.within":
            return DummyTool((200, {"results": "nope"}))
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", weird_places)
    status, payload = os_map._inventory({"bbox": bbox, "layers": ["uprns"]})
    assert status == 200
    assert payload["layers"]["uprns"]["count"] == 0
    assert payload["layers"]["uprns"]["results"] == []

    # Missing os_features.query tool.
    def missing_features(name: str):  # type: ignore[no-untyped-def]
        if name == "os_features.query":
            return None
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", missing_features)
    status, payload = os_map._inventory({"bbox": bbox, "layers": ["buildings"]})
    assert status == 200
    assert payload["layers"]["buildings"]["code"] == "MISSING_TOOL"

    # No collection mapping (simulated by removing default mapping).
    def has_features_tool(name: str):  # type: ignore[no-untyped-def]
        if name == "os_features.query":
            return DummyTool((200, {}))
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", has_features_tool)
    monkeypatch.setattr(os_map, "_DEFAULT_COLLECTION_BASES", {})
    status, payload = os_map._inventory({"bbox": bbox, "layers": ["buildings"]})
    assert status == 200
    assert payload["layers"]["buildings"]["code"] == "INVALID_INPUT"

    # Integration error: os_features.query returned non-object on success.
    monkeypatch.setattr(os_map, "_DEFAULT_COLLECTION_BASES", {"buildings": "bld-fts-buildingpart"})
    monkeypatch.setattr(os_map, "_get_latest_ngd_collection_ids", lambda: {})

    def bad_features_response(name: str):  # type: ignore[no-untyped-def]
        if name == "os_features.query":
            return DummyTool((200, "nope"))
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", bad_features_response)
    status, payload = os_map._inventory({"bbox": bbox, "layers": ["buildings"]})
    assert status == 200
    assert payload["layers"]["buildings"]["code"] == "INTEGRATION_ERROR"


def test_os_map_export_error_branches(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_map

    bbox = [-0.12, 51.5, -0.11, 51.51]
    bad_bbox = [-0.12, 51.5, -0.12, 51.51]  # minLon == maxLon

    status, payload = os_map._export({"bbox": bad_bbox})
    assert status == 400
    assert payload.get("code") == "INVALID_INPUT"

    status, payload = os_map._export({"bbox": bbox, "name": 123})
    assert status == 400
    assert payload.get("code") == "INVALID_INPUT"

    status, payload = os_map._export({"bbox": bbox, "recipe": "nope"})
    assert status == 400
    assert payload.get("code") == "INVALID_INPUT"

    monkeypatch.setattr(os_map, "_inventory", lambda _payload: (400, {"isError": True, "code": "INVALID_INPUT"}))
    status, payload = os_map._export({"bbox": bbox})
    assert status == 400
    assert payload.get("code") == "INVALID_INPUT"


def test_resources_read_export_not_found(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/exports/does-not-exist.json"})
    assert resp.status_code == 200
    payload = json.loads(resp.json()["contents"][0]["text"])
    assert payload.get("code") == "NOT_FOUND"
