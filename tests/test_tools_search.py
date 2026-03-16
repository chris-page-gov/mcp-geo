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


def test_tools_search_exact_name_returns_linked_ids_tool() -> None:
    resp = client.post("/tools/search", json={"query": "os_linked_ids.get"})
    assert resp.status_code == 200
    tool = resp.json()["tools"][0]
    assert tool["name"] == "os_linked_ids_get"
    assert tool["annotations"]["originalName"] == "os_linked_ids.get"


def test_tools_search_exact_name_returns_resource_bridge_tool() -> None:
    resp = client.post("/tools/search", json={"query": "os_resources.get"})
    assert resp.status_code == 200
    tool = resp.json()["tools"][0]
    assert tool["name"] == "os_resources_get"
    assert tool["annotations"]["originalName"] == "os_resources.get"


def test_tools_search_transcript_phrase_surfaces_harold_wood_recovery_tools() -> None:
    resp = client.post("/tools/search", json={"query": "linked identifiers get feature types"})
    assert resp.status_code == 200
    original_names = [tool["annotations"]["originalName"] for tool in resp.json()["tools"]]
    assert "os_linked_ids.feature_types" in original_names
    assert "os_linked_ids.get" in original_names

    resp = client.post("/tools/search", json={"query": "os_resources get export job read"})
    assert resp.status_code == 200
    original_names = [tool["annotations"]["originalName"] for tool in resp.json()["tools"]]
    assert "os_resources.get" in original_names
