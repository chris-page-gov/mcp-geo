import json
import time

import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.mcp import http_transport
from server.protocol import PROTOCOL_VERSION
from tools.registry import Tool, register


def test_sse_event_includes_retry():
    evt = http_transport._sse_event("{}", event_id="x", retry_ms=250)
    assert "retry: 250" in evt
    assert "id: x" in evt
    assert "data: {}" in evt


def test_pending_bucket_and_elicitation_seq_edge_cases():
    state = {}
    bucket1 = http_transport._pending_bucket(state)
    bucket1["x"] = 1
    bucket2 = http_transport._pending_bucket(state)
    assert bucket2 is bucket1

    state = {"elicitation_seq": "nope"}
    rid = http_transport._next_elicitation_request_id(state)
    assert rid == "elicitation-1"


def test_resolve_pending_rejects_non_string_id():
    assert http_transport._resolve_pending({}, 123, {"ok": True}) is False


def test_call_tool_error_and_non_dict_content_branch():
    with pytest.raises(ValueError):
        http_transport._call_tool({}, {})
    with pytest.raises(TypeError):
        http_transport._call_tool({"name": "os_mcp.descriptor", "arguments": "bad"}, {})

    register(
        Tool(
            name="test.http_non_dict",
            description="test",
            handler=lambda _payload: (200, "ok"),
        )
    )
    out = http_transport._call_tool({"name": "test.http_non_dict", "arguments": {}}, {})
    assert out.get("ok") is True
    assert out.get("content")


def test_mcp_http_empty_body_and_unknown_response_id():
    client = TestClient(app)
    resp = client.post("/mcp", data=b"", headers={"content-type": "application/json"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == -32600

    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "elicitation-unknown", "result": {"action": "accept"}},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == -32600


def test_mcp_http_missing_params_defaults_and_notification_exception_swallowed(monkeypatch):
    client = TestClient(app)
    init_resp = client.post("/mcp", json={"jsonrpc": "2.0", "id": "i", "method": "initialize", "params": {}})
    session_id = init_resp.headers.get("mcp-session-id")
    assert session_id

    # params omitted -> defaults to {}
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json={"jsonrpc": "2.0", "id": "x", "method": "tools/list"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"]["tools"]

    # Unknown method notification -> exception swallowed, 202 returned.
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json={"jsonrpc": "2.0", "method": "unknown/method", "params": {}},
    )
    assert resp.status_code == 202


def test_mcp_http_capabilities_not_dict_branch():
    client = TestClient(app)
    init_resp = client.post("/mcp", json={"jsonrpc": "2.0", "id": "i", "method": "initialize", "params": {}})
    session_id = init_resp.headers.get("mcp-session-id")
    assert session_id
    http_transport._SESSION_STATE[session_id]["capabilities"] = "bad"  # force branch

    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json={
            "jsonrpc": "2.0",
            "id": "call-1",
            "method": "tools/call",
            "params": {"name": "os_mcp_descriptor", "arguments": {}},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["result"]["ok"] is True


def test_mcp_http_initialize_negotiates_protocol_and_sets_header():
    client = TestClient(app)
    resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "i",
            "method": "initialize",
            "params": {"protocolVersion": "1999-01-01"},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["result"]["protocolVersion"] == PROTOCOL_VERSION
    assert resp.headers.get("mcp-protocol-version") == PROTOCOL_VERSION


def test_mcp_http_rejects_unsupported_protocol_header():
    client = TestClient(app)
    init_resp = client.post("/mcp", json={"jsonrpc": "2.0", "id": "i", "method": "initialize", "params": {}})
    session_id = init_resp.headers.get("mcp-session-id")
    assert session_id
    resp = client.post(
        "/mcp",
        headers={
            "mcp-session-id": session_id,
            "mcp-protocol-version": "2099-01-01",
        },
        json={"jsonrpc": "2.0", "id": "x", "method": "tools/list", "params": {}},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["message"] == "Unsupported protocol version"


def test_mcp_http_rejects_protocol_header_mismatch_from_negotiated_session():
    client = TestClient(app)
    init_resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "i",
            "method": "initialize",
            "params": {"protocolVersion": "2025-11-25"},
        },
    )
    session_id = init_resp.headers.get("mcp-session-id")
    assert session_id
    resp = client.post(
        "/mcp",
        headers={
            "mcp-session-id": session_id,
            "mcp-protocol-version": "2025-03-26",
        },
        json={"jsonrpc": "2.0", "id": "x", "method": "tools/list", "params": {}},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert "does not match negotiated session protocol" in body["error"]["message"]


def test_mcp_http_uses_negotiated_protocol_header_on_subsequent_requests():
    client = TestClient(app)
    init_resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "i",
            "method": "initialize",
            "params": {"protocolVersion": "2025-03-26"},
        },
    )
    session_id = init_resp.headers.get("mcp-session-id")
    assert session_id
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json={"jsonrpc": "2.0", "id": "x", "method": "tools/list", "params": {}},
    )
    assert resp.status_code == 200
    assert resp.headers.get("mcp-protocol-version") == "2025-03-26"


def test_mcp_http_generic_internal_error_handler(monkeypatch):
    client = TestClient(app)
    init_resp = client.post("/mcp", json={"jsonrpc": "2.0", "id": "i", "method": "initialize", "params": {}})
    session_id = init_resp.headers.get("mcp-session-id")
    assert session_id

    monkeypatch.setattr(http_transport, "_dispatch", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    resp = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json={"jsonrpc": "2.0", "id": "x", "method": "tools/list", "params": {}},
    )
    assert resp.status_code == 200
    payload = resp.json()["error"]
    assert payload["code"] == -32603
    assert payload["message"] == "Internal error"
    assert "boom" not in json.dumps(payload)
    assert isinstance(payload.get("data", {}).get("correlationId"), str)


def test_internal_error_logs_exception_type_only(monkeypatch):
    captured: dict[str, object] = {}

    def fake_error(message: str, *args: object) -> None:
        captured["message"] = message
        captured["args"] = args

    monkeypatch.setattr(http_transport.logger, "error", fake_error)
    payload = http_transport._internal_error(
        "id-1", "tools/list", RuntimeError("secret-http-token")
    )
    assert payload["error"]["message"] == "Internal error"
    assert isinstance(payload.get("error", {}).get("data", {}).get("correlationId"), str)

    serialized = json.dumps(captured)
    assert "secret-http-token" not in serialized
    assert "RuntimeError" in serialized
