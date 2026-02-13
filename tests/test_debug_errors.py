from fastapi.testclient import TestClient
from server.main import app
from tools.registry import Tool, register
from server.config import settings
from typing import Any
from _pytest.monkeypatch import MonkeyPatch

client = TestClient(app, raise_server_exceptions=False)

def boom(payload: dict[str, Any]):
    raise RuntimeError("debug trace path")

def test_debug_errors(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("DEBUG_ERRORS", "1")
    # Force settings.DEBUG_ERRORS to True if it's dynamically read; else patch attribute
    try:
        settings.DEBUG_ERRORS = True
    except Exception:
        pass
    name = "temp.debug_tool"
    register(Tool(name=name, description="d", handler=boom))
    resp = client.post("/tools/call", json={"tool": name})
    assert resp.status_code == 500
    data = resp.json()
    assert data["code"] == "INTERNAL_ERROR"
    # traceback should be present when DEBUG_ERRORS true
    assert "traceback" in data
    assert "debug trace path" in data["message"].lower()
