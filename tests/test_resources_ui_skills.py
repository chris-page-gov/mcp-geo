from fastapi.testclient import TestClient

from server.main import app
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
    assert contents[0]["mimeType"].startswith("text/html")
    assert "Geography Selector" in contents[0]["text"]


def test_resources_get_ui_uri_skybridge():
    resp = client.get(
        "/resources/read",
        params={"uri": "ui://mcp-geo/geography-selector.html"},
    )
    assert resp.status_code == 200
    contents = resource_contents(resp)
    assert contents[0]["mimeType"] == "text/html+skybridge"
    assert "openai/widgetCSP" in contents[0].get("_meta", {})
