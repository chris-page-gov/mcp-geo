import base64
import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.mcp import http_transport
from server.protocol import PROTOCOL_VERSION
from tools.registry import Tool, register


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _mint_hs256_jwt_for_coverage(
    secret: str,
    claims: dict[str, object],
    *,
    alg: str = "HS256",
) -> str:
    header = {"alg": alg, "typ": "JWT"}
    encoded_header = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_claims = _b64url(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_claims}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_claims}.{_b64url(signature)}"


class _AuthRequest:
    def __init__(self, authorization: str | None = None) -> None:
        self.headers: dict[str, str] = {}
        if authorization is not None:
            self.headers["authorization"] = authorization


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
    init_resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "i", "method": "initialize", "params": {}},
    )
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
    init_resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "i", "method": "initialize", "params": {}},
    )
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
    init_resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "i", "method": "initialize", "params": {}},
    )
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
    init_resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "i", "method": "initialize", "params": {}},
    )
    session_id = init_resp.headers.get("mcp-session-id")
    assert session_id

    monkeypatch.setattr(
        http_transport,
        "_dispatch",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
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


def test_http_transport_auth_helpers_and_non_applicable_quota(monkeypatch):
    monkeypatch.delenv("MCP_HTTP_AUTH_MODE", raising=False)
    monkeypatch.delenv("MCP_HTTP_JWT_HS256_SECRET", raising=False)
    monkeypatch.delenv("MCP_HTTP_AUTH_TOKEN", raising=False)
    assert http_transport._auth_mode() == "off"

    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "invalid")
    assert http_transport._auth_mode() == "off"

    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "")
    monkeypatch.setenv("MCP_HTTP_JWT_HS256_SECRET", "secret")
    assert http_transport._auth_mode() == "hs256_jwt"

    monkeypatch.delenv("MCP_HTTP_JWT_HS256_SECRET", raising=False)
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "static-token")
    assert http_transport._auth_mode() == "static_bearer"

    assert http_transport._parse_scopes({"scope": "a b"}) == {"a", "b"}
    assert http_transport._parse_scopes({"scp": ["a", "b"]}) == {"a", "b"}
    assert http_transport._parse_scopes({"scp": "a b"}) == {"a", "b"}
    assert http_transport._parse_scopes({}) == set()

    state = {"tool_call_count": 0}
    monkeypatch.setattr(http_transport, "_SESSION_TOOL_CALL_LIMIT", 0)
    http_transport._enforce_session_quota("tools/list", state)
    http_transport._enforce_session_quota("tools/call", state)
    assert state["tool_call_count"] == 0


def test_http_transport_error_response_helpers():
    auth = json.loads(http_transport._authentication_failure_response("msg-1", {}).body)
    assert auth["error"]["message"] == "Authentication failed"

    authorization = json.loads(http_transport._authorization_failure_response("msg-2", {}).body)
    assert authorization["error"]["message"] == "Forbidden"

    quota = json.loads(http_transport._session_quota_failure_response("msg-3", {}).body)
    assert quota["error"]["message"] == "Session quota exceeded"


def test_http_transport_auth_error_branches(monkeypatch):
    monkeypatch.setattr(
        http_transport.base64,
        "urlsafe_b64decode",
        lambda _value: (_ for _ in ()).throw(ValueError("bad-base64")),
    )
    with pytest.raises(http_transport.AuthenticationError):
        http_transport._b64url_decode("ignored")

    with pytest.raises(http_transport.AuthenticationError):
        http_transport._bearer_token_from_request(_AuthRequest())

    with pytest.raises(http_transport.AuthenticationError):
        http_transport._bearer_token_from_request(_AuthRequest("Bearer   "))

    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "off")
    assert http_transport._authenticate_request(_AuthRequest(), {}) is None

    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "static_bearer")
    monkeypatch.delenv("MCP_HTTP_AUTH_TOKEN", raising=False)
    with pytest.raises(http_transport.AuthenticationError):
        http_transport._authenticate_request(_AuthRequest("Bearer test"), {})

    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "expected-token")
    with pytest.raises(http_transport.AuthenticationError):
        http_transport._authenticate_request(_AuthRequest("Bearer wrong-token"), {})


