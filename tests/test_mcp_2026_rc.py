from __future__ import annotations

from server import stdio_adapter
from server.mcp import http_transport, rc2026
from server.protocol import MCP_2026_RC_PROTOCOL_VERSION, PROTOCOL_VERSION
from tools.registry import Tool, register


def _rc_meta() -> dict[str, object]:
    return {
        "protocolVersion": MCP_2026_RC_PROTOCOL_VERSION,
        "capabilities": {"elicitation": {}},
        "clientInfo": {"name": "rc-test", "version": "0"},
        "traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01",
    }


def _rpc(msg_id: str, method: str, params: dict[str, object]) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params}


def test_mcp_2026_rc_server_discover_is_feature_gated_and_stateless(client, monkeypatch):
    http_transport._SESSION_STATE.clear()
    monkeypatch.setenv("MCP_2026_RC_ENABLED", "1")

    resp = client.post(
        "/mcp",
        headers={
            "mcp-protocol-version": MCP_2026_RC_PROTOCOL_VERSION,
            "mcp-method": "server/discover",
        },
        json=_rpc("discover-1", "server/discover", {"_meta": _rc_meta()}),
    )

    assert resp.status_code == 200
    assert resp.headers.get("mcp-protocol-version") == MCP_2026_RC_PROTOCOL_VERSION
    assert "mcp-session-id" not in resp.headers
    result = resp.json()["result"]
    assert result["resultType"] == "complete"
    assert result["supportedVersions"][0] == MCP_2026_RC_PROTOCOL_VERSION
    assert result["serverInfo"]["name"] == "mcp-geo"


def test_mcp_2026_rc_rejected_without_feature_flag(client, monkeypatch):
    monkeypatch.delenv("MCP_2026_RC_ENABLED", raising=False)
    resp = client.post(
        "/mcp",
        headers={
            "mcp-protocol-version": MCP_2026_RC_PROTOCOL_VERSION,
            "mcp-method": "server/discover",
        },
        json=_rpc("discover-1", "server/discover", {"_meta": _rc_meta()}),
    )

    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["message"] == "Unsupported protocol version"
    assert PROTOCOL_VERSION in body["error"]["data"]["supported"]


def test_mcp_2026_rc_requires_standard_headers_in_strict_mode(client, monkeypatch):
    monkeypatch.setenv("MCP_2026_RC_ENABLED", "1")
    resp = client.post(
        "/mcp",
        headers={"mcp-protocol-version": MCP_2026_RC_PROTOCOL_VERSION},
        json=_rpc("list-1", "tools/list", {"_meta": _rc_meta()}),
    )

    assert resp.status_code == 400
    assert resp.json()["error"]["message"] == "Missing Mcp-Method header"


def test_mcp_2026_rc_cache_metadata_on_tools_list(client, monkeypatch):
    monkeypatch.setenv("MCP_2026_RC_ENABLED", "1")
    resp = client.post(
        "/mcp",
        headers={
            "mcp-protocol-version": MCP_2026_RC_PROTOCOL_VERSION,
            "mcp-method": "tools/list",
        },
        json=_rpc("list-1", "tools/list", {"_meta": _rc_meta()}),
    )

    assert resp.status_code == 200
    assert "mcp-session-id" not in resp.headers
    result = resp.json()["result"]
    assert result["resultType"] == "complete"
    assert result["ttlMs"] == rc2026.DEFAULT_LIST_TTL_MS
    assert result["cacheScope"] == "public"


def test_mcp_2026_rc_header_only_cache_metadata_on_tools_list(client, monkeypatch):
    monkeypatch.setenv("MCP_2026_RC_ENABLED", "1")
    resp = client.post(
        "/mcp",
        headers={
            "mcp-protocol-version": MCP_2026_RC_PROTOCOL_VERSION,
            "mcp-method": "tools/list",
        },
        json=_rpc("list-1", "tools/list", {}),
    )

    assert resp.status_code == 200
    assert resp.headers.get("mcp-protocol-version") == MCP_2026_RC_PROTOCOL_VERSION
    assert "mcp-session-id" not in resp.headers
    result = resp.json()["result"]
    assert result["resultType"] == "complete"
    assert result["ttlMs"] == rc2026.DEFAULT_LIST_TTL_MS
    assert result["cacheScope"] == "public"


def test_mcp_2026_rc_header_only_initialize_negotiates_rc_stateless(client, monkeypatch):
    http_transport._SESSION_STATE.clear()
    monkeypatch.setenv("MCP_2026_RC_ENABLED", "1")
    resp = client.post(
        "/mcp",
        headers={
            "mcp-protocol-version": MCP_2026_RC_PROTOCOL_VERSION,
            "mcp-method": "initialize",
        },
        json=_rpc("init-1", "initialize", {"capabilities": {}}),
    )

    assert resp.status_code == 200
    assert resp.headers.get("mcp-protocol-version") == MCP_2026_RC_PROTOCOL_VERSION
    assert "mcp-session-id" not in resp.headers
    assert resp.json()["result"]["protocolVersion"] == MCP_2026_RC_PROTOCOL_VERSION
    assert http_transport._SESSION_STATE == {}


def test_mcp_2026_rc_resource_not_found_uses_invalid_params(client, monkeypatch):
    monkeypatch.setenv("MCP_2026_RC_ENABLED", "1")
    uri = "ui://mcp-geo/unknown"
    resp = client.post(
        "/mcp",
        headers={
            "mcp-protocol-version": MCP_2026_RC_PROTOCOL_VERSION,
            "mcp-method": "resources/read",
            "mcp-name": uri,
        },
        json=_rpc("read-1", "resources/read", {"_meta": _rc_meta(), "uri": uri}),
    )

    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == -32602


