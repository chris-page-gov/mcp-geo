from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)


def test_os_landscape_find_bowland() -> None:
    resp = client.post(
        "/tools/call",
        json={"tool": "os_landscape.find", "text": "Forrest of Bowland"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    first = body["results"][0]
    assert first["id"] == "aonb-forest-of-bowland"


def test_os_landscape_get_by_id_with_geometry() -> None:
    resp = client.post(
        "/tools/call",
        json={"tool": "os_landscape.get", "id": "aonb-forest-of-bowland"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["landscape"]["name"] == "Forest of Bowland National Landscape"
    assert body["geometry"]["type"] == "Polygon"


def test_os_landscape_get_without_geometry() -> None:
    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_landscape.get",
            "name": "Forest of Bowland",
            "includeGeometry": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "geometry" not in body


def test_os_landscape_get_not_found() -> None:
    resp = client.post(
        "/tools/call",
        json={"tool": "os_landscape.get", "name": "Not A Real Landscape"},
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"
