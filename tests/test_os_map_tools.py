from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any


def test_os_map_feature_intersects_polygon_detects_crossing_segments() -> None:
    from tools import os_map

    poly = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
    feature = {
        "geometry": {
            "type": "LineString",
            "coordinates": [[-1.0, 1.0], [3.0, 1.0]],
        }
    }
    assert os_map._feature_intersects_polygon(feature, poly)


def _install_os_stubs(  # type: ignore[no-untyped-def]
    monkeypatch,
    mock_os_client,
    *,
    places_bbox_handler=None,
) -> list[tuple[str, dict[str, Any]]]:
    from tools import os_common, os_features, os_places_extra

    fake_client = os_common.client
    monkeypatch.setattr(os_places_extra, "client", fake_client)
    monkeypatch.setattr(os_features, "client", fake_client)

    # Avoid cross-test pollution from in-process caches.
    from tools import os_map

    os_map._NGD_COLLECTION_CACHE["stored_at"] = 0.0
    os_map._NGD_COLLECTION_CACHE["latest_by_base"] = {}

    def default_places_bbox_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
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

    mock_os_client["places/v1/bbox"] = places_bbox_handler or default_places_bbox_handler
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


def test_os_map_inventory_preserves_harold_wood_places_bbox_axis_order(
    client, monkeypatch, mock_os_client
) -> None:  # type: ignore[no-untyped-def]
    places_calls: list[dict[str, Any]] = []

    def places_bbox_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        places_calls.append(dict(params))
        lat_min, lon_min, lat_max, lon_max = [float(value) for value in params["bbox"].split(",")]
        assert lat_min < lat_max
        assert lon_min < lon_max
        return 200, {
            "results": [
                {
                    "DPA": {
                        "UPRN": "10024386371",
                        "ADDRESS": "HAROLD WOOD POLYCLINIC, COPSE AVENUE, HAROLD WOOD, RM3 0FE",
                        "LAT": 51.5931845,
                        "LNG": 0.2257232,
                        "CLASS": "CM02",
                    }
                }
            ]
        }

    _install_os_stubs(
        monkeypatch,
        mock_os_client,
        places_bbox_handler=places_bbox_handler,
    )

    harold_wood_bbox = [
        0.212767901572177,
        51.5770138134869,
        0.270927815822217,
        51.6091919953636,
    ]
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_map.inventory",
            "bbox": harold_wood_bbox,
            "layers": ["uprns"],
            "limits": {"uprns": 10},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    uprns = body["layers"]["uprns"]
    assert uprns["count"] == 1
    assert uprns["truncated"] is False
    assert uprns["results"][0]["uprn"] == "10024386371"
    assert uprns["provenance"]["bboxMode"] == "tiled"
    assert uprns["provenance"]["tileCount"] == len(places_calls)
    assert len(places_calls) > 1


def test_os_map_inventory_keeps_harold_wood_places_clamp_below_strict_vendor_limit(
    client, monkeypatch, mock_os_client
) -> None:  # type: ignore[no-untyped-def]
    from tools import os_places_extra

    places_calls: list[dict[str, Any]] = []

    def places_bbox_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        places_calls.append(dict(params))
        lat_min, lon_min, lat_max, lon_max = [float(value) for value in params["bbox"].split(",")]
        area = os_places_extra._bbox_area_m2(lon_min, lat_min, lon_max, lat_max)
        assert area < os_places_extra.MAX_BBOX_AREA_M2
        return 200, {
            "results": [
                {
                    "DPA": {
                        "UPRN": "10024386371",
                        "ADDRESS": "HAROLD WOOD POLYCLINIC, COPSE AVENUE, HAROLD WOOD, RM3 0FE",
                        "LAT": 51.5931845,
                        "LNG": 0.2257232,
                        "CLASS": "CM02",
                    }
                }
            ]
        }

    _install_os_stubs(
        monkeypatch,
        mock_os_client,
        places_bbox_handler=places_bbox_handler,
    )

    harold_wood_bbox = [0.212839, 51.572372, 0.287124, 51.609192]
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_map.inventory",
            "bbox": harold_wood_bbox,
            "layers": ["uprns"],
            "limits": {"uprns": 20},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    uprns = body["layers"]["uprns"]
    assert uprns["count"] == 1
    assert uprns["results"][0]["uprn"] == "10024386371"
    assert uprns["provenance"]["bboxMode"] == "clamped"
    assert uprns["provenance"]["tileCount"] == 1
    assert uprns["provenance"]["originalTileCount"] > 25
    assert len(places_calls) == 1


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
    assert body["resourceUri"] == body["uri"]
    assert "path" not in body

    export_path = exports_dir / f"{body['exportId']}.json"
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