def test_http_transport_auth_subject_binding_uses_session_lock(monkeypatch):
    class TrackingLock:
        def __init__(self) -> None:
            self.depth = 0

        def __enter__(self):
            self.depth += 1
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            self.depth -= 1

    class LockedSession(dict[str, object]):
        def __init__(self, lock: TrackingLock) -> None:
            super().__init__()
            self.lock = lock

        def get(self, key: str, default=None):
            if key == "auth_subject":
                assert self.lock.depth > 0
            return super().get(key, default)

        def __setitem__(self, key: str, value: object) -> None:
            if key in {"auth_subject", "auth_mode"}:
                assert self.lock.depth > 0
            super().__setitem__(key, value)

    tracking_lock = TrackingLock()
    session_state = LockedSession(tracking_lock)
    monkeypatch.setattr(http_transport, "_SESSION_LOCK", tracking_lock)
    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "static_bearer")
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "expected-token")

    claims = http_transport._authenticate_request(
        _AuthRequest("Bearer expected-token"),
        session_state,
    )

    assert claims == {"sub": "static-bearer-client", "scope": "mcp"}
    assert session_state["auth_subject"] == "static-bearer-client"
    assert session_state["auth_mode"] == "static_bearer"
    assert tracking_lock.depth == 0


def test_http_transport_verify_hs256_jwt_error_paths(monkeypatch):
    secret = "coverage-secret"
    now = int(time.time())

    monkeypatch.delenv("MCP_HTTP_JWT_HS256_SECRET", raising=False)
    with pytest.raises(http_transport.AuthenticationError):
        http_transport._verify_hs256_jwt("a.b.c")

    monkeypatch.setenv("MCP_HTTP_JWT_HS256_SECRET", secret)
    with pytest.raises(http_transport.AuthenticationError):
        http_transport._verify_hs256_jwt("not-a-jwt")

    bad_signature = (
        _mint_hs256_jwt_for_coverage(secret, {"sub": "user", "exp": now + 60})[:-2]
        + "xx"
    )
    with pytest.raises(http_transport.AuthenticationError):
        http_transport._verify_hs256_jwt(bad_signature)

    wrong_alg = _mint_hs256_jwt_for_coverage(secret, {"sub": "user", "exp": now + 60}, alg="RS256")
    with pytest.raises(http_transport.AuthenticationError):
        http_transport._verify_hs256_jwt(wrong_alg)

    expired = _mint_hs256_jwt_for_coverage(secret, {"sub": "user", "exp": now - 120})
    with pytest.raises(http_transport.AuthenticationError):
        http_transport._verify_hs256_jwt(expired)

    future_nbf = _mint_hs256_jwt_for_coverage(
        secret,
        {"sub": "user", "exp": now + 300, "nbf": now + 120},
    )
    with pytest.raises(http_transport.AuthenticationError):
        http_transport._verify_hs256_jwt(future_nbf)

    missing_sub = _mint_hs256_jwt_for_coverage(secret, {"exp": now + 300})
    with pytest.raises(http_transport.AuthenticationError):
        http_transport._verify_hs256_jwt(missing_sub)

    monkeypatch.setenv("MCP_HTTP_JWT_AUDIENCE", "mcp-geo")
    audience_mismatch = _mint_hs256_jwt_for_coverage(
        secret,
        {"sub": "user", "exp": now + 300, "aud": "other"},
    )
    with pytest.raises(http_transport.AuthorizationError):
        http_transport._verify_hs256_jwt(audience_mismatch)

    monkeypatch.delenv("MCP_HTTP_JWT_AUDIENCE", raising=False)
    monkeypatch.setenv("MCP_HTTP_JWT_ISSUER", "https://issuer.example")
    issuer_mismatch = _mint_hs256_jwt_for_coverage(
        secret,
        {"sub": "user", "exp": now + 300, "iss": "https://wrong.example"},
    )
    with pytest.raises(http_transport.AuthorizationError):
        http_transport._verify_hs256_jwt(issuer_mismatch)

    monkeypatch.delenv("MCP_HTTP_JWT_ISSUER", raising=False)
    monkeypatch.setenv("MCP_HTTP_JWT_REQUIRED_SCOPES", "mcp:invoke")
    missing_scope = _mint_hs256_jwt_for_coverage(
        secret,
        {"sub": "user", "exp": now + 300, "scope": "other"},
    )
    with pytest.raises(http_transport.AuthorizationError):
        http_transport._verify_hs256_jwt(missing_scope)
