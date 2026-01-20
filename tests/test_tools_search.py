from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_tools_search_basic_query():
    resp = client.post("/tools/search", json={"query": "postcode"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    assert any(t["name"] == "os_places.by_postcode" for t in data["tools"])


def test_tools_search_regex_mode():
    resp = client.post("/tools/search", json={"query": r"^os_places\.", "mode": "regex"})
    assert resp.status_code == 200
    data = resp.json()
    assert any(t["name"].startswith("os_places.") for t in data["tools"])


def test_tools_search_category_filter():
    resp = client.post("/tools/search", json={"query": "address", "category": "places"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tools"]
    assert all(t["category"] == "places" for t in data["tools"])


def test_tools_search_missing_query():
    resp = client.post("/tools/search", json={})
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("code") == "INVALID_INPUT"