def test_os_map_export_roads_writes_semantic_parts_and_manifest(client, monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_catalog
    from tools import os_map

    os_exports_dir = tmp_path / "os_exports"
    monkeypatch.setattr(os_map, "_OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORT_JOBS_DIR", os_exports_dir / "jobs")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports_dir)

    class DummyTool:
        def call(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            cql = args.get("cql")
            page_token = str(args.get("pageToken") or "")
            if cql == "roadclassificationnumber = 'A444'" and not page_token:
                return 200, {
                    "features": [
                        {
                            "id": "a444-1",
                            "properties": {"roadclassificationnumber": "A444"},
                            "geometry": {"type": "LineString", "coordinates": [[-1.5, 52.4], [-1.49, 52.41]]},
                        },
                        {
                            "id": "a444-2",
                            "properties": {"roadclassificationnumber": "A444"},
                            "geometry": {"type": "LineString", "coordinates": [[-1.49, 52.41], [-1.48, 52.42]]},
                        },
                    ],
                    "offset": 0,
                    "nextPageToken": "2",
                    "hints": {"warnings": []},
                }
            if cql == "roadclassificationnumber = 'A444'" and page_token == "2":
                return 200, {
                    "features": [
                        {
                            "id": "a444-3",
                            "properties": {"roadclassificationnumber": "A444"},
                            "geometry": {"type": "LineString", "coordinates": [[-1.48, 52.42], [-1.47, 52.43]]},
                        }
                    ],
                    "offset": 2,
                    "nextPageToken": None,
                    "hints": {"warnings": []},
                }
            if cql == "roadclassificationnumber = 'A5'":
                return 200, {
                    "features": [
                        {
                            "id": "a5-1",
                            "properties": {"roadclassificationnumber": "A5"},
                            "geometry": {"type": "LineString", "coordinates": [[-1.6, 52.45], [-1.59, 52.46]]},
                        }
                    ],
                    "offset": 0,
                    "nextPageToken": None,
                    "hints": {"warnings": []},
                }
            raise AssertionError(f"Unexpected args: {args}")

    monkeypatch.setattr(
        os_map,
        "get_tool",
        lambda name: DummyTool() if name == "os_features.query" else None,
    )

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export_roads",
            "collection": "trn-ntwk-roadlink-5",
            "bbox": [-1.65, 52.35, -1.4, 52.58],
            "roads": [
                {"label": "A444", "roadClassificationNumber": "A444"},
                {"label": "A5", "roadClassificationNumber": "A5"},
            ],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["format"] == "geojson_bundle"
    assert body["featureCounts"] == {"A444": 3, "A5": 1}
    assert body["complete"] is True
    assert body["sourcePagesFetched"] == 3
    assert body["cached"] is False

    manifest_read = client.get("/resources/read", params={"uri": body["resourceUri"]})
    assert manifest_read.status_code == 200
    manifest_contents = manifest_read.json()["contents"][0]
    manifest = json.loads(manifest_contents["text"])
    assert manifest["featureCounts"]["A444"] == 3
    assert any(part["name"] == "a444.geojson" for part in manifest["parts"])

    a444_part = next(part for part in body["parts"] if part["name"] == "a444.geojson")
    part_read = client.get("/resources/read", params={"uri": a444_part["uri"]})
    assert part_read.status_code == 200
    part_contents = part_read.json()["contents"][0]
    assert part_contents["mimeType"] == "application/geo+json"
    feature_collection = json.loads(part_contents["text"])
    assert feature_collection["type"] == "FeatureCollection"
    assert len(feature_collection["features"]) == 3


def test_os_map_export_roads_uses_cached_manifest_for_repeat_requests(client, monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_catalog
    from tools import os_map

    os_exports_dir = tmp_path / "os_exports"
    monkeypatch.setattr(os_map, "_OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORT_JOBS_DIR", os_exports_dir / "jobs")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports_dir)

    call_count = {"value": 0}

    class DummyTool:
        def call(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            call_count["value"] += 1
            assert args["cql"] == "roadclassificationnumber = 'B4101'"
            return 200, {
                "features": [
                    {
                        "id": "b4101-1",
                        "properties": {"roadclassificationnumber": "B4101"},
                        "geometry": {"type": "LineString", "coordinates": [[-1.8, 52.4], [-1.79, 52.41]]},
                    }
                ],
                "offset": 0,
                "nextPageToken": None,
                "hints": {"warnings": []},
            }

    monkeypatch.setattr(
        os_map,
        "get_tool",
        lambda name: DummyTool() if name == "os_features.query" else None,
    )

    request = {
        "tool": "os_map.export_roads",
        "collection": "trn-ntwk-roadlink-5",
        "bbox": [-1.87, 52.34, -1.6, 52.56],
        "outputFormat": "javascript_overlay",
        "roads": [{"label": "B4101", "roadClassificationNumber": "B4101"}],
    }
    first = client.post("/tools/call", json=request)
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["cached"] is False
    assert call_count["value"] == 1

    monkeypatch.setattr(os_map, "get_tool", lambda _name: None)

    second = client.post("/tools/call", json=request)
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["cached"] is True
    assert second_body["resourceUri"] == first_body["resourceUri"]
    assert second_body["primaryUri"] == first_body["primaryUri"]

    primary_read = client.get("/resources/read", params={"uri": second_body["primaryUri"]})
    assert primary_read.status_code == 200
    primary_contents = primary_read.json()["contents"][0]
    assert primary_contents["mimeType"] == "application/javascript"
    assert "roadOverlayData" in primary_contents["text"]


def test_os_map_export_roads_resolves_gss_code_aoi_without_bbox(
    client, monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_catalog
    from tools import os_map

    os_exports_dir = tmp_path / "os_exports"
    monkeypatch.setattr(os_map, "_OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORT_JOBS_DIR", os_exports_dir / "jobs")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(
        os_map,
        "_resolve_selection_rows",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("gss_code-only AOI should not resolve address selectors")
        ),
    )

    road_requests: list[dict[str, Any]] = []

    class AreaTool:
        def call(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            assert args == {
                "tool": "admin_lookup.area_geometry",
                "id": "E05000644",
                "includeGeometry": True,
            }
            return 200, {
                "id": "E05000644",
                "bbox": [-1.55, 52.38, -1.45, 52.48],
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-1.55, 52.38],
                            [-1.45, 52.38],
                            [-1.45, 52.48],
                            [-1.55, 52.48],
                            [-1.55, 52.38],
                        ]
                    ],
                },
            }

    class RoadTool:
        def call(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            road_requests.append(dict(args))
            assert "bbox" not in args
            assert "polygon" in args
            return 200, {
                "features": [
                    {
                        "id": "road-1",
                        "properties": {"roadclassificationnumber": "A444"},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[-1.51, 52.40], [-1.50, 52.41]],
                        },
                    }
                ],
                "offset": 0,
                "nextPageToken": None,
                "hints": {"warnings": []},
            }

    def _get_tool(name: str):  # type: ignore[no-untyped-def]
        if name == "admin_lookup.area_geometry":
            return AreaTool()
        if name == "os_features.query":
            return RoadTool()
        return None

    monkeypatch.setattr(os_map, "get_tool", _get_tool)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export_roads",
            "collection": "trn-ntwk-roadlink-5",
            "selectionSpec": {
                "selectors": [{"type": "gss_code", "level": "WARD", "code": "E05000644"}],
                "uprnOverrides": {"include": [], "exclude": []},
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["featureCounts"] == {"selection": 1}
    assert body["aoi"]["queryPolygonCount"] == 1
    assert any(part["name"] == "aoi-limits.geojson" for part in body["parts"])
    assert len(road_requests) == 1


def test_os_map_export_roads_allows_explicit_road_bboxes_when_selection_unresolved(
    client, monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_catalog
    from tools import os_map

    os_exports_dir = tmp_path / "os_exports"
    monkeypatch.setattr(os_map, "_OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORT_JOBS_DIR", os_exports_dir / "jobs")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(
        os_map,
        "_resolve_export_road_aoi",
        lambda **_kwargs: (None, ["selector returned no geometry"]),
    )

    road_requests: list[dict[str, Any]] = []

    class RoadTool:
        def call(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            road_requests.append(dict(args))
            assert args["bbox"] == [-1.55, 52.38, -1.45, 52.48]
            return 200, {
                "features": [
                    {
                        "id": "road-1",
                        "properties": {"roadclassificationnumber": "A444"},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[-1.51, 52.40], [-1.50, 52.41]],
                        },
                    }
                ],
                "offset": 0,
                "nextPageToken": None,
                "hints": {"warnings": []},
            }

    monkeypatch.setattr(
        os_map,
        "get_tool",
        lambda name: RoadTool() if name == "os_features.query" else None,
    )

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export_roads",
            "selectionSpec": {"postcode": "ZZ1 1ZZ"},
            "roads": [
                {
                    "label": "A444",
                    "bbox": [-1.55, 52.38, -1.45, 52.48],
                    "roadClassificationNumber": "A444",
                }
            ],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["featureCounts"] == {"A444": 1}
    assert road_requests


def test_os_map_export_roads_resolves_uprn_anchor_to_building_polygon(
    client, monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    from server.config import settings
    from server.mcp import resource_catalog
    from tools import os_map

    cache_dir = tmp_path / "ons_geo_cache"
    db_name = "ons_geo_cache.sqlite"
    _seed_ons_geo_uprn_index(cache_dir, db_name)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DIR", str(cache_dir), raising=False)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DB", db_name, raising=False)

    os_exports_dir = tmp_path / "os_exports"
    monkeypatch.setattr(os_map, "_OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORT_JOBS_DIR", os_exports_dir / "jobs")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports_dir)

    building_requests: list[dict[str, Any]] = []
    road_requests: list[dict[str, Any]] = []

    class UprnTool:
        def call(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            assert args == {"tool": "os_places.by_uprn", "uprn": "100023336959"}
            return 200, {"result": {"uprn": "100023336959", "lat": 51.5006, "lon": -0.1102}}

    class FeaturesTool:
        def call(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            collection = args.get("collection")
            if collection == "buildings":
                building_requests.append(dict(args))
                assert "bbox" in args
                return 200, {
                    "features": [
                        {
                            "id": "building-1",
                            "properties": {"name": "Anchor building"},
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [-0.11035, 51.50045],
                                        [-0.11005, 51.50045],
                                        [-0.11005, 51.50075],
                                        [-0.11035, 51.50075],
                                        [-0.11035, 51.50045],
                                    ]
                                ],
                            },
                        }
                    ]
                }
            road_requests.append(dict(args))
            assert collection == "trn-ntwk-roadlink-5"
            assert "polygon" in args
            assert "bbox" not in args
            return 200, {
                "features": [
                    {
                        "id": "road-1",
                        "properties": {"roadclassificationnumber": "A444"},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[-0.1103, 51.5005], [-0.1098, 51.5009]],
                        },
                    }
                ],
                "offset": 0,
                "nextPageToken": None,
                "hints": {"warnings": []},
            }

    def _get_tool(name: str):  # type: ignore[no-untyped-def]
        if name == "os_places.by_uprn":
            return UprnTool()
        if name == "os_features.query":
            return FeaturesTool()
        return None

    monkeypatch.setattr(os_map, "get_tool", _get_tool)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export_roads",
            "collection": "trn-ntwk-roadlink-5",
            "selectionSpec": {
                "selectors": [{"type": "uprn", "uprn": "100023336959"}],
                "uprnOverrides": {"include": [], "exclude": []},
            },
            "anchorBufferMeters": 15,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["featureCounts"] == {"selection": 1}
    assert body["aoi"]["anchorPolygonCount"] == 1
    assert body["aoi"]["addressStats"]["resolvedUprnCount"] == 1
    assert any(part["name"] == "aoi-anchors.geojson" for part in body["parts"])
    assert len(building_requests) == 1
    assert len(road_requests) == 1


