from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_tools_search_basic_query():
    resp = client.post("/tools/search", json={"query": "postcode"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1
    assert any(t["name"] == "os_places_by_postcode" for t in data["tools"])
    first = data["tools"][0]
    assert "annotations" in first
    assert "originalName" in first["annotations"]


def test_tools_search_regex_mode():
    resp = client.post("/tools/search", json={"query": r"^os_places\.", "mode": "regex"})
    assert resp.status_code == 200
    data = resp.json()
    assert any(t["name"].startswith("os_places_") for t in data["tools"])


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


def test_tools_search_toolset_include_filter():
    resp = client.post("/tools/search", json={"query": "dataset", "toolset": "ons_selection"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tools"]
    original_names = [t.get("annotations", {}).get("originalName") for t in data["tools"]]
    assert all(
        isinstance(name, str)
        and (name.startswith("ons_select.") or name.startswith("ons_search.") or name.startswith("ons_codes."))
        for name in original_names
    )


def test_tools_search_toolset_exclude_filter():
    resp = client.post(
        "/tools/search",
        json={"query": "address", "excludeToolsets": ["places_names"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["tools"]
    original_names = [t.get("annotations", {}).get("originalName") for t in data["tools"]]
    assert all(
        isinstance(name, str)
        and not (
            name.startswith("os_places.")
            or name.startswith("os_names.")
            or name == "os_linked_ids.get"
        )
        for name in original_names
    )
