from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_ons_observations_resource_unavailable():
    resp = client.get("/resources/read", params={"name": "ons_observations"})
    assert resp.status_code == 404
