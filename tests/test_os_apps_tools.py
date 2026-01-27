from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_os_apps_render_geography_selector():
    resp = client.post(
        "/tools/call",
        json={"tool": "os_apps.render_geography_selector", "level": "ward"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "uiResourceUris" not in body
    assert body["status"] == "ready"
    assert body["config"]["level"] == "ward"
