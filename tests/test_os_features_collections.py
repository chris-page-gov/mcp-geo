from __future__ import annotations

from typing import Any


def test_os_features_collections_latest_by_base(client, monkeypatch, mock_os_client) -> None:  # type: ignore[no-untyped-def]
    from tools import os_common, os_features

    fake_client = os_common.client
    monkeypatch.setattr(os_features, "client", fake_client)

    def ngd_collections_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        return 200, {
            "collections": [
                {
                    "id": "trn-ntwk-roadlink-5",
                    "title": "RoadLink",
                    "description": "v5",
                },
                {
                    "id": "trn-ntwk-roadlink-4",
                    "title": "RoadLink",
                    "description": "v4",
                },
                {
                    "id": "bld-fts-buildingpart-1",
                    "title": "Building Part",
                    "description": "",
                },
                {"id": "unversioned", "title": "Unversioned", "description": ""},
            ]
        }

    # Match both /collections and /collections/{id}/items URLs; this test only calls /collections.
    mock_os_client["features/ngd/ofa/v1/collections"] = ngd_collections_handler

    resp = client.post("/tools/call", json={"tool": "os_features.collections"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["latestByBaseId"]["trn-ntwk-roadlink"] == "trn-ntwk-roadlink-5"
    assert body["latestByBaseId"]["bld-fts-buildingpart"] == "bld-fts-buildingpart-1"
    assert "unversioned" not in body["latestByBaseId"].values()
    assert body["count"] == len(body["collections"])


def test_os_features_collections_q_filter(client, monkeypatch, mock_os_client) -> None:  # type: ignore[no-untyped-def]
    from tools import os_common, os_features

    fake_client = os_common.client
    monkeypatch.setattr(os_features, "client", fake_client)

    def ngd_collections_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        return 200, {
            "collections": [
                {"id": "trn-ntwk-roadlink-5", "title": "RoadLink", "description": "v5"},
                {"id": "bld-fts-buildingpart-1", "title": "Building Part", "description": ""},
            ]
        }

    mock_os_client["features/ngd/ofa/v1/collections"] = ngd_collections_handler

    resp = client.post("/tools/call", json={"tool": "os_features.collections", "q": "roadlink-5"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["collections"][0]["id"] == "trn-ntwk-roadlink-5"


def test_os_features_query_polygon_filter_projection_sort_and_queryables(
    client, monkeypatch, mock_os_client
) -> None:  # type: ignore[no-untyped-def]
    from tools import os_common, os_features

    fake_client = os_common.client
    monkeypatch.setattr(os_features, "client", fake_client)

    def items_handler(url: str, params: dict[str, Any]):
        assert "bbox" in params
        return 200, {
            "numberMatched": 3,
            "numberReturned": 3,
            "features": [
                {
                    "id": "f2",
                    "geometry": {"type": "Point", "coordinates": [0.8, 0.8]},
                    "properties": {"name": "Beta", "height": 12, "status": "active", "drop": "x"},
                },
                {
                    "id": "f1",
                    "geometry": {"type": "Point", "coordinates": [0.2, 0.2]},
                    "properties": {"name": "Alpha", "height": 25, "status": "active", "drop": "y"},
                },
                {
                    "id": "f3",
                    "geometry": {"type": "Point", "coordinates": [2.0, 2.0]},
                    "properties": {"name": "Gamma", "height": 8, "status": "inactive", "drop": "z"},
                },
            ],
        }

    def queryables_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        return 200, {"type": "object", "properties": {"status": {"type": "string"}}}

    mock_os_client["features/ngd/ofa/v1/collections/bld-fts-buildingpart-2/items"] = items_handler
    mock_os_client["features/ngd/ofa/v1/collections/bld-fts-buildingpart-2/queryables"] = queryables_handler

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "polygon": [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
            "filter": {"status": "active", "height": {"gte": 10}},
            "sortBy": "-height",
            "includeFields": ["name", "height", "status", "drop"],
            "excludeFields": ["drop"],
            "includeQueryables": True,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert [feature["id"] for feature in body["features"]] == ["f1", "f2"]
    assert body["features"][0]["properties"] == {"name": "Alpha", "height": 25, "status": "active"}
    assert "queryables" in body
    assert body["queryables"]["properties"]["status"]["type"] == "string"
    assert body["requestedCollection"] == "buildings"


def test_os_features_query_result_type_hits(client, monkeypatch, mock_os_client) -> None:  # type: ignore[no-untyped-def]
    from tools import os_common, os_features

    fake_client = os_common.client
    monkeypatch.setattr(os_features, "client", fake_client)

    def items_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        return 200, {
            "features": [
                {
                    "id": "f1",
                    "geometry": {"type": "Point", "coordinates": [0.1, 0.1]},
                    "properties": {"status": "active"},
                }
            ]
        }

    mock_os_client["features/ngd/ofa/v1/collections/bld-fts-buildingpart-2/items"] = items_handler

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "resultType": "hits",
            "filter": {"status": "active"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["resultType"] == "hits"
    assert body["features"] == []
    assert body["count"] == 0
    assert body["numberReturned"] == 0


def test_os_features_query_limit_is_clamped(client, monkeypatch, mock_os_client) -> None:  # type: ignore[no-untyped-def]
    from tools import os_common, os_features

    fake_client = os_common.client
    monkeypatch.setattr(os_features, "client", fake_client)

    def items_handler(url: str, params: dict[str, Any]):
        assert params.get("limit") == 100
        return 200, {"numberMatched": 1000, "features": []}

    mock_os_client["features/ngd/ofa/v1/collections/bld-fts-buildingpart-2/items"] = items_handler

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "limit": 500,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["limit"] == 100
    assert "RESULT_LIMIT_CLAMPED" in body["hints"]["warnings"]


def test_os_features_query_number_returned_matches_feature_length(
    client, monkeypatch, mock_os_client
) -> None:  # type: ignore[no-untyped-def]
    from tools import os_common, os_features

    fake_client = os_common.client
    monkeypatch.setattr(os_features, "client", fake_client)

    def items_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        return 200, {
            "numberMatched": 5,
            "numberReturned": 999,
            "features": [
                {
                    "id": "f1",
                    "geometry": {"type": "Point", "coordinates": [0.1, 0.1]},
                    "properties": {"name": "One"},
                }
            ],
        }

    mock_os_client["features/ngd/ofa/v1/collections/bld-fts-buildingpart-2/items"] = items_handler

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "limit": 1,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["features"]) == 1
    assert body["numberReturned"] == 1
    assert body["count"] == 1


def test_os_features_query_local_filter_reports_partial_scan(
    client, monkeypatch, mock_os_client
) -> None:  # type: ignore[no-untyped-def]
    from tools import os_common, os_features

    fake_client = os_common.client
    monkeypatch.setattr(os_features, "client", fake_client)

    def items_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        return 200, {
            "numberMatched": 200,
            "features": [
                {
                    "id": "f1",
                    "geometry": {"type": "Point", "coordinates": [0.1, 0.1]},
                    "properties": {"status": "active"},
                }
            ],
        }

    mock_os_client["features/ngd/ofa/v1/collections/bld-fts-buildingpart-2/items"] = items_handler

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "limit": 1,
            "filter": {"status": "active"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["hints"]["filterApplied"] == "local"
    assert body["hints"]["scan"]["partial"] is True
    assert "LOCAL_FILTER_PARTIAL_SCAN" in body["hints"]["warnings"]


def test_os_features_query_resource_delivery(
    client, monkeypatch, mock_os_client
) -> None:  # type: ignore[no-untyped-def]
    from tools import os_common, os_features

    fake_client = os_common.client
    monkeypatch.setattr(os_features, "client", fake_client)

    def items_handler(url: str, params: dict[str, Any]):  # noqa: ARG001
        return 200, {
            "numberMatched": 1,
            "features": [
                {
                    "id": "f1",
                    "geometry": {"type": "Point", "coordinates": [0.1, 0.1]},
                    "properties": {
                        "name": "One",
                        "long_text": "x" * 3000,
                    },
                }
            ],
        }

    def fake_write(prefix: str, payload: dict[str, Any]):
        return {
            "resourceUri": f"resource://mcp-geo/os-exports/{prefix}.json",
            "bytes": 123,
            "sha256": "abc123",
            "path": "/tmp/resource.json",
        }

    mock_os_client["features/ngd/ofa/v1/collections/bld-fts-buildingpart-2/items"] = items_handler
    monkeypatch.setattr(os_features, "write_resource_payload", fake_write, raising=True)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "delivery": "auto",
            "inlineMaxBytes": 1,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["delivery"] == "resource"
    assert body["resourceUri"].startswith("resource://mcp-geo/os-exports/")


def test_os_features_query_rejects_non_closed_polygon(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]],
        },
    )
    assert resp.status_code == 400
    assert "closed" in resp.json()["message"].lower()
