from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_unknown_tool():
    resp = client.post("/tools/call", json={"tool": "does.not_exist", "foo": "bar"})
    assert resp.status_code == 404
    data = resp.json()
    assert data["code"] == "UNKNOWN_TOOL"
