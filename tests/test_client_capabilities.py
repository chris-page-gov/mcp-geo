from server.mcp.client_capabilities import summarize_client_capabilities


def test_summarize_client_capabilities_infers_support_flags():
    summary = summarize_client_capabilities(
        capabilities={
            "tools": {},
            "resources": {},
            "prompts": {},
            "elicitation": {"form": {}},
            "extensions": {"io.modelcontextprotocol/ui": {"mimeTypes": ["text/html;profile=mcp-app"]}},
        },
        requested_protocol_version="2025-03-26",
        negotiated_protocol_version="2025-03-26",
    )
    assert summary["requestedProtocolSupportedByServer"] is True
    supports = summary["supports"]
    assert supports["tools"] is True
    assert supports["resources"] is True
    assert supports["prompts"] is True
    assert supports["elicitationForm"] is True
    assert supports["mcpAppsUi"] is True


def test_summarize_client_capabilities_handles_unknown_requested_protocol():
    summary = summarize_client_capabilities(
        capabilities={},
        requested_protocol_version="1900-01-01",
        negotiated_protocol_version="2025-11-25",
    )
    assert summary["requestedProtocolSupportedByServer"] is False
    assert summary["supports"]["elicitationForm"] is False
