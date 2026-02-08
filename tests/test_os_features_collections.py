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

