from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_resources_list_includes_skills_and_ui():
    resp = client.get("/resources/list")
    assert resp.status_code == 200
    resources = resp.json()["resources"]
    uris = {r.get("uri") for r in resources if isinstance(r, dict)}
    assert "skills://mcp-geo/getting-started" in uris
    assert "ui://mcp-geo/geography-selector" in uris


def test_resources_get_skills_uri():
    resp = client.get("/resources/get", params={"uri": "skills://mcp-geo/getting-started"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mimeType"] == "text/markdown"
    assert "MCP Geo Skills" in body["content"]


def test_resources_get_ui_uri():
    resp = client.get("/resources/get", params={"uri": "ui://mcp-geo/geography-selector"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mimeType"].startswith("text/html")
    assert "Geography Selector" in body["content"]
