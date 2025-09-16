import json
import types
from typing import Any
import requests

from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

class DummyResp:
    def __init__(self, status_code: int, json_data: dict[str, Any]):
        self.status_code = status_code
        self._json = json_data
        self.text = json.dumps(json_data)
    def json(self):
        return self._json

# Helper to patch requests.get depending on URL patterns

def patch_requests(monkeypatch, mappings):
    def fake_get(url, params=None, timeout=5):
        for pattern, response in mappings:
            if pattern in url:
                status, body = response
                return DummyResp(status, body)
        return DummyResp(404, {"error": "not found"})
    monkeypatch.setattr(requests, "get", fake_get)


def test_places_by_postcode_normalization(monkeypatch):
    patch_requests(monkeypatch, [
        ("/postcode", (200, {"results": [{"DPA": {"UPRN": "1","ADDRESS": "1 Test St","LAT": "51.0","LNG": "-0.1","CLASS": "R"}}]})),
    ])
    resp = client.post("/tools/call", json={"tool": "os_places.by_postcode", "postcode": "SW1A 2AA"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["uprns"][0]["uprn"] == "1"
    assert data["uprns"][0]["lat"] == 51.0


def test_places_search(monkeypatch):
    patch_requests(monkeypatch, [
        ("/find", (200, {"results": [{"DPA": {"UPRN": "2","ADDRESS": "2 Example Rd","LAT": "51.5","LNG": "-0.2","CLASS": "C"}}]})),
    ])
    resp = client.post("/tools/call", json={"tool": "os_places.search", "text": "Example"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["uprn"] == "2"


def test_names_find(monkeypatch):
    patch_requests(monkeypatch, [
        ("search/names/v1/find", (200, {"results": [{"GAZETTEER_ENTRY": {"ID": "X1","NAME1": "London","TYPE": "City","LOCAL_TYPE": "City","GEOMETRY": {"type": "Point","coordinates": [0,0]}}}]})),
    ])
    resp = client.post("/tools/call", json={"tool": "os_names.find", "text": "London"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["name1"] == "London"


def test_features_query(monkeypatch):
    patch_requests(monkeypatch, [
        ("features/v1/buildings", (200, {"features": [{"id": "f1","geometry": {"type": "Polygon"},"properties": {"foo": "bar"}}]})),
    ])
    resp = client.post("/tools/call", json={"tool": "os_features.query", "collection": "buildings", "bbox": [0,0,1,1]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["features"][0]["id"] == "f1"


def test_vector_tiles_descriptor(monkeypatch):
    # No network call needed (just returns template)
    resp = client.post("/tools/call", json={"tool": "os_vector_tiles.descriptor"})
    assert resp.status_code == 200
    data = resp.json()
    assert "tileTemplate" in data["vectorTiles"]