def test_os_map_export_roads_accepts_postcode_selection_shorthand(
    client, monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    from server.config import settings
    from server.mcp import resource_catalog
    from tools import os_map

    cache_dir = tmp_path / "ons_geo_cache"
    db_name = "ons_geo_cache.sqlite"
    _seed_ons_geo_uprn_index(cache_dir, db_name)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DIR", str(cache_dir), raising=False)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DB", db_name, raising=False)

    os_exports_dir = tmp_path / "os_exports"
    monkeypatch.setattr(os_map, "_OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORT_JOBS_DIR", os_exports_dir / "jobs")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports_dir)

    class UprnTool:
        def call(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            assert args == {"tool": "os_places.by_uprn", "uprn": "100023336959"}
            return 200, {"result": {"uprn": "100023336959", "lat": 51.5006, "lon": -0.1102}}

    class FeaturesTool:
        def call(self, args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
            if args.get("collection") == "buildings":
                return 200, {
                    "features": [
                        {
                            "id": "building-1",
                            "properties": {"name": "Anchor building"},
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [-0.11035, 51.50045],
                                        [-0.11005, 51.50045],
                                        [-0.11005, 51.50075],
                                        [-0.11035, 51.50075],
                                        [-0.11035, 51.50045],
                                    ]
                                ],
                            },
                        }
                    ]
                }
            return 200, {
                "features": [
                    {
                        "id": "road-1",
                        "properties": {"roadclassificationnumber": "COVENTRY"},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[-0.1103, 51.5005], [-0.1098, 51.5009]],
                        },
                    }
                ],
                "offset": 0,
                "nextPageToken": None,
                "hints": {"warnings": []},
            }

    def _get_tool(name: str):  # type: ignore[no-untyped-def]
        if name == "os_places.by_uprn":
            return UprnTool()
        if name == "os_features.query":
            return FeaturesTool()
        return None

    monkeypatch.setattr(os_map, "get_tool", _get_tool)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export_roads",
            "collection": "trn-ntwk-roadlink-5",
            "selectionSpec": {"postcode": "CV1 2GT"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["featureCounts"] == {"selection": 1}
    assert body["aoi"]["addressStats"]["resolvedUprnCount"] == 1


def test_os_map_export_roads_selection_cache_failure_is_normalized(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export_roads",
            "selectionSpec": {"postcode": "CV3 1HB"},
            "outputFormat": "geojson_bundle",
        },
    )
    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] in {"CACHE_UNAVAILABLE", "CACHE_READ_ERROR"}


