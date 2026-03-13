from __future__ import annotations

from pathlib import Path

from server import stdio_adapter
from server.config import settings


def _stub_os_map_export(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_catalog
    from tools import os_map

    export_dir = tmp_path / "exports"
    monkeypatch.setattr(os_map, "_EXPORTS_DIR", export_dir)
    monkeypatch.setattr(resource_catalog, "EXPORTS_DIR", export_dir)
    monkeypatch.setattr(
        os_map,
        "_inventory",
        lambda payload: (
            200,
            {
                "bbox": payload["bbox"],
                "layers": [],
                "summary": [{"id": "inventory_points", "count": 1}],
            },
        ),
        raising=True,
    )


def _initialize_payload() -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": "init-1", "method": "initialize", "params": {}}


def _call_payload(msg_id: str, method: str, params: dict[str, object]) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params}


def test_os_resources_get_reads_skills_resource(client) -> None:
    resp = client.post(
        "/tools/call",
        json={"tool": "os_resources.get", "uri": "skills://mcp-geo/getting-started"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["mimeType"] == "text/markdown"
    assert body["complete"] is True
    assert body["nextPageToken"] is None
    assert "MCP Geo Skills" in body["text"]


def test_os_resources_get_chunks_utf8_boundaries(monkeypatch, client) -> None:  # type: ignore[no-untyped-def]
    from tools import os_resources

    monkeypatch.setattr(
        os_resources,
        "read_resource_content",
        lambda **_kwargs: {
            "uri": "resource://mcp-geo/demo",
            "mimeType": "text/plain",
            "text": "A😀B😀C",
            "etag": 'W/"demo"',
            "_meta": None,
        },
        raising=True,
    )

    first = client.post(
        "/tools/call",
        json={"tool": "os_resources.get", "uri": "resource://mcp-geo/demo", "maxBytes": 5},
    )
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["text"] == "A😀"
    assert first_body["nextPageToken"] == "5"
    assert first_body["complete"] is False

    second = client.post(
        "/tools/call",
        json={
            "tool": "os_resources.get",
            "uri": "resource://mcp-geo/demo",
            "pageToken": first_body["nextPageToken"],
            "maxBytes": 5,
        },
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["text"] == "B😀"
    assert second_body["nextPageToken"] == "10"
    assert second_body["complete"] is False


def test_os_resources_get_rejects_missing_or_invalid_dynamic_resources(client) -> None:
    missing = client.post(
        "/tools/call",
        json={"tool": "os_resources.get", "uri": "resource://mcp-geo/os-exports/missing.json"},
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "NOT_FOUND"

    traversal = client.post(
        "/tools/call",
        json={"tool": "os_resources.get", "uri": "resource://mcp-geo/exports/../nope.json"},
    )
    assert traversal.status_code == 400
    assert traversal.json()["code"] == "INVALID_INPUT"


def test_os_resources_validation_error_branches(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_resources

    assert os_resources._get_resource({"uri": 1}) == (
        400,
        {"isError": True, "code": "INVALID_INPUT", "message": "uri must be a string"},
    )
    assert os_resources._get_resource({"uri": "resource://mcp-geo/demo", "pageToken": "abc"}) == (
        400,
        {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "pageToken must be a non-negative integer offset",
        },
    )
    assert os_resources._get_resource({"uri": "resource://mcp-geo/demo", "maxBytes": 0}) == (
        400,
        {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "maxBytes must be an integer between 1 and 24576",
        },
    )

    monkeypatch.setattr(
        os_resources,
        "read_resource_content",
        lambda **_kwargs: {
            "uri": "resource://mcp-geo/demo",
            "mimeType": "text/plain",
            "text": "A😀B",
            "etag": 'W/"demo"',
            "_meta": None,
        },
        raising=True,
    )
    status_code, payload = os_resources._get_resource(
        {"uri": "resource://mcp-geo/demo", "pageToken": 2}
    )
    assert status_code == 400
    assert payload["message"] == "pageToken must align to a UTF-8 codepoint boundary"


def test_resource_handoff_helper_branches(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import resource_access, resource_handoff

    monkeypatch.delenv("MCP_HTTP_AUTH_MODE", raising=False)
    monkeypatch.delenv("MCP_HTTP_JWT_HS256_SECRET", raising=False)
    monkeypatch.delenv("MCP_HTTP_AUTH_TOKEN", raising=False)
    assert resource_handoff._current_http_auth_mode() == "off"

    monkeypatch.setenv("MCP_HTTP_JWT_HS256_SECRET", "jwt-secret")
    assert resource_handoff._current_http_auth_mode() == "hs256_jwt"
    monkeypatch.delenv("MCP_HTTP_JWT_HS256_SECRET", raising=False)
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "fallback-token")
    assert resource_handoff._current_http_auth_mode() == "static_bearer"
    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "invalid")
    assert resource_handoff._current_http_auth_mode() == "off"

    assert resource_handoff._resource_name_from_uri("resource-demo") == "resource-demo"
    assert resource_handoff._resource_name_from_uri("resource://mcp-geo/demo") == "demo"
    assert resource_handoff._resource_name_from_uri("resource://mcp-geo/demo/") == "demo"
    assert resource_handoff._resource_mime_from_payload({"mimeType": "text/plain"}, "resource://x") == (
        "text/plain"
    )
    assert resource_handoff._resource_mime_from_payload({"contentType": "application/xml"}, "resource://x") == (
        "application/xml"
    )
    assert (
        resource_handoff._resource_mime_from_payload({"stream": {"mimeType": "text/plain"}}, "resource://x")
        == "text/plain"
    )
    assert resource_handoff._resource_mime_from_payload({}, "ui://mcp-geo/demo") == (
        "text/html;profile=mcp-app"
    )
    assert resource_handoff._resource_mime_from_payload({}, "skills://mcp-geo/getting-started") == "text/markdown"
    assert resource_handoff._resource_mime_from_payload({}, "resource://mcp-geo/data.csv") == "text/csv"
    assert resource_handoff._resource_mime_from_payload({}, "resource://mcp-geo/readme.txt") == "text/plain"
    assert resource_handoff._primary_resource_uri({"stream": {"uri": "resource://mcp-geo/demo"}}) == (
        "resource://mcp-geo/demo"
    )
    assert resource_handoff._http_access("resource://mcp-geo/demo") is None

    monkeypatch.setattr(settings, "MCP_RESOURCE_HTTP_LINKS_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "MCP_PUBLIC_BASE_URL", "https://example.test", raising=False)
    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "off")
    assert resource_handoff._http_access("resource://mcp-geo/demo") is None

    handoff = resource_handoff.build_resource_handoff(
        {
            "resourceUri": "resource://mcp-geo/readme.txt",
            "bytes": 10,
            "sha256": "abc123",
        }
    )
    assert handoff is not None
    assert handoff["bytes"] == 10
    assert handoff["sha256"] == "abc123"
    decorated = resource_handoff.decorate_resource_handoff(
        {"resourceUri": "resource://mcp-geo/readme.txt", "structuredContent": {}}
    )
    assert decorated["structuredContent"]["resourceHandoff"]["mimeType"] == "text/plain"

    try:
        resource_access.read_resource_content(uri=123)  # type: ignore[arg-type]
    except ValueError as exc:
        assert str(exc) == "uri must be a string"
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected ValueError for non-string uri")


def test_raw_tools_call_adds_resource_handoff_without_path(client, monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    _stub_os_map_export(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "MCP_RESOURCE_HTTP_LINKS_ENABLED", False, raising=False)
    monkeypatch.setattr(settings, "MCP_PUBLIC_BASE_URL", "", raising=False)

    resp = client.post(
        "/tools/call",
        json={"tool": "os_map.export", "bbox": [-0.12, 51.5, -0.11, 51.51], "name": "fallback"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["resourceUri"] == body["uri"]
    assert "path" not in body
    assert body["resourceHandoff"]["resourceUri"] == body["resourceUri"]
    assert body["resourceHandoff"]["resolverTool"] == "os_resources.get"
    assert "httpAccess" not in body["resourceHandoff"]
    content = body.get("content", [])
    assert content[0]["type"] == "text"
    assert any(block.get("type") == "resource_link" for block in content if isinstance(block, dict))

    read = client.get("/resources/read", params={"uri": body["resourceUri"]})
    assert read.status_code == 200
    contents = read.json()["contents"]
    assert "_meta" not in contents[0] or "path" not in contents[0].get("_meta", {})


def test_raw_tools_call_requires_auth_when_enabled(client, monkeypatch) -> None:
    from server.mcp import http_transport

    http_transport._SESSION_STATE.clear()
    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "static_bearer")
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "raw-token")

    unauthorized = client.post("/tools/call", json={"tool": "os_mcp.descriptor"})
    assert unauthorized.status_code == 401
    assert unauthorized.json()["code"] == "AUTHENTICATION_FAILED"

    authorized = client.post(
        "/tools/call",
        headers={"Authorization": "Bearer raw-token"},
        json={"tool": "os_mcp.descriptor"},
    )
    assert authorized.status_code == 200
    assert authorized.headers.get("mcp-session-id")


def test_raw_tools_call_validation_errors_keep_session_header(client, monkeypatch) -> None:
    from server.mcp import http_transport

    http_transport._SESSION_STATE.clear()
    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "static_bearer")
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "raw-token")

    resp = client.post(
        "/tools/call",
        headers={"Authorization": "Bearer raw-token"},
        json={"bbox": [-0.12, 51.5, -0.11, 51.51]},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "INVALID_INPUT"
    assert resp.headers.get("mcp-session-id")


def test_raw_http_auth_metrics_cover_auth_and_quota_failures(client, monkeypatch) -> None:
    from server.mcp import http_transport

    http_transport._SESSION_STATE.clear()
    http_transport._AUTH_FAILURES_TOTAL.clear()
    monkeypatch.setattr(http_transport, "_SESSION_QUOTA_REJECTIONS_TOTAL", 0, raising=True)
    monkeypatch.setattr(http_transport, "_SESSION_TOOL_CALL_LIMIT", 1, raising=True)
    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "static_bearer")
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "metrics-token")

    unauthorized = client.get("/resources/read", params={"uri": "skills://mcp-geo/getting-started"})
    assert unauthorized.status_code == 401

    first = client.post(
        "/tools/call",
        headers={"Authorization": "Bearer metrics-token"},
        json={"tool": "os_mcp.descriptor"},
    )
    assert first.status_code == 200
    session_id = first.headers.get("mcp-session-id")
    assert session_id

    quota = client.post(
        "/tools/call",
        headers={
            "Authorization": "Bearer metrics-token",
            "mcp-session-id": session_id,
        },
        json={"tool": "os_mcp.descriptor"},
    )
    assert quota.status_code == 429
    lines = "\n".join(http_transport.build_prometheus_lines())
    assert 'mcp_http_auth_failures_total{reason="authentication"} 1' in lines
    assert "mcp_http_session_quota_rejections_total 1" in lines


def test_mcp_http_wrapped_resource_handoff_and_auth_safe_http_links(
    client, monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    from server.mcp import http_transport

    _stub_os_map_export(monkeypatch, tmp_path)
    http_transport._SESSION_STATE.clear()
    monkeypatch.setenv("MCP_HTTP_AUTH_MODE", "static_bearer")
    monkeypatch.setenv("MCP_HTTP_AUTH_TOKEN", "bridge-token")
    monkeypatch.setattr(settings, "MCP_RESOURCE_HTTP_LINKS_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "MCP_PUBLIC_BASE_URL", "https://example.test", raising=False)

    init_resp = client.post(
        "/mcp",
        headers={"Authorization": "Bearer bridge-token"},
        json=_initialize_payload(),
    )
    assert init_resp.status_code == 200
    session_id = init_resp.headers.get("mcp-session-id")
    assert session_id

    call_resp = client.post(
        "/mcp",
        headers={
            "Authorization": "Bearer bridge-token",
            "mcp-session-id": session_id,
        },
        json=_call_payload(
            "call-1",
            "tools/call",
            {"name": "os_map_export", "arguments": {"bbox": [-0.12, 51.5, -0.11, 51.51]}},
        ),
    )
    assert call_resp.status_code == 200
    result = call_resp.json()["result"]
    handoff = result["data"]["resourceHandoff"]
    assert handoff["resourceUri"] == result["data"]["resourceUri"]
    assert handoff["httpAccess"]["readUrl"].startswith("https://example.test/resources/read?uri=")
    assert handoff["httpAccess"]["requiresAuthorization"] is True
    assert result["structuredContent"]["resourceHandoff"]["resolverTool"] == "os_resources.get"
    assert any(
        block.get("type") == "resource_link" for block in result.get("content", []) if isinstance(block, dict)
    )

    unauthenticated = client.get(
        "/resources/read",
        params={"uri": "skills://mcp-geo/getting-started"},
    )
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["code"] == "AUTHENTICATION_FAILED"

    authenticated = client.get(
        "/resources/read",
        headers={"Authorization": "Bearer bridge-token"},
        params={"uri": "skills://mcp-geo/getting-started"},
    )
    assert authenticated.status_code == 200
    assert authenticated.headers.get("mcp-session-id")


def test_stdio_resource_handoff_added_for_resource_backed_tools(
    monkeypatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    _stub_os_map_export(monkeypatch, tmp_path)
    call = stdio_adapter.handle_call_tool(
        {"name": "os_map_export", "arguments": {"bbox": [-0.12, 51.5, -0.11, 51.51]}}
    )
    assert call.get("ok") is True
    data = call.get("data", {})
    assert "path" not in data
    handoff = data["resourceHandoff"]
    assert handoff["resolverTool"] == "os_resources.get"
    assert any(
        block.get("type") == "resource_link" for block in call.get("content", []) if isinstance(block, dict)
    )
