from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_places_search_missing_text():
    resp = client.post("/tools/call", json={"tool": "os_places.search"})
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"


def test_places_by_uprn_missing():
    resp = client.post("/tools/call", json={"tool": "os_places.by_uprn"})
    assert resp.status_code == 400


def test_places_within_bad_bbox():
    resp = client.post("/tools/call", json={"tool": "os_places.within", "bbox": [0,1,2]})
    assert resp.status_code == 400


def test_features_query_missing_collection():
    resp = client.post("/tools/call", json={"tool": "os_features.query", "bbox": [0,0,1,1]})
    assert resp.status_code == 400


def test_features_query_bad_bbox():
    resp = client.post("/tools/call", json={"tool": "os_features.query", "collection": "buildings", "bbox": [0,0,1]})
    assert resp.status_code == 400
