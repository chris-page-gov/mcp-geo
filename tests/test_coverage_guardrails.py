from fastapi.testclient import TestClient

from server.main import app
from tools.typing_utils import parse_float


def test_parse_float_string_and_object_paths():
    assert parse_float(" ") == 0.0
    assert parse_float("") == 0.0
    assert parse_float("1.25") == 1.25
    assert parse_float("not-a-number") == 0.0

    class Floaty:
        def __float__(self):
            return 2.0

    class BadFloaty:
        def __float__(self):
            raise TypeError("nope")

    assert parse_float(Floaty()) == 2.0
    assert parse_float(BadFloaty()) == 0.0


def test_tools_search_invalid_regex_returns_400():
    client = TestClient(app)
    resp = client.post("/tools/search", json={"query": "[", "mode": "regex"})
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("code") == "INVALID_INPUT"


def test_os_mcp_descriptor_invalid_params():
    client = TestClient(app)
    resp = client.post("/tools/call", json={"tool": "os_mcp.descriptor", "category": 123})
    assert resp.status_code == 400
    assert resp.json().get("code") == "INVALID_INPUT"
