import json
from typing import Any

import requests
from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)

class DummyResp:
    def __init__(self, status_code: int, json_data: dict[str, Any]):
        self.status_code = status_code
        self._json = json_data
        self.text = json.dumps(json_data)

    def json(self) -> dict[str, Any]:
        return self._json

# Helper to patch requests.get depending on URL patterns

def patch_requests(
    monkeypatch: MonkeyPatch, mappings: list[tuple[str, tuple[int, dict[str, Any]]]]
):
    monkeypatch.setattr("tools.os_common.client.api_key", "test-key", raising=False)
    def fake_get(url: str, params: dict[str, Any] | None = None, timeout: int = 5):
        for pattern, response in mappings:
            if pattern in url:
                status, body = response
                return DummyResp(status, body)
        return DummyResp(404, {"error": "not found"})
    monkeypatch.setattr(requests, "get", fake_get)


def test_places_by_postcode_normalization(monkeypatch: MonkeyPatch):
    patch_requests(
        monkeypatch,
        [
            (
                "/postcode",
                (
                    200,
                    {
                        "results": [
                            {
                                "DPA": {
                                    "UPRN": "1",
                                    "ADDRESS": "1 Test St",
                                    "LAT": "51.0",
                                    "LNG": "-0.1",
                                    "CLASS": "R",
                                }
                            }
                        ]
                    },
                ),
            )
        ],
    )
    resp = client.post(
        "/tools/call",
        json={"tool": "os_places.by_postcode", "postcode": "SW1A 2AA"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["uprns"][0]["uprn"] == "1"
    assert data["uprns"][0]["lat"] == 51.0


def test_places_search(monkeypatch: MonkeyPatch):
    patch_requests(
        monkeypatch,
        [
            (
                "/find",
                (
                    200,
                    {
                        "results": [
                            {
                                "DPA": {
                                    "UPRN": "2",
                                    "ADDRESS": "2 Example Rd",
                                    "LAT": "51.5",
                                    "LNG": "-0.2",
                                    "CLASS": "C",
                                }
                            }
                        ]
                    },
                ),
            )
        ],
    )
    resp = client.post("/tools/call", json={"tool": "os_places.search", "text": "Example"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["uprn"] == "2"


def test_places_search_sanitized_tool_name(monkeypatch: MonkeyPatch):
    patch_requests(
        monkeypatch,
        [
            (
                "/find",
                (
                    200,
                    {
                        "results": [
                            {
                                "DPA": {
                                    "UPRN": "2",
                                    "ADDRESS": "2 Example Rd",
                                    "LAT": "51.5",
                                    "LNG": "-0.2",
                                    "CLASS": "C",
                                }
                            }
                        ]
                    },
                ),
            )
        ],
    )
    resp = client.post(
        "/tools/call",
        json={"tool": "os_places_search", "text": "Example"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["uprn"] == "2"


def test_names_find(monkeypatch: MonkeyPatch):
    patch_requests(
        monkeypatch,
        [
            (
                "search/names/v1/find",
                (
                    200,
                    {
                        "results": [
                            {
                                "GAZETTEER_ENTRY": {
                                    "ID": "X1",
                                    "NAME1": "London",
                                    "TYPE": "City",
                                    "LOCAL_TYPE": "City",
                                    "GEOMETRY": {
                                        "type": "Point",
                                        "coordinates": [0, 0],
                                    },
                                }
                            }
                        ]
                    },
                ),
            )
        ],
    )
    resp = client.post("/tools/call", json={"tool": "os_names.find", "text": "London"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["name1"] == "London"


def test_features_query(monkeypatch: MonkeyPatch):
    patch_requests(
        monkeypatch,
        [
            (
                "features/ngd/ofa/v1/collections/buildings/items",
                (
                    200,
                    {
                        "numberMatched": 3,
                        "numberReturned": 1,
                        "features": [
                            {
                                "id": "f1",
                                "geometry": {"type": "Polygon"},
                                "properties": {"foo": "bar"},
                            }
                        ]
                    },
                ),
            )
        ],
    )
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
    data = resp.json()
    assert data["features"][0]["id"] == "f1"
    assert data["numberMatched"] == 3
    assert data["numberReturned"] == 1
    assert data["nextPageToken"] == "1"


def test_features_query_bad_limit(monkeypatch: MonkeyPatch):
    patch_requests(monkeypatch, [])
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "limit": 0,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_features_query_bad_bbox_numeric(monkeypatch: MonkeyPatch):
    patch_requests(monkeypatch, [])
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": ["a", "b", "c", "d"],
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_features_query_bad_page_token(monkeypatch: MonkeyPatch):
    patch_requests(monkeypatch, [])
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "pageToken": "not-an-int",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_linked_ids_infer_uprn(monkeypatch: MonkeyPatch):
    patch_requests(
        monkeypatch,
        [
            (
                "search/links/v1/identifierTypes/uprn/100021892956",
                (200, {"identifiers": [{"type": "TOID", "value": "osgb1000000000"}]}),
            )
        ],
    )
    resp = client.post(
        "/tools/call",
        json={"tool": "os_linked_ids.get", "identifier": "100021892956"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["identifierType"] == "uprn"
    assert data["assumedType"] is True
    assert isinstance(data["identifiers"], list)


def test_linked_ids_explicit_toid_type(monkeypatch: MonkeyPatch):
    patch_requests(
        monkeypatch,
        [
            (
                "search/links/v1/identifierTypes/toid/osgb1000000000",
                (200, {"identifiers": [{"type": "UPRN", "value": "100021892956"}]}),
            )
        ],
    )
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_linked_ids.get",
            "identifier": "osgb1000000000",
            "identifierType": "OSGB",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["identifierType"] == "toid"
    assert data["assumedType"] is False


def test_linked_ids_invalid_type_and_no_inference(monkeypatch: MonkeyPatch):
    patch_requests(monkeypatch, [])
    resp = client.post(
        "/tools/call",
        json={"tool": "os_linked_ids.get", "identifier": "abc", "identifierType": "bad"},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_features_query_limit_not_int(monkeypatch: MonkeyPatch):
    patch_requests(monkeypatch, [])
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "limit": "1",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_features_query_negative_page_token(monkeypatch: MonkeyPatch):
    patch_requests(monkeypatch, [])
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_features.query",
            "collection": "buildings",
            "bbox": [0, 0, 1, 1],
            "pageToken": -1,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_features_query_next_token_without_number_matched(monkeypatch: MonkeyPatch):
    patch_requests(
        monkeypatch,
        [
            (
                "features/ngd/ofa/v1/collections/buildings/items",
                (
                    200,
                    {
                        "features": [
                            "bad-entry",
                            {
                                "id": "f2",
                                "geometry": {"type": "Polygon"},
                                "properties": {},
                            },
                        ]
                    },
                ),
            )
        ],
    )
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
    data = resp.json()
    assert data["count"] == 1
    assert data["nextPageToken"] == "1"


def test_linked_ids_infer_toid(monkeypatch: MonkeyPatch):
    patch_requests(
        monkeypatch,
        [
            (
                "search/links/v1/identifierTypes/toid/osgb1000000000",
                (200, {"identifiers": [{"type": "UPRN", "value": "100021892956"}]}),
            )
        ],
    )
    resp = client.post(
        "/tools/call",
        json={"tool": "os_linked_ids.get", "identifier": "osgb1000000000"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["identifierType"] == "toid"
    assert data["assumedType"] is True


def test_linked_ids_status_error(monkeypatch: MonkeyPatch):
    patch_requests(
        monkeypatch,
        [
            (
                "search/links/v1/identifierTypes/uprn/100021892956",
                (403, {"error": "forbidden"}),
            )
        ],
    )
    resp = client.post(
        "/tools/call",
        json={"tool": "os_linked_ids.get", "identifier": "100021892956"},
    )
    assert resp.status_code == 501
    assert resp.json()["code"] in {"OS_API_ERROR", "OS_API_KEY_INVALID"}


def test_vector_tiles_descriptor(monkeypatch: MonkeyPatch):
    # No network call needed (just returns template)
    resp = client.post("/tools/call", json={"tool": "os_vector_tiles.descriptor"})
    assert resp.status_code == 200
    data = resp.json()
    assert "tileTemplate" in data["vectorTiles"]