def test_os_map_export_roads_unresolved_selection_returns_explicit_error(
    client, monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    from server.config import settings
    from tools import os_map

    cache_dir = tmp_path / "ons_geo_cache"
    db_name = "ons_geo_cache.sqlite"
    _seed_ons_geo_uprn_index(cache_dir, db_name)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DIR", str(cache_dir), raising=False)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DB", db_name, raising=False)
    monkeypatch.setattr(os_map, "get_tool", lambda _name: None)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export_roads",
            "selectionSpec": {"postcode": "ZZ1 1ZZ"},
        },
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "AOI_NOT_RESOLVED"


def _seed_ons_geo_uprn_index(cache_dir: Path, db_name: str) -> Path:
    from server.ons_geo_cache import ensure_schema

    cache_dir.mkdir(parents=True, exist_ok=True)
    db_path = cache_dir / db_name
    conn = sqlite3.connect(str(db_path))
    ensure_schema(conn)
    conn.execute(
        """
        INSERT INTO ons_geo_products (
            product_id, key_type, derivation_mode, release, source_name,
            source_path, source_sha256, record_count, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ONSUD",
            "uprn",
            "exact",
            "2026-02",
            "ONSUD",
            "onsud.csv",
            "hash",
            2,
            "2026-02-22T00:00:00Z",
        ),
    )
    conn.execute(
        """
        INSERT INTO ons_geo_uprn_index (
            product_id, derivation_mode, uprn, postcode, oa_code, lsoa_code, msoa_code,
            lad_code, lad_name, postal_delivery, geographies_json, cached_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ONSUD",
            "exact",
            "100023336959",
            "CV12GT",
            "E0001",
            "E0101",
            "E0201",
            "E08000026",
            "Coventry",
            1,
            "{}",
            "2026-02-22T00:00:00Z",
        ),
    )
    conn.execute(
        """
        INSERT INTO ons_geo_uprn_index (
            product_id, derivation_mode, uprn, postcode, oa_code, lsoa_code, msoa_code,
            lad_code, lad_name, postal_delivery, geographies_json, cached_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "ONSUD",
            "exact",
            "100120786206",
            "M601NW",
            "E0002",
            "E0102",
            "E0202",
            "E08000026",
            "Coventry",
            0,
            "{}",
            "2026-02-22T00:00:00Z",
        ),
    )
    conn.commit()
    conn.close()
    return db_path


def test_os_map_selection_export_async_csv_and_status_polling(client, monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from server.config import settings
    from server.mcp import resource_catalog
    from tools import os_map

    cache_dir = tmp_path / "ons_geo_cache"
    db_name = "ons_geo_cache.sqlite"
    _seed_ons_geo_uprn_index(cache_dir, db_name)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DIR", str(cache_dir), raising=False)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DB", db_name, raising=False)

    os_exports_dir = tmp_path / "os_exports"
    monkeypatch.setattr(os_map, "_OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORT_JOBS_DIR", os_exports_dir / "jobs")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports_dir)

    queued = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export",
            "exportType": "selection_uprn",
            "selectionSpec": {
                "selectors": [
                    {"type": "gss_code", "level": "LAD", "code": "E08000026"},
                ],
                "uprnOverrides": {"include": [], "exclude": []},
            },
            "format": "csv",
            "filters": {"postalDeliveryOnly": True},
            "delivery": "resource",
        },
    )
    assert queued.status_code == 200
    queued_body = queued.json()
    assert queued_body["status"] == "queued"
    export_id = queued_body["exportId"]

    terminal = None
    for _ in range(80):
        status_resp = client.post("/tools/call", json={"tool": "os_map.get_export", "exportId": export_id})
        assert status_resp.status_code == 200
        status_body = status_resp.json()
        if status_body["status"] in {"completed", "failed"}:
            terminal = status_body
            break
        time.sleep(0.05)
    assert terminal is not None
    assert terminal["status"] == "completed", terminal
    assert terminal.get("resultUri", "").startswith("resource://mcp-geo/os-exports/")
    assert terminal.get("rowCount") == 1
    assert any("postalDeliveryOnly applied" in w for w in terminal.get("warnings", []))

    read = client.get("/resources/read", params={"uri": terminal["resultUri"]})
    assert read.status_code == 200
    contents = read.json()["contents"][0]
    assert contents["mimeType"] == "text/csv"
    csv_text = contents["text"]
    assert "uprn,postcode,oa_code,local_authority_name" in csv_text
    assert "100023336959,CV12GT,E0001,Coventry" in csv_text


def test_os_map_selection_export_without_membership_columns(client, monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from server.config import settings
    from server.mcp import resource_catalog
    from tools import os_map

    cache_dir = tmp_path / "ons_geo_cache"
    db_name = "ons_geo_cache.sqlite"
    _seed_ons_geo_uprn_index(cache_dir, db_name)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DIR", str(cache_dir), raising=False)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DB", db_name, raising=False)

    os_exports_dir = tmp_path / "os_exports"
    monkeypatch.setattr(os_map, "_OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORT_JOBS_DIR", os_exports_dir / "jobs")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports_dir)

    queued = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export",
            "exportType": "selection_uprn",
            "selectionSpec": {
                "selectors": [{"type": "gss_code", "level": "LAD", "code": "E08000026"}],
                "uprnOverrides": {"include": [], "exclude": []},
            },
            "format": "csv",
            "columns": {"defaultSet": "maplab_default_v1", "selectorMembership": False},
            "delivery": "resource",
        },
    )
    assert queued.status_code == 200
    export_id = queued.json()["exportId"]

    terminal = None
    for _ in range(80):
        status_resp = client.post("/tools/call", json={"tool": "os_map.get_export", "exportId": export_id})
        assert status_resp.status_code == 200
        status_body = status_resp.json()
        if status_body["status"] in {"completed", "failed"}:
            terminal = status_body
            break
        time.sleep(0.05)
    assert terminal is not None
    assert terminal["status"] == "completed", terminal
    assert terminal.get("columns", {}).get("selectorMembership") is False

    read = client.get("/resources/read", params={"uri": terminal["resultUri"]})
    assert read.status_code == 200
    csv_text = read.json()["contents"][0]["text"]
    assert (
        "uprn,postcode,oa_code,local_authority_name,lsoa_code,msoa_code,lad_code"
        in csv_text
    )
    assert "selected_by_oa" not in csv_text


def test_os_map_selection_export_accepts_postcode_selection_shorthand(
    client, monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    from server.config import settings
    from server.mcp import resource_catalog
    from tools import os_map

    cache_dir = tmp_path / "ons_geo_cache"
    db_name = "ons_geo_cache.sqlite"
    _seed_ons_geo_uprn_index(cache_dir, db_name)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DIR", str(cache_dir), raising=False)
    monkeypatch.setattr(settings, "ONS_GEO_CACHE_DB", db_name, raising=False)

    os_exports_dir = tmp_path / "os_exports"
    monkeypatch.setattr(os_map, "_OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORT_JOBS_DIR", os_exports_dir / "jobs")
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports_dir)

    queued = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export",
            "exportType": "selection_uprn",
            "selectionSpec": {"postcode": "CV1 2GT"},
            "format": "json",
            "delivery": "resource",
        },
    )
    assert queued.status_code == 200
    export_id = queued.json()["exportId"]

    terminal = None
    for _ in range(80):
        status_resp = client.post(
            "/tools/call",
            json={"tool": "os_map.get_export", "exportId": export_id},
        )
        assert status_resp.status_code == 200
        status_body = status_resp.json()
        if status_body["status"] in {"completed", "failed"}:
            terminal = status_body
            break
        time.sleep(0.05)
    assert terminal is not None
    assert terminal["status"] == "completed", terminal
    assert terminal["rowCount"] == 1

    read = client.get("/resources/read", params={"uri": terminal["resultUri"]})
    assert read.status_code == 200
    payload = json.loads(read.json()["contents"][0]["text"])
    assert payload["rows"][0]["uprn"] == "100023336959"


def test_os_map_selection_export_cache_failure_is_reported(
    client, monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_catalog
    from tools import os_map

    os_exports_dir = tmp_path / "os_exports"
    monkeypatch.setattr(resource_catalog, "OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORTS_DIR", os_exports_dir)
    monkeypatch.setattr(os_map, "_OS_EXPORT_JOBS_DIR", os_exports_dir / "jobs")

    queued = client.post(
        "/tools/call",
        json={
            "tool": "os_map.export",
            "exportType": "selection_uprn",
            "selectionSpec": {"postcode": "CV3 1HB"},
            "format": "json",
            "delivery": "resource",
        },
    )
    assert queued.status_code == 200
    export_id = queued.json()["exportId"]

    terminal = None
    for _ in range(80):
        status_resp = client.post(
            "/tools/call",
            json={"tool": "os_map.get_export", "exportId": export_id},
        )
        assert status_resp.status_code == 200
        status_body = status_resp.json()
        if status_body["status"] in {"completed", "failed"}:
            terminal = status_body
            break
        time.sleep(0.05)
    assert terminal is not None
    assert terminal["status"] == "failed"
    assert terminal["error"]["code"] in {"CACHE_UNAVAILABLE", "CACHE_READ_ERROR"}


def test_os_map_get_export_not_found(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/tools/call",
        json={"tool": "os_map.get_export", "exportId": str(uuid.uuid4())},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "NOT_FOUND"


def test_os_map_get_export_rejects_non_uuid_ids(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/tools/call",
        json={"tool": "os_map.get_export", "exportId": "../../../etc/passwd"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "INVALID_INPUT"


def test_os_map_parsers_cover_edge_cases() -> None:
    from tools import os_map

    assert os_map._parse_bbox("nope") is None
    assert os_map._parse_bbox([1, 2, 3]) is None
    assert os_map._parse_bbox([1, 2, "x", 4]) is None
    assert os_map._parse_bbox([0, 0, 0, 1]) is None  # minLon >= maxLon
    assert os_map._parse_bbox([0, 1, 2, 0]) is None  # minLat >= maxLat

    assert os_map._parse_layers("uprns, buildings, nope") == ["uprns", "buildings"]
    assert os_map._parse_layers(123) is None

    defaults = os_map._parse_limits(None)
    assert defaults["uprns"] == 100
    assert defaults["buildings"] == 100
    assert defaults["road_links"] == 100
    assert defaults["path_links"] == 100

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

    column_config = os_map._normalize_columns_config(
        {"defaultSet": "unknown", "selectorMembership": False}
    )
    assert column_config == {"defaultSet": "maplab_default_v1", "selectorMembership": False}
    assert os_map._csv_columns_from_config({"selectorMembership": False}) == [
        "uprn",
        "postcode",
        "oa_code",
        "local_authority_name",
        "lsoa_code",
        "msoa_code",
        "lad_code",
    ]


def test_os_map_selection_and_aoi_helpers_cover_error_branches(monkeypatch) -> None:
    from tools import os_map

    assert os_map._parse_selection_spec("bad") == (None, "selectionSpec must be an object")
    assert os_map._parse_selection_spec({"selectors": "bad"}) == (
        None,
        "selectionSpec.selectors must be an array of objects",
    )
    assert os_map._parse_selection_spec({"geometry": []}) == (
        None,
        "selectionSpec.geometry must be an object",
    )
    assert os_map._parse_selection_spec({"gssCode": "E05000644"}) == (
        None,
        "selectionSpec.level is required when selectionSpec.gssCode is provided",
    )
    assert os_map._parse_selection_spec({"postcode": ""}) == (
        None,
        "selectionSpec.postcode must be a non-empty string",
    )
    assert os_map._parse_selection_spec({"uprnOverrides": []}) == (
        None,
        "selectionSpec.uprnOverrides must be an object",
    )
    assert os_map._parse_selection_spec({"uprnOverrides": {"include": ["bad"]}}) == (
        None,
        "selectionSpec.uprnOverrides.include must be an array of numeric strings",
    )
    assert os_map._address_selector_spec(
        {
            "selectors": [{"type": "gss_code", "level": "WARD", "code": "E05000644"}],
            "uprnOverrides": {"include": [], "exclude": []},
        }
    ) is None

    status, payload = os_map._selection_cache_error(RuntimeError("cache missing"))
    assert status == 503
    assert payload["code"] == "CACHE_UNAVAILABLE"

    status, payload = os_map._selection_cache_error(sqlite3.OperationalError("bad db"))
    assert status == 503
    assert payload["code"] == "CACHE_READ_ERROR"

    status, payload = os_map._selection_cache_error(ValueError("boom"))
    assert status == 500
    assert payload["code"] == "INTEGRATION_ERROR"

    polygons, warnings = os_map._normalize_polygon_geometry(
        {
            "type": "MultiPolygon",
            "coordinates": [
                [[[-1.0, 52.0], [-0.9, 52.0], [-0.9, 52.1], [-1.0, 52.0]]],
                [[[-1.1, 52.1], [-1.0, 52.1], [-1.0, 52.2], [-1.1, 52.1]]],
            ],
        }
    )
    assert len(polygons) == 2
    assert "AOI_MULTIPOLYGON_SPLIT" in warnings

    polygons, warnings = os_map._normalize_polygon_geometry(
        {
            "rings": [
                [[-1.0, 52.0], [-0.9, 52.0], [-0.9, 52.1], [-1.0, 52.0]],
                [[-1.2, 52.2], [-1.1, 52.2], [-1.1, 52.3], [-1.2, 52.2]],
            ]
        }
    )
    assert len(polygons) == 2
    assert "AOI_ARCGIS_GEOMETRY_NORMALIZED" in warnings
    assert "AOI_MULTIRING_SPLIT" in warnings

    assert os_map._resolve_export_road_aoi(
        selection_spec=None,
        derivation_mode="exact",
        postal_delivery_only=False,
        buffer_meters=20.0,
    ) == (None, None)


def test_os_map_area_limit_and_export_aoi_resolution_branches(monkeypatch) -> None:
    from tools import os_map

    assert os_map._resolve_area_limit_polygons({"selectors": "bad"}) == ([], [], [])

    monkeypatch.setattr(os_map, "get_tool", lambda _name: None)
    polygons, summaries, warnings = os_map._resolve_area_limit_polygons(
        {
            "selectors": [
                {"type": "gss_code", "level": "WARD", "code": "E05000644"},
                {"type": "gss_code", "level": "", "code": ""},
            ]
        }
    )
    assert polygons == []
    assert summaries == []
    assert "AREA_GEOMETRY_TOOL_MISSING" in warnings
    assert any("missing level/code" in warning for warning in warnings)

    class DummyAreaTool:
        def __init__(self, result: tuple[int, object]) -> None:
            self.result = result

        def call(self, args: dict[str, Any]) -> tuple[int, object]:
            return self.result

    monkeypatch.setattr(
        os_map,
        "get_tool",
        lambda _name: DummyAreaTool((500, {"isError": True})),
    )
    _polygons, _summaries, warnings = os_map._resolve_area_limit_polygons(
        {"selectors": [{"type": "gss_code", "level": "WARD", "code": "E05000644"}]}
    )
    assert "AREA_GEOMETRY_LOOKUP_FAILED:E05000644" in warnings

    monkeypatch.setattr(
        os_map,
        "get_tool",
        lambda _name: DummyAreaTool((200, {"id": "E05000644"})),
    )
    _polygons, _summaries, warnings = os_map._resolve_area_limit_polygons(
        {"selectors": [{"type": "gss_code", "level": "WARD", "code": "E05000644"}]}
    )
    assert "AREA_GEOMETRY_MISSING:E05000644" in warnings

    monkeypatch.setattr(
        os_map,
        "_resolve_area_limit_polygons",
        lambda _spec: (
            [{"type": "Polygon", "coordinates": [[[-1.0, 52.0], [-0.9, 52.0], [-0.9, 52.1], [-1.0, 52.0]]]}],
            [{"selectorType": "gss_code"}],
            ["LIMIT"],
        ),
    )
    monkeypatch.setattr(
        os_map,
        "_resolve_address_anchor_polygons",
        lambda **_kwargs: (
            [{"type": "Polygon", "coordinates": [[[-1.0, 52.0], [-0.8, 52.0], [-0.8, 52.2], [-1.0, 52.0]]]}],
            [{"anchorType": "building_polygon"}],
            ["ANCHOR"],
            {"resolvedUprnCount": 1},
        ),
    )
    resolved, warnings = os_map._resolve_export_road_aoi(
        selection_spec={"selectors": []},
        derivation_mode="exact",
        postal_delivery_only=False,
        buffer_meters=20.0,
    )
    assert resolved is not None
    assert len(resolved["queryPolygons"]) == 1
    assert len(resolved["limitPolygons"]) == 1
    assert warnings == ["LIMIT", "ANCHOR"]

    monkeypatch.setattr(
        os_map,
        "_resolve_address_anchor_polygons",
        lambda **_kwargs: ([], [], [], {"resolvedUprnCount": 0}),
    )
    resolved, warnings = os_map._resolve_export_road_aoi(
        selection_spec={"selectors": []},
        derivation_mode="exact",
        postal_delivery_only=False,
        buffer_meters=20.0,
    )
    assert resolved is not None
    assert resolved["limitPolygons"] is None
    assert warnings == ["LIMIT"]


def test_os_map_polygon_selector_resolution_branches(monkeypatch) -> None:
    from tools import os_map

    assert os_map._resolve_polygon_selector({}) == (set(), "polygon selector requires geometry")

    monkeypatch.setattr(os_map, "get_tool", lambda _name: None)
    assert os_map._resolve_polygon_selector({"geometry": {"type": "Polygon"}}) == (
        set(),
        "os_places.polygon not available for polygon selector",
    )

    class DummyPolygonTool:
        def __init__(self, result: tuple[int, object]) -> None:
            self.result = result

        def call(self, args: dict[str, Any]) -> tuple[int, object]:
            return self.result

    monkeypatch.setattr(
        os_map,
        "get_tool",
        lambda _name: DummyPolygonTool((500, {"message": "upstream failed"})),
    )
    assert os_map._resolve_polygon_selector({"geometry": {"type": "Polygon"}}) == (
        set(),
        "upstream failed",
    )

    monkeypatch.setattr(
        os_map,
        "get_tool",
        lambda _name: DummyPolygonTool((200, {"results": "bad"})),
    )
    assert os_map._resolve_polygon_selector({"geometry": {"type": "Polygon"}}) == (set(), None)

    monkeypatch.setattr(
        os_map,
        "get_tool",
        lambda _name: DummyPolygonTool(
            (
                200,
                {"results": [{"uprn": "100023336959"}, {"uprn": "bad"}, "skip"]},
            )
        ),
    )
    uprns, error = os_map._resolve_polygon_selector({"geometry": {"type": "Polygon"}})
    assert error is None
    assert uprns == {"100023336959"}


def test_os_map_address_anchor_resolution_branches(monkeypatch) -> None:
    from tools import os_map

    empty = os_map._resolve_address_anchor_polygons(
        selection_spec={"selectors": [{"type": "gss_code", "level": "WARD", "code": "E05000644"}]},
        derivation_mode="exact",
        postal_delivery_only=False,
        buffer_meters=20.0,
    )
    assert empty == ([], [], [], {"resolvedUprnCount": 0, "selectorCount": 0, "excludedCount": 0})

    monkeypatch.setattr(
        os_map,
        "_resolve_selection_rows",
        lambda **_kwargs: ([{"uprn": "100023336959"}], {"resolvedUprnCount": 1}, []),
    )
    monkeypatch.setattr(os_map, "get_tool", lambda _name: None)
    polygons, summaries, warnings, stats = os_map._resolve_address_anchor_polygons(
        selection_spec={"selectors": [{"type": "uprn", "uprn": "100023336959"}]},
        derivation_mode="exact",
        postal_delivery_only=False,
        buffer_meters=20.0,
    )
    assert polygons == []
    assert summaries == []
    assert warnings == ["UPRN_POINT_LOOKUP_TOOL_MISSING"]
    assert stats == {"resolvedUprnCount": 1}

    class DummyPointTool:
        def __init__(self, result: tuple[int, object]) -> None:
            self.result = result

        def call(self, args: dict[str, Any]) -> tuple[int, object]:
            return self.result

    monkeypatch.setattr(
        os_map,
        "_resolve_selection_rows",
        lambda **_kwargs: (
            [{"uprn": "100023336959"}, {"uprn": "100023336960"}, {"uprn": ""}],
            {"resolvedUprnCount": 2},
            [],
        ),
    )
    monkeypatch.setattr(
        os_map,
        "get_tool",
        lambda _name: DummyPointTool((200, {"result": {"lat": "bad", "lon": 1}})),
    )
    polygons, summaries, warnings, stats = os_map._resolve_address_anchor_polygons(
        selection_spec={"selectors": [{"type": "uprn", "uprn": "100023336959"}]},
        derivation_mode="exact",
        postal_delivery_only=False,
        buffer_meters=20.0,
    )
    assert polygons == []
    assert summaries == []
    assert "UPRN_POINT_INVALID:100023336959" in warnings
    assert "UPRN_POINT_INVALID:100023336960" in warnings
    assert stats == {"resolvedUprnCount": 2}


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
    assert body["render"]["urlTemplate"] == body["render"]["imageUrl"]
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

    # Upstream failure from os_features.query should be surfaced on the layer.
    def failing_features(name: str):  # type: ignore[no-untyped-def]
        if name == "os_features.query":
            return DummyTool((500, {"isError": True, "code": "OS_API_ERROR", "message": "fail"}))
        return orig_get_tool(name)

    monkeypatch.setattr(os_map, "get_tool", failing_features)
    status, payload = os_map._inventory({"bbox": bbox, "layers": ["buildings"]})
    assert status == 200
    assert payload["layers"]["buildings"]["code"] == "OS_API_ERROR"

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


def test_os_maps_helper_normalization_paths() -> None:
    from tools import os_maps

    assert os_maps._num("bad") is None

    assert os_maps._feature_point("bad") is None
    assert os_maps._feature_point({"type": "Feature", "geometry": {"type": "LineString"}}) is None
    assert os_maps._feature_point({"coordinates": ["bad", 1]}) is None
    point = os_maps._feature_point({"lng": "-0.12", "lat": "51.5", "properties": "bad"})
    assert point is not None
    assert point["geometry"]["type"] == "Point"
    assert point["properties"] == {}

    assert os_maps._feature_line("bad") is None
    assert os_maps._feature_line({"type": "Feature", "geometry": {"type": "Polygon"}}) is None
    line = os_maps._feature_line({"geometry": {"type": "LineString", "coordinates": []}})
    assert line is not None
    assert line["geometry"]["type"] == "LineString"

    assert os_maps._feature_polygon("bad") is None
    assert os_maps._feature_polygon({"type": "Feature", "geometry": {"type": "LineString"}}) is None
    polygon = os_maps._feature_polygon({"geometry": {"type": "Polygon", "coordinates": []}})
    assert polygon is not None
    assert polygon["geometry"]["type"] == "Polygon"

    assert os_maps._normalize_feature_collection(None, kind="point") == []
    assert (
        os_maps._normalize_feature_collection(
            {"type": "FeatureCollection", "features": "bad"},
            kind="point",
        )
        == []
    )
    assert os_maps._normalize_feature_collection({"type": "bad"}, kind="point") == []
    line_features = os_maps._normalize_feature_collection(
        [{"geometry": {"type": "LineString", "coordinates": []}}],
        kind="line",
    )
    assert len(line_features) == 1

    local_layers = os_maps._normalize_local_layers(
        [
            "skip",
            {"name": "invalid", "geojson": {"type": "FeatureCollection", "features": []}},
            {
                "geojson": {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": []},
                    "properties": {"x": 1},
                }
            },
            {
                "kind": "bad",
                "geojson": {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-0.1, 51.5]},
                    "properties": {},
                },
            },
            {
                "kind": "bad",
                "geojson": {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": []},
                    "properties": {},
                },
            },
        ]
    )
    assert len(local_layers) == 3
    assert local_layers[0]["name"] == "local_layer_3"
    assert local_layers[0]["kind"] == "polygon"
    assert local_layers[1]["kind"] == "point"
    assert local_layers[2]["kind"] == "line"

    assert os_maps._build_uprn_features("bad") == []
    uprn_features = os_maps._build_uprn_features(
        [{"uprn": "1", "lat": "bad", "lon": -0.1}, {"uprn": "2", "lat": 51.5, "lon": -0.1}]
    )
    assert len(uprn_features) == 1
    assert uprn_features[0]["properties"]["uprn"] == "2"

    assert os_maps._extract_inventory_overlay_layers({"layers": "bad"}) == []
    inventory_layers = os_maps._extract_inventory_overlay_layers(
        {
            "layers": {
                "uprns": {"results": [{"uprn": "100", "lat": 51.5, "lon": -0.1}]},
                "buildings": {
                    "collection": "bld-x",
                    "features": [
                        {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": []}}
                    ],
                },
                "road_links": {"features": []},
                "path_links": {
                    "collection": "path-x",
                    "features": [
                        {"type": "Feature", "geometry": {"type": "LineString", "coordinates": []}}
                    ],
                    "nextPageToken": "10",
                },
            }
        }
    )
    assert {row["id"] for row in inventory_layers} == {
        "inventory_uprns",
        "inventory_buildings",
        "inventory_path_links",
    }
    summary = os_maps._overlay_summary(inventory_layers)
    assert any(row["id"] == "inventory_path_links" and row["nextPageToken"] == "10" for row in summary)

    assert os_maps._normalize_overlay_layers({"overlays": "bad"}) == []
    normalized_overlay = os_maps._normalize_overlay_layers(
        {
            "overlays": {
                "points": [{"lat": 51.5, "lon": -0.1}],
                "lines": [{"geometry": {"type": "LineString", "coordinates": []}}],
                "polygons": [{"geometry": {"type": "Polygon", "coordinates": []}}],
                "localLayers": [{"geojson": {"type": "Feature", "geometry": {"type": "Polygon"}}}],
            }
        }
    )
    assert {row["id"] for row in normalized_overlay} >= {
        "input_points",
        "input_lines",
        "input_polygons",
    }

    req_without_inventory = os_maps._build_inventory_request({"tool": "x"}, [-0.2, 51.4, -0.1, 51.5])
    assert req_without_inventory == {"tool": "os_map.inventory", "bbox": [-0.2, 51.4, -0.1, 51.5]}
    req_with_inventory = os_maps._build_inventory_request(
        {
            "inventory": {
                "layers": ["uprns"],
                "limits": {"uprns": 1},
                "pageTokens": {"road_links": "2"},
                "includeGeometry": {"buildings": False},
                "collections": {"buildings": "custom"},
            }
        },
        [-0.2, 51.4, -0.1, 51.5],
    )
    assert req_with_inventory["layers"] == ["uprns"]
    assert req_with_inventory["limits"]["uprns"] == 1
    assert req_with_inventory["collections"]["buildings"] == "custom"


def test_os_maps_render_validation_and_inventory_error_paths(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_maps

    assert os_maps._maps_render({"bbox": "bad"})[0] == 400
    assert os_maps._maps_render({"bbox": [0, 0, "x", 1]})[0] == 400
    assert os_maps._maps_render({"bbox": [0, 0, 0, 1]})[0] == 400
    assert os_maps._maps_render({"bbox": [0, 0, 1, 1], "size": "bad"})[0] == 400
    assert os_maps._maps_render({"bbox": [0, 0, 1, 1], "size": 64})[0] == 400

    payload = {"bbox": [-0.2, 51.4, -0.1, 51.5], "includeInventory": True}

    monkeypatch.setattr(os_maps, "get_tool", lambda _name: None)
    status, result = os_maps._maps_render(payload)
    assert status == 501
    assert result["code"] == "MISSING_TOOL"

    class DummyTool:
        def __init__(self, response: tuple[int, Any]):
            self.response = response

        def call(self, args: dict[str, Any]):  # noqa: ARG002
            return self.response

    monkeypatch.setattr(
        os_maps,
        "get_tool",
        lambda name: DummyTool((502, {"isError": True, "code": "UPSTREAM"}))
        if name == "os_map.inventory"
        else None,
    )
    status, result = os_maps._maps_render(payload)
    assert status == 502
    assert result["code"] == "UPSTREAM"

    monkeypatch.setattr(
        os_maps,
        "get_tool",
        lambda name: DummyTool((200, "bad"))
        if name == "os_map.inventory"
        else None,
    )
    status, result = os_maps._maps_render(payload)
    assert status == 500
    assert result["code"] == "INTEGRATION_ERROR"
