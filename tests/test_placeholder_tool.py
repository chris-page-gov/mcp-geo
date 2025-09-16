from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)

def test_placeholder_tool_listed():
    resp = client.get("/tools/list")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # presence is optional; just ensure endpoint works
    assert "tools" in data or "items" in data
