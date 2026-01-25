import json
from fastapi.testclient import TestClient

from server.main import app


def test_playground_events_logging(monkeypatch, tmp_path):
    from server import config

    log_path = tmp_path / "events.jsonl"
    monkeypatch.setattr(config.settings, "PLAYGROUND_EVENT_LOG_PATH", str(log_path))

    client = TestClient(app)
    resp = client.post(
        "/playground/events",
        json={"eventType": "prompt", "payload": {"text": "Hello"}},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    list_resp = client.get("/playground/events")
    assert list_resp.status_code == 200
    events = list_resp.json()["events"]
    assert events
    assert events[-1]["eventType"] == "prompt"

    lines = log_path.read_text().strip().splitlines()
    assert lines
    logged = json.loads(lines[-1])
    assert logged["eventType"] == "prompt"


def test_playground_evaluation_latest():
    client = TestClient(app)
    resp = client.get("/playground/evaluation/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert "path" in body
    assert "data" in body
