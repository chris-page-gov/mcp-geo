from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def _reset_orchestration() -> None:
    client.delete("/playground/orchestration")


def test_playground_transcript_initial():
    _reset_orchestration()
    resp = client.get("/playground/transcript")
    assert resp.status_code == 200
    assert "transcript" in resp.json()


def test_playground_invalid_payload():
    # Missing required 'tool'
    resp = client.post("/playground/tool_call", json={"input": {"x": 1}})
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("isError")
    assert body.get("code") == "INVALID_INPUT"


def test_playground_record_and_prune():
    _reset_orchestration()
    # Add more than MAX_TRANSCRIPT entries to trigger prune branch
    for i in range(25):
        resp = client.post(
            "/playground/tool_call",
            json={
                "tool": f"tool{i}",
                "input": {"n": i},
                "output": {"ok": True},
                "sessionId": "session-prune",
            },
        )
        assert resp.json().get("ok") is True
    resp2 = client.get("/playground/transcript", params={"sessionId": "session-prune"})
    data = resp2.json()["transcript"]
    assert len(data) <= 10


def test_playground_orchestration_summary_and_reset():
    _reset_orchestration()

    tool_resp = client.post(
        "/playground/tool_call",
        json={
            "tool": "os_mcp_descriptor",
            "input": {"tool": "os_mcp.descriptor"},
            "output": {"ok": True},
            "sessionId": "session-1",
            "correlationId": "corr-1",
        },
    )
    assert tool_resp.status_code == 200

    event_resp = client.post(
        "/playground/events",
        json={
            "eventType": "prompt",
            "payload": {"text": "Hello"},
            "sessionId": "session-1",
            "correlationId": "corr-1",
        },
    )
    assert event_resp.status_code == 200

    summary = client.get("/playground/orchestration", params={"sessionId": "session-1"})
    assert summary.status_code == 200
    body = summary.json()
    assert body["summary"]["toolCallCount"] == 1
    assert body["summary"]["eventCount"] == 1
    assert body["summary"]["toolCounts"]["os_mcp_descriptor"] == 1
    assert body["summary"]["eventTypeCounts"]["prompt"] == 1
    assert "evaluation" in body

    reset = client.delete("/playground/orchestration")
    assert reset.status_code == 200
    assert reset.json()["ok"] is True

    after = client.get("/playground/orchestration")
    assert after.status_code == 200
    assert after.json()["summary"]["toolCallCount"] == 0
    assert after.json()["summary"]["eventCount"] == 0
