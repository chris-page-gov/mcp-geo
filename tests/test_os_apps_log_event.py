import json

from fastapi.testclient import TestClient

from server.config import settings
from server.main import app


def test_os_apps_log_event_writes(tmp_path):
    log_path = tmp_path / "ui-events.jsonl"
    original = settings.UI_EVENT_LOG_PATH
    settings.UI_EVENT_LOG_PATH = str(log_path)
    try:
        client = TestClient(app)
        resp = client.post(
            "/tools/call",
            json={
                "tool": "os_apps.log_event",
                "eventType": "select_result",
                "source": "geography-selector",
                "payload": {"api_key": "secret", "label": "Westminster"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "logged"
        assert log_path.exists()
        record = json.loads(log_path.read_text().splitlines()[0])
        assert record["eventType"] == "select_result"
        assert record["payload"]["api_key"] == "***"
        assert record["payload"]["label"] == "Westminster"
    finally:
        settings.UI_EVENT_LOG_PATH = original
