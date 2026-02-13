from fastapi.testclient import TestClient

from server.config import settings
from server.main import app

client = TestClient(app)


def test_metrics_endpoint_exposes_counters():
    if not settings.METRICS_ENABLED:
        return
    r = client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "app_requests_total" in text
    assert "app_request_latency_ms_bucket" in text


def test_metrics_endpoint_exposes_tool_and_playground_observability():
    if not settings.METRICS_ENABLED:
        return

    init = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": "init-obs", "method": "initialize", "params": {}},
    )
    assert init.status_code == 200
    session_id = init.headers.get("mcp-session-id")
    assert isinstance(session_id, str) and session_id

    tool_call = client.post(
        "/mcp",
        headers={"mcp-session-id": session_id},
        json={
            "jsonrpc": "2.0",
            "id": "call-obs",
            "method": "tools/call",
            "params": {
                "name": "os_apps_render_geography_selector",
                "arguments": {
                    "initialLat": 52.0,
                    "initialLng": -1.0,
                    "initialZoom": 16,
                },
            },
        },
    )
    assert tool_call.status_code == 200

    client.post(
        "/playground/events",
        json={"eventType": "prompt", "payload": {"text": "obs"}},
    )
    client.get("/playground/orchestration")

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    text = metrics.text
    assert "mcp_tool_calls_total" in text
    assert "mcp_tool_latency_ms_bucket" in text
    assert "mcp_tool_payload_bytes_total" in text
    assert "mcp_tool_cache_hits_total" in text
    assert "mcp_tool_fallback_total" in text
    assert "mcp_tool_delivery_resource_fallback_total" in text
    assert "playground_tool_call_records_total" in text
    assert "playground_orchestration_requests_total" in text
    assert "playground_events_total" in text


def test_rate_limit_enforced():
    # Temporarily lower limit for test (monkeypatch style inline)
    original = settings.RATE_LIMIT_PER_MIN
    orig_bypass = settings.RATE_LIMIT_BYPASS
    settings.RATE_LIMIT_PER_MIN = 5
    settings.RATE_LIMIT_BYPASS = False
    hits: list[int] = []
    for _ in range(7):
        resp = client.get("/health")
        status: int = resp.status_code
        hits.append(status)
    # Restore
    settings.RATE_LIMIT_PER_MIN = original
    settings.RATE_LIMIT_BYPASS = orig_bypass
    assert any(code == 429 for code in hits), hits
