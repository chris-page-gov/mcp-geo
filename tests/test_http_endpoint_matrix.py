from fastapi.testclient import TestClient

from server.config import settings
from server.main import app

client = TestClient(app)


def test_endpoint_matrix_health_tools_resources_and_playground():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json().get("status") == "OK"

    tools_list = client.get("/tools/list")
    assert tools_list.status_code == 200
    assert isinstance(tools_list.json().get("tools"), list)
    assert "nextPageToken" in tools_list.json()

    tools_describe = client.get("/tools/describe")
    assert tools_describe.status_code == 200
    assert isinstance(tools_describe.json().get("tools"), list)

    tool_call = client.post("/tools/call", json={"tool": "os_mcp.descriptor"})
    assert tool_call.status_code == 200
    descriptor = tool_call.json()
    assert descriptor.get("server") == "mcp-geo"
    assert descriptor.get("transport") == "http"

    resources_list = client.get("/resources/list")
    assert resources_list.status_code == 200
    assert isinstance(resources_list.json().get("resources"), list)

    transcript_get = client.get("/playground/transcript")
    assert transcript_get.status_code == 200
    assert isinstance(transcript_get.json().get("transcript"), list)

    transcript_post = client.post(
        "/playground/tool_call",
        json={
            "tool": "os_mcp.descriptor",
            "input": {"example": True},
            "output": {"ok": True},
        },
    )
    assert transcript_post.status_code == 200
    assert transcript_post.json().get("ok") is True

    events_get = client.get("/playground/events")
    assert events_get.status_code == 200
    assert isinstance(events_get.json().get("events"), list)

    events_post = client.post(
        "/playground/events",
        json={"eventType": "test", "payload": {"ok": True}, "context": {"source": "pytest"}},
    )
    assert events_post.status_code == 200
    assert events_post.json().get("ok") is True

    eval_latest = client.get("/playground/evaluation/latest")
    assert eval_latest.status_code == 200
    assert "path" in eval_latest.json()
    assert "data" in eval_latest.json()


def test_endpoint_matrix_metrics():
    response = client.get("/metrics")
    if settings.METRICS_ENABLED:
        assert response.status_code == 200
        assert "app_requests_total" in response.text
    else:
        assert response.status_code == 404
        body = response.json()
        assert body.get("code") == "NOT_ENABLED"
