import json
from fastapi.testclient import TestClient

from server.main import app


def test_playground_events_logging(monkeypatch, tmp_path):
    from server import config

    log_path = tmp_path / "events.jsonl"
    monkeypatch.setattr(config.settings, "PLAYGROUND_EVENT_LOG_PATH", str(log_path))

    client = TestClient(app)
    client.delete("/playground/orchestration")
    resp = client.post(
        "/playground/events",
        json={
            "eventType": "prompt",
            "payload": {"text": "Hello"},
            "sessionId": "session-events",
            "correlationId": "corr-events",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    list_resp = client.get("/playground/events", params={"sessionId": "session-events"})
    assert list_resp.status_code == 200
    events = list_resp.json()["events"]
    assert events
    assert events[-1]["eventType"] == "prompt"
    assert events[-1]["sessionId"] == "session-events"
    assert events[-1]["correlationId"] == "corr-events"

    lines = log_path.read_text().strip().splitlines()
    assert lines
    logged = json.loads(lines[-1])
    assert logged["eventType"] == "prompt"
    assert logged["sessionId"] == "session-events"


def test_playground_evaluation_latest():
    client = TestClient(app)
    resp = client.get("/playground/evaluation/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert "path" in body
    assert "data" in body


def test_playground_orchestration_filters_by_session():
    client = TestClient(app)
    client.delete("/playground/orchestration")
    client.post(
        "/playground/tool_call",
        json={"tool": "os_mcp_descriptor", "input": {}, "output": {}, "sessionId": "s-a"},
    )
    client.post(
        "/playground/tool_call",
        json={"tool": "os_mcp_descriptor", "input": {}, "output": {}, "sessionId": "s-b"},
    )

    a_resp = client.get("/playground/orchestration", params={"sessionId": "s-a"})
    b_resp = client.get("/playground/orchestration", params={"sessionId": "s-b"})

    assert a_resp.status_code == 200
    assert b_resp.status_code == 200
    assert a_resp.json()["summary"]["toolCallCount"] == 1
    assert b_resp.json()["summary"]["toolCallCount"] == 1


def test_playground_events_invalid_payload_and_pruning():
    from server.mcp import playground

    client = TestClient(app)
    client.delete("/playground/orchestration")

    invalid = client.post("/playground/events", json={"payload": {"text": "missing event type"}})
    assert invalid.status_code == 200
    assert invalid.json()["code"] == "INVALID_INPUT"

    playground.PLAYGROUND_EVENTS[:] = [{} for _ in range(playground.MAX_EVENTS * 2)]
    resp = client.post("/playground/events", json={"eventType": "prompt"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert len(playground.PLAYGROUND_EVENTS) == playground.MAX_EVENTS


def test_playground_latest_evaluation_no_file(monkeypatch):
    from server.mcp import playground

    monkeypatch.setattr(playground.Path, "exists", lambda _self: False)
    payload = playground._latest_evaluation_payload()
    assert payload["path"] is None
    assert payload["data"] is None
