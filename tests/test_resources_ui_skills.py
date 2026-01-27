from fastapi.testclient import TestClient

from server.main import app
from server.mcp import resources as resources_module
from tests.helpers import resource_contents

client = TestClient(app)


def test_resources_list_includes_skills_and_ui():
    resp = client.get("/resources/list")
    assert resp.status_code == 200
    resources = resp.json()["resources"]
    uris = {r.get("uri") for r in resources if isinstance(r, dict)}
    assert "skills://mcp-geo/getting-started" in uris
    assert "ui://mcp-geo/geography-selector" in uris


def test_resources_get_skills_uri():
    resp = client.get("/resources/read", params={"uri": "skills://mcp-geo/getting-started"})
    assert resp.status_code == 200
    contents = resource_contents(resp)
    assert contents[0]["mimeType"] == "text/markdown"
    assert "MCP Geo Skills" in contents[0]["text"]


def test_resources_get_ui_uri():
    resp = client.get("/resources/read", params={"uri": "ui://mcp-geo/geography-selector"})
    assert resp.status_code == 200
    contents = resource_contents(resp)
    assert contents[0]["mimeType"] == "text/html;profile=mcp-app"
    assert "ui" in contents[0].get("_meta", {})
    assert "Geography Selector" in contents[0]["text"]


def test_resources_list_pagination():
    resp = client.get("/resources/list", params={"limit": 1, "page": 1})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("nextPageToken") == "2"
    assert len(payload.get("resources", [])) == 1


def test_resources_describe_pagination():
    resp = client.get("/resources/describe", params={"limit": 1, "page": 1})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("nextPageToken") == "2"
    assert len(payload.get("resources", [])) == 1


def test_resources_read_missing_params():
    resp = client.get("/resources/read")
    assert resp.status_code == 400


def test_resources_read_by_name_with_etag():
    resp = client.get("/resources/read", params={"name": "ui_geography_selector"})
    assert resp.status_code == 200
    etag = resp.headers.get("ETag")
    assert etag
    cached = client.get(
        "/resources/read",
        params={"name": "ui_geography_selector"},
        headers={"If-None-Match": etag},
    )
    assert cached.status_code == 304


def test_resources_read_ui_uri_etag():
    resp = client.get("/resources/read", params={"uri": "ui://mcp-geo/geography-selector"})
    assert resp.status_code == 200
    etag = resp.headers.get("ETag")
    assert etag
    cached = client.get(
        "/resources/read",
        params={"uri": "ui://mcp-geo/geography-selector"},
        headers={"If-None-Match": etag},
    )
    assert cached.status_code == 304


def test_resources_read_skill_uri_etag():
    resp = client.get("/resources/read", params={"uri": "skills://mcp-geo/getting-started"})
    assert resp.status_code == 200
    etag = resp.headers.get("ETag")
    assert etag
    cached = client.get(
        "/resources/read",
        params={"uri": "skills://mcp-geo/getting-started"},
        headers={"If-None-Match": etag},
    )
    assert cached.status_code == 304


def test_resources_read_skill_name_etag():
    resp = client.get("/resources/read", params={"name": "skills_getting_started"})
    assert resp.status_code == 200
    etag = resp.headers.get("ETag")
    assert etag
    cached = client.get(
        "/resources/read",
        params={"name": "skills_getting_started"},
        headers={"If-None-Match": etag},
    )
    assert cached.status_code == 304


def test_resources_read_unknown_uri():
    resp = client.get("/resources/read", params={"uri": "ui://mcp-geo/unknown"})
    assert resp.status_code == 404


def test_resources_read_live_only_prefix():
    resp = client.get(
        "/resources/read",
        params={"uri": "resource://mcp-geo/admin_boundaries"},
    )
    assert resp.status_code == 404


def test_resources_read_live_only_name_prefix():
    resp = client.get(
        "/resources/read",
        params={"name": "resource://mcp-geo/admin_boundaries"},
    )
    assert resp.status_code == 404


def test_read_json_result_helper():
    payload = resources_module._read_json_result("resource://mcp-geo/example", {"ok": True})
    assert payload["contents"][0]["mimeType"] == "application/json"
    assert '"ok":true' in payload["contents"][0]["text"]
