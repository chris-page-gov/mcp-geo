from fastapi.testclient import TestClient

from server.main import app
from tools.registry import Tool, register

# Use a client that does not re-raise server exceptions so we can inspect the error model
client = TestClient(app, raise_server_exceptions=False)

def raising_handler(payload):
    raise RuntimeError("kaboom exploded")

def test_tool_internal_exception():
    temp_name = "temp.raise_tool"
    register(Tool(name=temp_name, description="temp", handler=raising_handler))
    resp = client.post("/tools/call", json={"tool": temp_name})
    assert resp.status_code == 500
    data = resp.json()
    assert data["isError"] is True
    assert data["code"] == "INTERNAL_ERROR"
    assert "kaboom" in data["message"].lower()