def test_mcp_2026_rc_toolset_selection_uses_mrtr_input_required(client, monkeypatch):
    monkeypatch.setenv("MCP_2026_RC_ENABLED", "1")
    name = "os_mcp.select_toolsets"
    first = client.post(
        "/mcp",
        headers={
            "mcp-protocol-version": MCP_2026_RC_PROTOCOL_VERSION,
            "mcp-method": "tools/call",
            "mcp-name": name,
        },
        json=_rpc(
            "call-1",
            "tools/call",
            {"_meta": _rc_meta(), "name": name, "arguments": {}},
        ),
    )

    assert first.status_code == 200
    result = first.json()["result"]
    assert result["resultType"] == "input_required"
    assert "toolset_selection" in result["inputRequests"]
    assert result["inputRequests"]["toolset_selection"]["method"] == "elicitation/create"

    retry = client.post(
        "/mcp",
        headers={
            "mcp-protocol-version": MCP_2026_RC_PROTOCOL_VERSION,
            "mcp-method": "tools/call",
            "mcp-name": name,
        },
        json=_rpc(
            "call-2",
            "tools/call",
            {
                "_meta": _rc_meta(),
                "name": name,
                "arguments": {},
                "inputResponses": {
                    "toolset_selection": {
                        "action": "accept",
                        "content": {"includeToolsets": ["core_router"]},
                    }
                },
            },
        ),
    )

    assert retry.status_code == 200
    final = retry.json()["result"]
    assert final["ok"] is True
    assert final["data"]["effectiveFilters"]["includeToolsets"] == ["core_router"]


def test_stdio_server_discover_and_cache_metadata(monkeypatch):
    monkeypatch.setenv("MCP_2026_RC_ENABLED", "1")
    discover = stdio_adapter.handle_server_discover({"_meta": _rc_meta()})
    assert discover["supportedVersions"][0] == MCP_2026_RC_PROTOCOL_VERSION

    listed = stdio_adapter.handle_list_tools({"_meta": _rc_meta()})
    assert listed["resultType"] == "complete"
    assert listed["ttlMs"] == rc2026.DEFAULT_LIST_TTL_MS
    assert listed["cacheScope"] == "public"


def test_stdio_rc_meta_is_ignored_without_feature_flag(monkeypatch):
    monkeypatch.delenv("MCP_2026_RC_ENABLED", raising=False)
    listed = stdio_adapter.handle_list_tools({"_meta": _rc_meta()})

    assert "ttlMs" not in listed
    assert "cacheScope" not in listed


def test_rc2026_helper_guardrail_branches(monkeypatch):
    monkeypatch.setenv("MCP_2026_RC_ENABLED", "1")

    assert rc2026.request_meta_from_params(None) == {}
    meta = rc2026.request_meta_from_params(
        {
            "_meta": {
                "protocolVersion": MCP_2026_RC_PROTOCOL_VERSION,
                "logLevel": " debug ",
            }
        }
    )
    assert meta["logLevel"] == "debug"
    assert rc2026.wants_2026_rc_protocol(
        header_version=None,
        method="tools/list",
        params={"_meta": {"protocolVersion": MCP_2026_RC_PROTOCOL_VERSION}},
    )

    assert rc2026.add_cache_metadata(
        ["not", "dict"],
        method="tools/list",
        protocol_version=MCP_2026_RC_PROTOCOL_VERSION,
    ) == ["not", "dict"]
    assert rc2026.add_cache_metadata(
        {"ok": True},
        method="tools/call",
        protocol_version=MCP_2026_RC_PROTOCOL_VERSION,
    ) == {"ok": True}
    read_result = rc2026.add_cache_metadata(
        {"contents": []},
        method="resources/read",
        protocol_version=MCP_2026_RC_PROTOCOL_VERSION,
    )
    assert read_result["cacheScope"] == "private"
    assert read_result["ttlMs"] == rc2026.DEFAULT_PRIVATE_TTL_MS
    list_result = rc2026.add_cache_metadata(
        {"resources": []},
        method="resources/list",
        protocol_version=MCP_2026_RC_PROTOCOL_VERSION,
    )
    assert list_result["cacheScope"] == "private"

    assert rc2026.client_supports_elicitation_request(None) is False
    issues = rc2026.validate_json_schema_2020_12_guardrails(
        {"$ref": "https://example.test/schema"},
        require_root_object=True,
    )
    assert "$: inputSchema root type must be object" in issues
    assert "$: external $ref is not allowed" in issues
    assert rc2026.validate_json_schema_2020_12_guardrails(
        {"type": "object", "properties": {"a": {}}},
        max_nodes=1,
    ) == ["$.type: schema exceeds 1 nodes", "$.properties: schema exceeds 1 nodes"]
    assert rc2026.validate_json_schema_2020_12_guardrails(
        {"type": "object", "properties": {"a": {"type": "string"}}},
        max_depth=1,
    ) == ["$.properties.a: schema exceeds depth 1"]

    register(
        Tool(
            name="test.rc_guardrail",
            description="temporary schema guardrail fixture",
            input_schema={},
            output_schema={"$ref": "https://example.test/output"},
        )
    )
    registered_issues = rc2026.validate_registered_tool_schemas()
    assert any(issue.startswith("test.rc_guardrail.inputSchema") for issue in registered_issues)
    assert any(issue.startswith("test.rc_guardrail.outputSchema") for issue in registered_issues)


def test_registered_tool_schemas_meet_2026_rc_guardrails():
    assert rc2026.validate_registered_tool_schemas(
        ignore_tool_prefixes=("temp.", "test."),
    ) == []
